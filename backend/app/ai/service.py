import secrets
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.ai.conversations import append_message, get_current_conversation_state, get_or_create_conversation, reset_current_conversation
from app.ai.data_access import (
    find_authorized_order,
    get_authorized_account,
    get_authorized_order,
    get_authorized_ticket,
    list_authorized_orders_by_carrier,
)
from app.ai.evidence import calculate_confidence, filter_applicable_document_chunks, summarize_sources
from app.ai.parsing import extract_entities, infer_category, infer_intent, normalize_context_value
from app.ai.providers import GroqChat, fetch_authorized_account_agreement, search_authorized_documents
from app.ai.response_formatting import append_ticket_offer, clean_answer, cleanLabel, format_order_choices, format_order_status_answer
from app.core.config import get_settings
from app.core.exceptions import AuthorizationError, ExternalServiceError, ValidationError
from app.models import AgentConversation, Order, Ticket, TicketEvent, User
from app.routers.orders import serialize_order
from app.routers.tickets import serialize_ticket

SUPPORT_SLA_BY_ACCOUNT = {
    "ACCT-001": {"HIGH": "1 hour", "MEDIUM": "8 business hours", "LOW": "2 business days"},
    "ACCT-002": {"HIGH": "4 business hours", "MEDIUM": "2 business days", "LOW": "3 business days"},
}
async def run_customer_agent(
    db: Session,
    *,
    current_user: User,
    message: str,
    conversation_id: str | None = None,
    category: str | None = None,
    subcategory: str | None = None,
    order_id: str | None = None,
    ticket_id: str | None = None,
) -> dict:
    entities = extract_entities(message)
    conversation = get_or_create_conversation(
        db,
        current_user=current_user,
        conversation_id=conversation_id,
        category=category,
        subcategory=subcategory,
        order_id=order_id or entities["order_id"],
        ticket_id=ticket_id or entities["ticket_id"],
    )
    conversation.category = infer_category(message) or normalize_context_value(category) or conversation.category
    conversation.subcategory = normalize_context_value(subcategory) or conversation.subcategory
    if entities["order_id"]:
        conversation.order_id = entities["order_id"]
    if entities["ticket_id"]:
        conversation.ticket_id = entities["ticket_id"]
    intent = infer_intent(message, conversation=conversation, entities=entities)
    if entities.get("carrier") and not entities.get("order_id") and intent in {"ORDER_STATUS", "UNSUPPORTED_RESTART"}:
        conversation.order_id = None

    append_message(db, conversation_id=conversation.conversation_id, role="user", content=message)

    evidence: list[dict] = []
    evidence.append(
        {
            "type": "conversation_context",
            "data": {
                "category": conversation.category,
                "subcategory": conversation.subcategory,
                "note": "Category and subcategory are routing hints from the guided UI, not hard retrieval boundaries.",
            },
        }
    )
    account_data = get_authorized_account(db, current_user=current_user)
    if account_data:
        evidence.append({"type": "account", "data": account_data})
    if conversation.order_id:
        order_data = find_authorized_order(db, order_id=conversation.order_id, current_user=current_user)
        if not order_data:
            return persist_agent_response(
                db,
                conversation=conversation,
                answer=append_ticket_offer(
                    (
                        f"I couldn't find **{conversation.order_id}** in your shipment records.\n\n"
                        "**Next steps**\n"
                        "- Please check the order ID and try again.\n"
                        "- Share any alternate shipment reference, carrier, or booking date you have."
                    ),
                    "LOW",
                ),
                confidence="LOW",
                confidence_score=20,
                evidence=evidence,
                provider_ready=False,
            )
        evidence.append({"type": "order", "data": order_data})
    if conversation.ticket_id:
        evidence.append({"type": "ticket", "data": get_authorized_ticket(db, ticket_id=conversation.ticket_id, current_user=current_user)})

    if intent == "CREATE_TICKET":
        draft = build_ticket_draft(
            conversation=conversation,
            current_user=current_user,
            account_data=account_data,
            evidence=evidence,
            message=message,
        )
        conversation.pending_action = {"type": "CREATE_TICKET", "status": "AWAITING_CONFIRMATION", "draft": draft}
        return persist_agent_response(
            db,
            conversation=conversation,
            answer=(
                "I prepared a support ticket draft using the context I already have. "
                "Review it below and click **Create Ticket** when you want me to submit it."
            ),
            confidence="MEDIUM",
            confidence_score=70,
            evidence=evidence,
            provider_ready=False,
            ticket_preview=draft,
        )

    direct_response = build_structured_response(
        db,
        intent=intent,
        message=message,
        entities=entities,
        conversation=conversation,
        current_user=current_user,
        account_data=account_data,
        evidence=evidence,
    )
    if direct_response:
        return persist_agent_response(db, conversation=conversation, evidence=evidence, **direct_response)

    settings = get_settings()
    provider_ready = bool(settings.voyage_api_key and settings.qdrant_url and settings.groq_api_key)
    document_chunks = []
    if provider_ready:
        try:
            document_chunks = await search_authorized_documents(
                query=message,
                account_id=current_user.account_id,
                effective_at=settings.dataset_snapshot_time,
                limit=8,
            )
            if is_account_policy_question(message):
                document_chunks = merge_document_chunks(
                    document_chunks,
                    await fetch_authorized_account_agreement(account_id=current_user.account_id),
                )
            document_chunks = filter_applicable_document_chunks(
                document_chunks,
                message=message,
                effective_at=settings.dataset_snapshot_time,
            )
            evidence.extend(
                {
                    "type": "document",
                    "chunk_id": chunk.chunk_id,
                    "score": chunk.score,
                    "text": chunk.text,
                    "metadata": chunk.metadata,
                }
                for chunk in document_chunks
            )
            answer = await generate_answer(
                message=message,
                evidence=evidence,
                has_document_evidence=bool(document_chunks),
            )
            confidence_score, confidence = calculate_confidence(
                evidence=evidence,
                document_chunks=document_chunks,
                conversation=conversation,
            )
            answer = append_ticket_offer(answer, confidence)
        except ExternalServiceError as exc:
            answer = (
                "I saved your question and account context, but the AI retrieval service is unavailable right now. "
                f"Provider error: {exc.code}. Please try again after the provider connection or rate limit recovers."
            )
            confidence_score = 20
            confidence = "LOW"
            answer = append_ticket_offer(answer, confidence)
    else:
        answer = (
            "AI Support is wired to use Voyage, Qdrant, and Groq, but the provider keys are not configured yet. "
            "I saved this conversation context and can answer with retrieved policy evidence once those keys and documents are loaded."
        )
        confidence_score = 25
        confidence = "LOW"
        answer = append_ticket_offer(answer, confidence)

    return persist_agent_response(
        db,
        conversation=conversation,
        answer=answer,
        confidence=confidence,
        confidence_score=confidence_score,
        evidence=evidence,
        provider_ready=provider_ready,
    )


