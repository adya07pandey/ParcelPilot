from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models import Account, AgentConversation, AgentMessage, Order, Role, ShipmentEvent, Ticket, User
from app.support.documents import agreement_record_for_account, general_policy_records
from app.support.investigation import run_support_investigation

router = APIRouter(prefix="/support", tags=["support"])

SUPPORT_USER = Depends(require_roles(Role.SUPPORT, Role.ADMIN))
ORDER_PATTERN = re.compile(r"\bORD[-\s]?(\d{3,})\b", re.IGNORECASE)

SLA_TARGETS = {
    "HIGH": timedelta(minutes=15),
    "MEDIUM": timedelta(hours=1),
    "LOW": timedelta(hours=8),
}
MIN_DATE = datetime.min.replace(tzinfo=timezone.utc)

POLICIES = [
    {
        "document_id": "support-policy-v3",
        "name": "Support Policy v3",
        "type": "General Policy",
        "status": "CURRENT",
        "effective": "1 May 2026",
        "summary": "Current support targets and escalation handling.",
    },
    {
        "document_id": "cancellation-service-credit-sop-v4",
        "name": "Cancellation & Service Credit SOP v4",
        "type": "General Policy",
        "status": "CURRENT",
        "effective": "15 June 2026",
        "summary": "Cancellation fees, service-credit eligibility, and carrier/customer fault rules.",
    },
    {
        "document_id": "product-operations-guide",
        "name": "Product Operations Guide",
        "type": "General Policy",
        "status": "CURRENT",
        "effective": "14 Aug 2026",
        "summary": "Known operational issues and product behavior notes.",
    },
    {
        "document_id": "support-policy-v2",
        "name": "Support Policy v2",
        "type": "General Policy",
        "status": "DEPRECATED",
        "effective": "1 Jan 2025 - 30 Apr 2026",
        "summary": "Previous support policy retained for historical questions.",
    },
]


class InvestigationRequest(BaseModel):
    account_id: str | None = Field(default=None, max_length=32)
    question: str = Field(min_length=3, max_length=2000)


def normalize_priority(priority: str | None) -> str:
    value = (priority or "MEDIUM").upper()
    return {"P1": "HIGH", "P2": "MEDIUM", "P3": "LOW"}.get(value, value)


def normalize_status(status: str | None) -> str:
    return (status or "open").upper()


def source_label(ticket: Ticket) -> str:
    channel = (ticket.channel or "").lower()
    if channel in {"ai_support", "ai", "assistant"} or "ai support" in (ticket.description or "").lower():
        return "AI Support"
    if channel in {"email", "chat", "internal"}:
        return channel.title()
    return "Customer Portal"


def extract_order_id(*texts: str | None) -> str | None:
    combined = " ".join(text or "" for text in texts)
    match = ORDER_PATTERN.search(combined)
    if not match:
        return None
    return f"ORD-{match.group(1)}"


def account_map(db: Session) -> dict[str, Account]:
    return {account.account_id: account for account in db.scalars(select(Account)).all()}


def serialize_account(account: Account | None) -> dict | None:
    if not account:
        return None
    return {
        "account_id": account.account_id,
        "account_name": account.account_name,
        "plan": account.plan,
        "status": account.status,
        "csm": account.csm,
        "contract_file": account.contract_file,
        "premium_support": account.premium_support,
        "notes": account.notes,
    }


def sla_info(ticket: Ticket) -> dict:
    priority = normalize_priority(ticket.priority)
    target = SLA_TARGETS.get(priority, SLA_TARGETS["MEDIUM"])
    deadline = ticket.created_at + target if ticket.created_at else None
    stored_state = (ticket.sla_state or "").upper()
    now = datetime.now(timezone.utc)
    if "BREACH" in stored_state:
        state = "BREACHED"
    elif "RISK" in stored_state:
        state = "AT_RISK"
    elif deadline and now > deadline:
        state = "BREACHED"
    elif deadline and deadline - now <= target / 3:
        state = "AT_RISK"
    else:
        state = "WITHIN_SLA"
    remaining_minutes = round((deadline - now).total_seconds() / 60) if deadline else None
    return {
        "state": state,
        "target": format_duration(target),
        "deadline": deadline,
        "remaining_minutes": remaining_minutes,
    }


def format_duration(duration: timedelta) -> str:
    minutes = round(duration.total_seconds() / 60)
    if minutes < 60:
        return f"{minutes} minutes"
    hours = minutes // 60
    return f"{hours} hour" if hours == 1 else f"{hours} hours"


def serialize_order(order: Order | None, account: Account | None = None, include_events: bool = False) -> dict | None:
    if not order:
        return None
    payload = {
        "order_id": order.order_id,
        "account_id": order.account_id,
        "account_name": account.account_name if account else None,
        "carrier": order.carrier,
        "status": order.status,
        "booked_at": order.booked_at,
        "pickup_window_start": order.pickup_window_start,
        "pickup_window_end": order.pickup_window_end,
        "pickup_actual_at": order.pickup_actual_at,
        "shipment_fee_inr": order.shipment_fee_inr,
        "origin": order.origin,
        "destination": order.destination,
        "estimated_delivery_at": order.estimated_delivery_at,
        "actual_delivery_at": order.actual_delivery_at,
        "current_location": order.current_location,
        "notes": order.notes,
    }
    if include_events:
        payload["events"] = [
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "event_time": event.event_time,
                "location": event.location,
                "description": event.description,
                "source": event.source,
            }
            for event in sorted(order.events, key=lambda item: item.event_time or MIN_DATE)
        ]
    return payload


def serialize_ticket(ticket: Ticket, account: Account | None = None, order: Order | None = None, include_events: bool = False) -> dict:
    payload = {
        "ticket_id": ticket.ticket_id,
        "account_id": ticket.account_id,
        "account_name": account.account_name if account else None,
        "created_at": ticket.created_at,
        "status": normalize_status(ticket.status),
        "subject": ticket.subject,
        "description": ticket.description,
        "channel": ticket.channel,
        "source": source_label(ticket),
        "assigned_to": ticket.assigned_to,
        "category": ticket.category,
        "subcategory": ticket.subcategory,
        "priority": normalize_priority(ticket.priority),
        "sla": sla_info(ticket),
        "linked_order_id": order.order_id if order else extract_order_id(ticket.subject, ticket.description),
        "linked_order": serialize_order(order, account) if order else None,
    }
    if include_events:
        payload["events"] = [
            {
                "ticket_event_id": event.ticket_event_id,
                "event_type": event.event_type,
                "event_time": event.event_time,
                "actor_type": event.actor_type,
                "description": event.description,
            }
            for event in sorted(ticket.events, key=lambda item: item.event_time or MIN_DATE)
        ]
    return payload


def load_linked_order(db: Session, ticket: Ticket) -> Order | None:
    order_id = extract_order_id(ticket.subject, ticket.description)
    return db.get(Order, order_id) if order_id else None


def issue_groups(tickets: list[Ticket], accounts: dict[str, Account]) -> list[dict]:
    groups: dict[str, list[Ticket]] = {}
    for ticket in tickets:
        subject = (ticket.subject or "").lower()
        category = (ticket.category or "").lower()
        if "bulk" in subject:
            key = "Bulk Upload Failures"
        elif "shipment creation" in subject or "creation" in category:
            key = "Shipment Creation Failures"
        elif "cancel" in subject or "cancellation" in category:
            key = "Cancellation Requests"
        elif "pickup" in subject:
            key = "Pickup Delays"
        else:
            key = (ticket.category or "General Support").replace("_", " ").title()
        groups.setdefault(key, []).append(ticket)

    payload = []
    for name, grouped in groups.items():
        customers = {ticket.account_id for ticket in grouped}
        high_count = sum(1 for ticket in grouped if normalize_priority(ticket.priority) == "HIGH")
        latest = max((ticket.created_at for ticket in grouped if ticket.created_at), default=None)
        severity = "Potential incident" if high_count >= 2 or len(grouped) >= 4 else "Possible recurring issue"
        payload.append(
            {
                "name": name,
                "severity": severity,
                "ticket_count": len(grouped),
                "customer_count": len(customers),
                "latest_at": latest,
                "accounts": sorted(accounts[account_id].account_name for account_id in customers if account_id in accounts),
                "ticket_ids": [ticket.ticket_id for ticket in sorted(grouped, key=lambda item: item.created_at or MIN_DATE, reverse=True)[:6]],
            }
        )
    return sorted(payload, key=lambda item: (item["severity"] != "Potential incident", -item["ticket_count"], item["name"]))