def is_account_policy_question(message: str) -> bool:
    text = message.lower()
    return any(
        phrase in text
        for phrase in [
            "policy",
            "policies",
            "contract",
            "agreement",
            "terms",
            "sla",
            "plan",
            "northstar",
            "lumenworks",
        ]
    )


def merge_document_chunks(primary, extra):
    merged = []
    seen = set()
    for chunk in [*primary, *extra]:
        if chunk.chunk_id in seen:
            continue
        seen.add(chunk.chunk_id)
        merged.append(chunk)
    return merged


def persist_agent_response(
    db: Session,
    *,
    conversation: AgentConversation,
    answer: str,
    confidence: str,
    confidence_score: int,
    evidence: list[dict],
    provider_ready: bool,
    ticket_preview: dict | None = None,
    action_preview: dict | None = None,
) -> dict:
    conversation.last_confidence = confidence
    append_message(
        db,
        conversation_id=conversation.conversation_id,
        role="assistant",
        content=answer,
        metadata={
            "confidence": confidence,
            "category": conversation.category,
            "subcategory": conversation.subcategory,
            "order_id": conversation.order_id,
            "ticket_id": conversation.ticket_id,
            "evidence_count": len(evidence),
            "confidence_score": confidence_score,
        },
    )
    db.commit()

    return {
        "conversation_id": conversation.conversation_id,
        "answer": answer,
        "confidence": confidence,
        "confidence_score": confidence_score,
        "active_context": {
            "category": conversation.category,
            "subcategory": conversation.subcategory,
            "order_id": conversation.order_id,
            "ticket_id": conversation.ticket_id,
            "account_id": conversation.account_id,
        },
        "sources": summarize_sources(evidence),
        "provider_ready": provider_ready,
        "ticket_preview": ticket_preview,
        "action_preview": action_preview,
    }


def build_ticket_draft(
    *,
    conversation: AgentConversation,
    current_user: User,
    account_data: dict | None,
    evidence: list[dict],
    message: str,
) -> dict:
    order = next((item["data"] for item in evidence if item["type"] == "order"), None)
    existing_ticket = next((item["data"] for item in evidence if item["type"] == "ticket"), None)
    priority, priority_reason = determine_ticket_priority(message=message, order=order, conversation=conversation)
    response_target = determine_response_target(account_id=current_user.account_id, priority=priority)
    subject = build_ticket_subject(conversation=conversation, order=order, existing_ticket=existing_ticket, message=message)
    description = build_ticket_description(
        account_data=account_data,
        order=order,
        existing_ticket=existing_ticket,
        message=message,
        priority=priority,
        priority_reason=priority_reason,
    )
    return {
        "subject": subject,
        "description": description,
        "account_id": current_user.account_id,
        "account_name": account_data.get("account_name") if account_data else None,
        "order_id": order.get("order_id") if order else conversation.order_id,
        "carrier": order.get("carrier") if order else None,
        "shipment_status": order.get("status") if order else None,
        "existing_ticket_id": existing_ticket.get("ticket_id") if existing_ticket else conversation.ticket_id,
        "priority": priority,
        "priority_reason": priority_reason,
        "response_target": response_target,
        "escalation_reason": build_escalation_reason(message=message, order=order, priority_reason=priority_reason),
        "category": conversation.category or "SUPPORT",
        "subcategory": conversation.subcategory or "OTHER",
    }


def build_cancellation_request_draft(*, order: dict, account_data: dict | None, conversation: AgentConversation) -> dict:
    priority = "MEDIUM"
    priority_reason = "Customer-requested cancellation for an eligible BOOKED shipment"
    response_target = determine_response_target(account_id=order.get("account_id"), priority=priority)
    account_name = account_data.get("account_name") if account_data else order.get("account_id")
    _ = account_name
    description = "Customer requested cancellation through AI Support. The shipment was eligible for no-fee cancellation when checked."
    return {
        "subject": f"Cancellation request - {order['order_id']}",
        "description": description,
        "account_id": order.get("account_id"),
        "account_name": account_name,
        "order_id": order["order_id"],
        "carrier": order.get("carrier"),
        "shipment_status": order.get("status"),
        "existing_ticket_id": None,
        "priority": priority,
        "priority_reason": priority_reason,
        "response_target": response_target,
        "escalation_reason": f"Customer confirmed a cancellation request for eligible BOOKED shipment {order['order_id']}.",
        "category": "CANCELLATION_REQUEST",
        "subcategory": conversation.subcategory or "CANCEL_SHIPMENT",
        "intent": "CANCELLATION_REQUEST",
    }


def determine_ticket_priority(*, message: str, order: dict | None, conversation: AgentConversation) -> tuple[str, str]:
    text = f"{message} {conversation.category or ''} {conversation.subcategory or ''}".lower()
    if any(term in text for term in ["api key", "credential", "security incident", "data leak", "breach"]):
        return "HIGH", "Suspected credential exposure or security incident"
    if any(term in text for term in ["all users", "every user", "complete outage", "cannot create any shipment", "shipment creation outage"]):
        return "HIGH", "Complete production outage affecting shipment creation"
    if any(term in text for term in ["bulk upload", "major", "degraded", "return", "return-to-origin", "out for delivery"]):
        return "HIGH", "Major operational issue or return workflow requiring support action"
    if order and str(order.get("status") or "").upper() in {"OUT_FOR_DELIVERY", "PICKED_UP", "IN_TRANSIT"}:
        return "HIGH", "Shipment is already in carrier flow and needs operations follow-up"
    if any(term in text for term in ["how do i", "how-to", "billing contact", "configuration"]):
        return "LOW", "How-to or configuration request"
    return "MEDIUM", "Normal support request or limited operational impact"