@router.get("/overview")
def overview(_: User = SUPPORT_USER, db: Session = Depends(get_db)) -> dict:
    tickets = db.scalars(select(Ticket).options(selectinload(Ticket.events))).all()
    accounts = account_map(db)
    open_tickets = [ticket for ticket in tickets if normalize_status(ticket.status) not in {"CLOSED", "RESOLVED"}]
    serialized = [serialize_ticket(ticket, accounts.get(ticket.account_id), load_linked_order(db, ticket)) for ticket in open_tickets]
    priority_queue = sorted(
        serialized,
        key=lambda item: (
            {"BREACHED": 0, "AT_RISK": 1, "WITHIN_SLA": 2}.get(item["sla"]["state"], 3),
            {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(item["priority"], 3),
            item["created_at"] or MIN_DATE,
        ),
    )
    ai_escalations = [item for item in serialized if item["source"] == "AI Support"]
    sla_states = Counter(item["sla"]["state"] for item in serialized)
    return {
        "kpis": {
            "open_tickets": len(open_tickets),
            "high_priority": sum(1 for item in serialized if item["priority"] == "HIGH"),
            "sla_at_risk": sla_states["AT_RISK"],
            "sla_breached": sla_states["BREACHED"],
            "unassigned": sum(1 for item in serialized if not item["assigned_to"]),
        },
        "priority_queue": priority_queue[:6],
        "ai_escalations": sorted(ai_escalations, key=lambda item: item["created_at"] or MIN_DATE, reverse=True)[:6],
        "issues": issue_groups(open_tickets, accounts)[:4],
    }


@router.get("/tickets")
def tickets(_: User = SUPPORT_USER, db: Session = Depends(get_db)) -> list[dict]:
    accounts = account_map(db)
    rows = db.scalars(select(Ticket).order_by(Ticket.created_at.desc().nullslast())).all()
    return [serialize_ticket(ticket, accounts.get(ticket.account_id), load_linked_order(db, ticket)) for ticket in rows]


@router.get("/tickets/{ticket_id}")
def ticket_detail(ticket_id: str, _: User = SUPPORT_USER, db: Session = Depends(get_db)) -> dict:
    ticket = db.scalar(select(Ticket).where(Ticket.ticket_id == ticket_id).options(selectinload(Ticket.events)))
    if not ticket:
        raise NotFoundError("Ticket not found", code="TICKET_NOT_FOUND")
    account = db.get(Account, ticket.account_id)
    order = load_linked_order(db, ticket)
    conversations = db.scalars(
        select(AgentConversation)
        .where(AgentConversation.account_id == ticket.account_id)
        .order_by(AgentConversation.updated_at.desc())
        .limit(3)
    ).all()
    conversation_ids = [conversation.conversation_id for conversation in conversations]
    messages = []
    if conversation_ids:
        messages = db.scalars(
            select(AgentMessage)
            .where(AgentMessage.conversation_id.in_(conversation_ids))
            .order_by(AgentMessage.created_at.asc())
            .limit(12)
        ).all()
    return {
        **serialize_ticket(ticket, account, order, include_events=True),
        "account": serialize_account(account),
        "linked_order": serialize_order(order, account, include_events=True) if order else None,
        "conversation": [
            {
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at,
            }
            for message in messages
        ],
    }


@router.get("/customers")
def customers(_: User = SUPPORT_USER, db: Session = Depends(get_db)) -> list[dict]:
    open_counts = dict(
        db.execute(
            select(Ticket.account_id, func.count(Ticket.ticket_id))
            .where(Ticket.status.notin_(["closed", "resolved", "CLOSED", "RESOLVED"]))
            .group_by(Ticket.account_id)
        ).all()
    )
    return [
        {**serialize_account(account), "open_tickets": open_counts.get(account.account_id, 0)}
        for account in db.scalars(select(Account).order_by(Account.account_name)).all()
    ]


@router.get("/customers/{account_id}")
def customer_detail(account_id: str, _: User = SUPPORT_USER, db: Session = Depends(get_db)) -> dict:
    account = db.get(Account, account_id)
    if not account:
        raise NotFoundError("Customer not found", code="ACCOUNT_NOT_FOUND")
    orders = db.scalars(select(Order).where(Order.account_id == account_id).order_by(Order.order_id)).all()
    tickets = db.scalars(select(Ticket).where(Ticket.account_id == account_id).order_by(Ticket.created_at.desc().nullslast())).all()
    return {
        "account": serialize_account(account),
        "orders": [serialize_order(order, account) for order in orders],
        "tickets": [serialize_ticket(ticket, account, load_linked_order(db, ticket)) for ticket in tickets],
        "agreement": agreement_for_account(account),
    }


@router.get("/orders")
def orders(_: User = SUPPORT_USER, db: Session = Depends(get_db)) -> list[dict]:
    accounts = account_map(db)
    return [
        serialize_order(order, accounts.get(order.account_id))
        for order in db.scalars(select(Order).order_by(Order.order_id)).all()
    ]


@router.get("/orders/{order_id}")
def order_detail(order_id: str, _: User = SUPPORT_USER, db: Session = Depends(get_db)) -> dict:
    order = db.scalar(select(Order).where(Order.order_id == order_id).options(selectinload(Order.events)))
    if not order:
        raise NotFoundError("Order not found", code="ORDER_NOT_FOUND")
    account = db.get(Account, order.account_id)
    related_tickets = db.scalars(
        select(Ticket)
        .where(Ticket.account_id == order.account_id)
        .order_by(Ticket.created_at.desc().nullslast())
    ).all()
    linked = [ticket for ticket in related_tickets if extract_order_id(ticket.subject, ticket.description) == order.order_id]
    return {
        **serialize_order(order, account, include_events=True),
        "account": serialize_account(account),
        "related_tickets": [serialize_ticket(ticket, account, order) for ticket in linked],
        "applicable_policies": applicable_policies(account),
    }


@router.get("/policies")
def policies(_: User = SUPPORT_USER, db: Session = Depends(get_db)) -> dict:
    agreements = [agreement_for_account(account) for account in db.scalars(select(Account).order_by(Account.account_name)).all()]
    return {
        "general_policies": general_policy_records(),
        "customer_agreements": agreements,
        "override_example": {
            "general_policy": "BOOKED shipments after 30 minutes may receive a INR 250 cancellation fee.",
            "customer_agreement": "Northstar can cancel BOOKED shipments before pickup with INR 0 cancellation fee.",
            "result": "Customer agreement overrides the general cancellation policy when it explicitly applies.",
        },
    }


@router.get("/issues")
def issues(_: User = SUPPORT_USER, db: Session = Depends(get_db)) -> list[dict]:
    accounts = account_map(db)
    tickets = db.scalars(select(Ticket).order_by(Ticket.created_at.desc().nullslast())).all()
    return issue_groups(tickets, accounts)


@router.post("/investigate")
def investigate(payload: InvestigationRequest, current_user: User = SUPPORT_USER, db: Session = Depends(get_db)) -> dict:
    return run_support_investigation(
        db,
        current_user=current_user,
        account_id=payload.account_id,
        question=payload.question,
    )


def agreement_for_account(account: Account) -> dict:
    return agreement_record_for_account(account)


def applicable_policies(account: Account | None) -> list[dict]:
    policies = [POLICIES[0], POLICIES[1], POLICIES[2]]
    if account:
        policies.append(agreement_for_account(account))
    return policies