def determine_response_target(*, account_id: str | None, priority: str) -> str:
    return SUPPORT_SLA_BY_ACCOUNT.get(account_id or "", {}).get(priority, {"HIGH": "4 business hours", "MEDIUM": "2 business days", "LOW": "3 business days"}[priority])


def build_ticket_subject(*, conversation: AgentConversation, order: dict | None, existing_ticket: dict | None, message: str) -> str:
    if existing_ticket:
        return f"Follow-up on {existing_ticket['ticket_id']}"
    if order and any(term in message.lower() for term in ["return", "return-to-origin", "cancel"]):
        return f"Return-to-origin investigation for {order['order_id']}"
    if order:
        return f"Shipment support request for {order['order_id']}"
    if conversation.category:
        return f"{cleanLabel(conversation.category)} support request"
    return "ParcelPilot support request"


def build_ticket_description(
    *,
    account_data: dict | None,
    order: dict | None,
    existing_ticket: dict | None,
    message: str,
    priority: str,
    priority_reason: str,
) -> str:
    _ = account_data, existing_ticket, priority, priority_reason
    if order:
        return f"Customer requested support from AI Support: {message}"
    return f"Customer requested support from AI Support: {message}"


def build_escalation_reason(*, message: str, order: dict | None, priority_reason: str) -> str:
    if order:
        return f"{priority_reason}. The request is tied to {order.get('order_id')} with status {cleanLabel(order.get('status'))}."
    return f"{priority_reason}. Customer asked: {message}"


def create_ticket_from_pending_action(
    db: Session,
    *,
    current_user: User,
    conversation_id: str,
    subject: str | None = None,
    description: str | None = None,
) -> dict:
    conversation = db.get(AgentConversation, conversation_id)
    if not conversation or conversation.user_id != current_user.user_id:
        raise AuthorizationError("Conversation not accessible", code="CONVERSATION_NOT_ACCESSIBLE")
    pending_action = conversation.pending_action or {}
    if pending_action.get("type") != "CREATE_TICKET" or pending_action.get("status") != "AWAITING_CONFIRMATION":
        raise ValidationError("No ticket draft is awaiting confirmation", code="NO_TICKET_DRAFT")
    draft = dict(pending_action.get("draft") or {})
    draft["subject"] = (subject or draft.get("subject") or "ParcelPilot support request").strip()
    draft["description"] = (description or draft.get("description") or "Support requested from AI Support").strip()
    if draft.get("order_id"):
        order = find_authorized_order(db, order_id=draft["order_id"], current_user=current_user)
        if not order:
            raise AuthorizationError("Order not found or not accessible", code="ORDER_NOT_ACCESSIBLE")

    now = datetime.now(timezone.utc)
    ticket = Ticket(
        ticket_id=f"TKT-{secrets.randbelow(900000) + 100000}",
        account_id=current_user.account_id,
        created_at=now,
        status="open",
        subject=draft["subject"],
        description=draft["description"],
        channel="ai_support",
        assigned_to=None,
        last_customer_message_at=now,
        historical_resolution=None,
        category=str(draft.get("category") or "SUPPORT").upper(),
        subcategory=str(draft.get("subcategory") or "OTHER").upper(),
        priority=draft.get("priority") or "MEDIUM",
        sla_state="WITHIN_SLA",
    )
    event = TicketEvent(
        ticket_event_id=f"TEV-{secrets.randbelow(900000) + 100000}",
        ticket_id=ticket.ticket_id,
        account_id=ticket.account_id,
        event_type="CREATED",
        event_time=now,
        actor_type="CUSTOMER" if current_user.role == "CUSTOMER" else "SUPPORT",
        description=draft["description"],
    )
    conversation.pending_action = None
    conversation.ticket_id = ticket.ticket_id
    append_message(
        db,
        conversation_id=conversation.conversation_id,
        role="assistant",
        content=f"Ticket **{ticket.ticket_id}** has been created.",
        metadata={"created_ticket_id": ticket.ticket_id, "priority": ticket.priority},
    )
    db.add_all([ticket, event])
    db.commit()
    db.refresh(ticket)
    ticket.events = [event]
    return {
        "ticket": serialize_ticket(ticket),
        "message": f"Ticket {ticket.ticket_id} has been created.",
    }


def confirm_cancellation_action(
    db: Session,
    *,
    current_user: User,
    conversation_id: str,
) -> dict:
    conversation = db.get(AgentConversation, conversation_id)
    if not conversation or conversation.user_id != current_user.user_id:
        raise AuthorizationError("Conversation not accessible", code="CONVERSATION_NOT_ACCESSIBLE")
    pending_action = conversation.pending_action or {}
    if pending_action.get("type") != "CANCELLATION_REQUEST" or pending_action.get("status") != "AWAITING_CONFIRMATION":
        raise ValidationError("No cancellation request is awaiting confirmation", code="NO_CANCELLATION_REQUEST")

    order_id = pending_action.get("order_id")
    order = db.scalar(select(Order).where(Order.order_id == order_id).options(selectinload(Order.events)))
    if not order or (current_user.role == "CUSTOMER" and order.account_id != current_user.account_id):
        raise AuthorizationError("Order not found or not accessible", code="ORDER_NOT_ACCESSIBLE")
    if str(order.status or "").upper() != "BOOKED" or order.pickup_actual_at:
        conversation.pending_action = None
        db.commit()
        raise ValidationError("Order status changed and a cancellation request is no longer eligible", code="ORDER_NOT_CANCELLABLE")

    now = datetime.now(timezone.utc)
    draft = dict(pending_action.get("draft") or {})
    draft.setdefault("subject", f"Cancellation request - {order.order_id}")
    draft.setdefault(
        "description",
        f"Customer confirmed cancellation request for {order.order_id}. Current status: {cleanLabel(order.status)}.",
    )
    ticket = Ticket(
        ticket_id=f"TKT-{secrets.randbelow(900000) + 100000}",
        account_id=current_user.account_id,
        created_at=now,
        status="open",
        subject=draft["subject"],
        description=draft["description"],
        channel="ai_support",
        assigned_to=None,
        last_customer_message_at=now,
        historical_resolution=None,
        category="CANCELLATION_REQUEST",
        subcategory=str(draft.get("subcategory") or "CANCEL_SHIPMENT").upper(),
        priority=draft.get("priority") or "MEDIUM",
        sla_state="WITHIN_SLA",
    )
    event = TicketEvent(
        ticket_event_id=f"TEV-{secrets.randbelow(900000) + 100000}",
        ticket_id=ticket.ticket_id,
        account_id=ticket.account_id,
        event_type="CREATED",
        event_time=now,
        actor_type="CUSTOMER" if current_user.role == "CUSTOMER" else "SUPPORT",
        description=draft["description"],
    )
    conversation.pending_action = None
    conversation.ticket_id = ticket.ticket_id
    append_message(
        db,
        conversation_id=conversation.conversation_id,
        role="assistant",
        content=f"Cancellation request ticket **{ticket.ticket_id}** has been created for **{order.order_id}**.",
        metadata={"created_ticket_id": ticket.ticket_id, "order_id": order.order_id, "intent": "CANCELLATION_REQUEST"},
    )
    db.add_all([ticket, event])
    db.commit()
    db.refresh(ticket)
    ticket.events = [event]
    return {
        "ticket": serialize_ticket(ticket),
        "order": serialize_order(order),
        "message": f"Cancellation request ticket {ticket.ticket_id} has been created for {order.order_id}.",
    }


def build_structured_response(
    db: Session,
    *,
    intent: str,
    message: str,
    entities: dict[str, str | None],
    conversation: AgentConversation,
    current_user: User,
    account_data: dict | None,
    evidence: list[dict],
) -> dict | None:
    _ = message
    order_items = [item["data"] for item in evidence if item["type"] == "order"]
    if intent == "CANCELLATION" and order_items:
        order = order_items[-1]
        return build_cancellation_response(order=order, account_data=account_data, conversation=conversation)

    if intent == "ORDER_STATUS" and order_items:
        order = order_items[-1]
        return {
            "answer": format_order_status_answer(order),
            "confidence": "HIGH",
            "confidence_score": 90,
            "provider_ready": False,
        }

    if intent == "ORDER_STATUS" and entities.get("carrier"):
        orders = list_authorized_orders_by_carrier(db, carrier=entities["carrier"], current_user=current_user)
        evidence.append({"type": "order_list", "carrier": entities["carrier"], "data": orders})
        if not orders:
            return {
                "answer": append_ticket_offer(
                    (
                        f"I couldn't find any **{entities['carrier']}** shipments in your account records.\n\n"
                        "**Next steps**\n"
                        "- Check whether the carrier name or order reference is different.\n"
                        "- Share an order ID if you have one."
                    ),
                    "LOW",
                ),
                "confidence": "LOW",
                "confidence_score": 25,
                "provider_ready": False,
            }
        if len(orders) == 1:
            conversation.order_id = orders[0]["order_id"]
            evidence.append({"type": "order", "data": orders[0]})
            return {
                "answer": format_order_status_answer(orders[0]),
                "confidence": "HIGH",
                "confidence_score": 90,
                "provider_ready": False,
            }
        return {
            "answer": (
                f"I found **{len(orders)} {entities['carrier']} shipments** in your account.\n\n"
                "**Which shipment do you mean?**\n"
                f"{format_order_choices(orders)}"
            ),
            "confidence": "MEDIUM",
            "confidence_score": 65,
            "provider_ready": False,
        }

    if intent == "UNSUPPORTED_RESTART":
        carrier = entities.get("carrier")
        orders = list_authorized_orders_by_carrier(db, carrier=carrier, current_user=current_user) if carrier else []
        if carrier:
            evidence.append({"type": "order_list", "carrier": carrier, "data": orders})
        order_text = ""
        if orders:
            order_text = f"\n\n**I found these {carrier} shipments for your account:**\n{format_order_choices(orders)}"
        elif carrier:
            order_text = f"\n\nI couldn't find any **{carrier}** shipments in your account records."
        return {
            "answer": append_ticket_offer(
                (
                    "ParcelPilot does not have a documented **restart shipment** action in the available product information.\n\n"
                    "**What I can do**\n"
                    "- Check the current shipment status from your account records.\n"
                    "- If you want to cancel a shipment, I can check whether cancellation is allowed and prepare a confirmation step.\n"
                    "- I won't assume that cancel + create a new shipment is an official restart workflow unless the product docs or tools support it."
                    f"{order_text}"
                ),
                "MEDIUM",
            ),
            "confidence": "MEDIUM",
            "confidence_score": 60,
            "provider_ready": False,
        }

    return None


def build_cancellation_response(*, order: dict, account_data: dict | None, conversation: AgentConversation) -> dict:
    status = str(order.get("status") or "").upper()
    picked_up = bool(order.get("pickup_actual_at")) or status in {"PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED"}
    carrier = order.get("carrier") or "Unknown carrier"
    account_name = account_data.get("account_name") if account_data else "your account"

    if status == "CANCELLED":
        answer = (
            f"**{order['order_id']} is already cancelled.**\n\n"
            "**Checked from order data**\n"
            f"- Carrier: **{carrier}**\n"
            f"- Current status: **{cleanLabel(status)}**"
        )
        return {"answer": answer, "confidence": "HIGH", "confidence_score": 95, "provider_ready": False}

    if not picked_up and status == "BOOKED":
        draft = build_cancellation_request_draft(order=order, account_data=account_data, conversation=conversation)
        conversation.pending_action = {
            "type": "CANCELLATION_REQUEST",
            "status": "AWAITING_CONFIRMATION",
            "order_id": order["order_id"],
            "fee_inr": 0,
            "draft": draft,
        }
        requested = (
            f"\n- Existing cancellation request timestamp: **{order['cancellation_requested_at']}**"
            if order.get("cancellation_requested_at")
            else ""
        )
        answer = (
            f"**{order['order_id']} can be cancelled.**\n\n"
            "**Checked from order data**\n"
            f"- Carrier: **{carrier}**\n"
            f"- Current status: **{cleanLabel(status)}**\n"
            "- Pickup status: **Not picked up**\n"
            "- Cancellation fee: **INR 0**"
            f"{requested}\n\n"
            "**Why**\n"
            f"- {account_name} has a cancellation override for BOOKED shipments before pickup.\n"
            "- The order is still BOOKED, so the no-fee cancellation path applies.\n\n"
            "**Next step**\n"
            "- I have prepared a cancellation request for the ParcelPilot support team. It still needs your explicit confirmation before a ticket is created."
        )
        return {
            "answer": answer,
            "confidence": "HIGH",
            "confidence_score": 95,
            "provider_ready": False,
            "action_preview": {
                "type": "CANCELLATION_REQUEST",
                "title": "Cancellation Request",
                "order_id": order["order_id"],
                "carrier": carrier,
                "status": status,
                "fee_inr": 0,
                "warning": "This will create a support ticket for the ParcelPilot team to process the cancellation request.",
                "confirm_label": "Create Cancellation Request",
            },
        }

    answer = (
        f"**{order['order_id']} cannot be cancelled now.**\n\n"
        "**Checked from order data**\n"
        f"- Carrier: **{carrier}**\n"
        f"- Current status: **{cleanLabel(status)}**\n"
        f"- Pickup actual time: **{order.get('pickup_actual_at') or 'Not available'}**\n\n"
        "**Why**\n"
        "- Once a shipment has been picked up or is already in carrier flow, the cancellation path is no longer available.\n"
        "- The supported next step is a return-to-origin/support workflow, not direct cancellation."
    )
    return {
        "answer": append_ticket_offer(answer, "MEDIUM"),
        "confidence": "MEDIUM",
        "confidence_score": 70,
        "provider_ready": False,
    }


async def generate_answer(*, message: str, evidence: list[dict], has_document_evidence: bool) -> str:
    system = (
        "You are ParcelPilot AI Support. Answer only from the supplied evidence. "
        "You may use account, order, ticket, and event records as operational truth for the authenticated customer. "
        "Customer agreements override general policy only when they explicitly cover the same issue. "
        "If evidence includes a customer_agreement document for the authenticated account, treat it as that customer's "
        "account-specific policy/contract evidence; do not say the system lacks that customer's policy documents. "
        "Use conversation category/subcategory as an initial routing hint, but answer the customer's actual "
        "natural-language question even when it crosses multiple support areas. "
        "Mention uncertainty and recommend support escalation when evidence is incomplete. "
        "Format answers for a customer support chat. Start with a direct answer, then use short Markdown bullets "
        "or numbered steps. Do not prefix the answer with 'Answer:'. "
        "Do not use Markdown tables, pipe-table syntax, raw HTML, or <br> tags. "
        "Keep contract and policy answers easy to scan with section labels such as Summary, What Applies, and Next Steps. "
        "For state-changing requests such as cancelling an order or creating a ticket, never claim that the action "
        "has been completed or will be completed immediately. Ask for missing information, describe the pending action, "
        "and say the customer must explicitly confirm before the backend executes it. "
        "If there is account metadata but no document evidence, summarize the visible account/contract metadata, "
        "state that the contract/policy PDFs have not been indexed into the document store yet, "
        "and do not invent exact contract clauses or policy terms."
    )
    content = (
        f"User question:\n{message}\n\n"
        f"Document evidence available: {has_document_evidence}\n\n"
        f"Evidence:\n{evidence}"
    )
    return await GroqChat().complete(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ]
    )
