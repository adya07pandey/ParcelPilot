from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import re

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Account, Order, Ticket, User
from app.support.documents import agreement_records_for_accounts, general_policy_records

ORDER_PATTERN = re.compile(r"\b(?:ORD[-\s]?)?(\d{3,})\b", re.IGNORECASE)

GLOBAL_SOURCES = [
    {
        "id": "support-policy-v3",
        "label": "Support Policy v3",
        "type": "policy",
        "status": "CURRENT",
        "authority": 3,
        "topics": {"sla", "support", "priority", "ticket"},
    },
    {
        "id": "cancellation-service-credit-sop-v4",
        "label": "Cancellation & Service Credit SOP v4",
        "type": "sop",
        "status": "CURRENT",
        "authority": 3,
        "topics": {"cancel", "cancellation", "credit", "service", "fee"},
    },
    {
        "id": "product-operations-guide",
        "label": "Product Operations Guide",
        "type": "product_doc",
        "status": "CURRENT",
        "authority": 2,
        "topics": {"product", "bulk", "csv", "api", "shipment", "carrier", "pickup", "delivery"},
    },
]

DEPRECATED_SOURCES = [
    {
        "id": "support-policy-v2",
        "label": "Support Policy v2",
        "type": "policy",
        "status": "DEPRECATED",
        "reason": "Deprecated policy retained for historical context only.",
    }
]


def run_support_investigation(
    db: Session,
    *,
    current_user: User,
    account_id: str | None,
    question: str,
) -> dict:
    accounts = load_accounts(db, account_id)
    accounts = narrow_accounts_from_question(accounts, question)
    account_ids = [account.account_id for account in accounts]
    orders = load_relevant_orders(db, account_ids, question)
    tickets = load_relevant_tickets(db, account_ids, question)
    similar_tickets = find_similar_tickets(tickets, question)
    known_issue = match_known_issue(question, tickets)
    issue_candidates = build_issue_candidates(tickets)
    sla_risks = build_sla_risks(tickets)
    sources = build_sources(accounts, orders, tickets, question)
    confidence = calculate_confidence(accounts, orders, tickets, sources, question)

    return {
        "scope": {
            "requested_account_id": account_id or "ALL",
            "authorized_account_count": len(accounts),
            "accounts": [serialize_account(account) for account in accounts],
        },
        "answer": build_answer(
            accounts=accounts,
            orders=orders,
            tickets=tickets,
            question=question,
            confidence=confidence,
            known_issue=known_issue,
            issue_candidates=issue_candidates,
        ),
        "confidence": confidence,
        "evidence": {
            "accounts": [serialize_account(account) for account in accounts],
            "orders": [serialize_order(order) for order in orders[:8]],
            "tickets": [serialize_ticket(ticket) for ticket in tickets[:8]],
            "documents": sources,
            "excluded": DEPRECATED_SOURCES,
        },
        "similar_tickets": similar_tickets,
        "known_issue": known_issue,
        "issue_candidates": issue_candidates,
        "sla_risks": sla_risks,
        "recommendations": build_recommendations(confidence, known_issue, issue_candidates),
        "audit": {
            "investigated_by": current_user.user_id,
            "created_at": datetime.now(timezone.utc),
            "note": "Support investigation is read-only. Any company response or ticket mutation requires agent review.",
        },
    }


def load_accounts(db: Session, account_id: str | None) -> list[Account]:
    if account_id and account_id != "ALL":
        account = db.get(Account, account_id)
        return [account] if account else []
    return list(db.scalars(select(Account).order_by(Account.account_name)).all())


def narrow_accounts_from_question(accounts: list[Account], question: str) -> list[Account]:
    if len(accounts) <= 1:
        return accounts
    text = (question or "").lower()
    matched = [
        account
        for account in accounts
        if account.account_name and account.account_name.lower().split()[0] in text
    ]
    return matched or accounts


def load_relevant_orders(
    db: Session,
    account_ids: list[str],
    question: str,
) -> list[Order]:
    if not account_ids:
        return []
    order_id = extract_order_id(question)
    query = select(Order).where(Order.account_id.in_(account_ids)).options(selectinload(Order.events))
    if order_id:
        query = query.where(Order.order_id == order_id)
    elif any(word in question.lower() for word in ["order", "shipment", "carrier", "pickup", "delivery", "status", "tracking"]):
        query = query.order_by(Order.booked_at.desc().nullslast()).limit(10)
    else:
        query = query.order_by(Order.booked_at.desc().nullslast()).limit(5)
    return list(db.scalars(query).all())


def load_relevant_tickets(
    db: Session,
    account_ids: list[str],
    question: str,
) -> list[Ticket]:
    if not account_ids:
        return []
    needle = "%{}%".format(question.strip()[:80]) if question.strip() else None
    order_id = extract_order_id(question)
    query = select(Ticket).where(Ticket.account_id.in_(account_ids)).options(selectinload(Ticket.events))
    filters = []
    if order_id:
        filters.append(or_(Ticket.subject.ilike(f"%{order_id}%"), Ticket.description.ilike(f"%{order_id}%")))
    if needle and len(question.strip()) > 5:
        filters.append(or_(Ticket.subject.ilike(needle), Ticket.description.ilike(needle)))
    if filters:
        query = query.where(or_(*filters))
    return list(db.scalars(query.order_by(Ticket.created_at.desc().nullslast()).limit(12)).all())


def extract_order_id(text: str) -> str | None:
    match = ORDER_PATTERN.search(text or "")
    return f"ORD-{match.group(1)}" if match else None


def build_sources(accounts: list[Account], orders: list[Order], tickets: list[Ticket], question: str) -> list[dict]:
    selected = []
    terms = set(tokenize(question))
    policy_records = {record["document_id"]: record for record in general_policy_records()}
    for source in GLOBAL_SOURCES:
        if terms & source["topics"]:
            selected.append({**source, **policy_records.get(source["id"], {})})
    if not selected:
        selected = [{**source, **policy_records.get(source["id"], {})} for source in GLOBAL_SOURCES]
    for agreement in agreement_records_for_accounts(accounts):
        selected.append(
            {
                "id": agreement["document_id"],
                "label": agreement["name"],
                "type": "customer_agreement",
                "status": agreement["status"],
                "authority": agreement["authority"],
                "account_id": agreement["account_id"],
                "source_file": agreement["source_file"],
                "summary": agreement["summary"],
                "terms": agreement["terms"],
                "excerpt": agreement["excerpt"],
            }
        )
    if tickets:
        selected.append(
            {
                "id": "historical-tickets",
                "label": "Historical tickets",
                "type": "ticket_history",
                "status": "CONTEXT_ONLY",
                "authority": 1,
            }
        )
    if orders:
        selected.append(
            {
                "id": "structured-orders",
                "label": "Structured order records",
                "type": "structured_data",
                "status": "CURRENT",
                "authority": 5,
            }
        )
    return selected


def calculate_confidence(accounts: list[Account], orders: list[Order], tickets: list[Ticket], sources: list[dict], question: str) -> str:
    score = 0
    if accounts:
        score += 20
    if orders or tickets:
        score += 25
    if any(source["type"] in {"customer_agreement", "sop", "policy"} for source in sources):
        score += 25
    if any(source.get("status") in {"CURRENT", "ACTIVE"} for source in sources):
        score += 15
    if not extract_order_id(question) or orders:
        score += 15
    if extract_order_id(question) and not orders:
        score -= 25
    if not accounts:
        score -= 30
    if score >= 80:
        return "HIGH"
    if score >= 50:
        return "MEDIUM"
    return "LOW"


def build_answer(
    *,
    accounts: list[Account],
    orders: list[Order],
    tickets: list[Ticket],
    question: str,
    confidence: str,
    known_issue: dict | None,
    issue_candidates: list[dict],
) -> str:
    scope = "all authorized companies" if len(accounts) != 1 else accounts[0].account_name
    lines = [
        f"I investigated the request for **{scope}**.",
        "",
        "### Findings",
        f"- Structured records found: **{len(orders)} orders** and **{len(tickets)} tickets**.",
    ]
    agreement_accounts = [account for account in accounts if account.contract_file]
    if agreement_accounts:
        agreements = agreement_records_for_accounts(agreement_accounts)
        agreement_text = ", ".join(f"**{item['account_name']}** ({item['source_file']})" for item in agreements)
        lines.append(f"- Company agreement evidence available: {agreement_text}.")
        lines.extend(build_agreement_lines(agreements))
    if orders:
        order = orders[0]
        lines.append(f"- Most relevant order: **{order.order_id}** ({order.carrier}, {clean_label(order.status)}).")
    if known_issue:
        lines.append(f"- Known issue match: **{known_issue['id']} - {known_issue['title']}** ({known_issue['match']}% match).")
    if issue_candidates:
        top = issue_candidates[0]
        lines.append(f"- Recurring pattern detected: **{top['name']}** across {top['ticket_count']} tickets and {top['customer_count']} companies.")
    if "cancel" in question.lower():
        lines.extend(
            [
                "",
                "### Policy Resolution",
                "- Company agreements are checked before the generic Cancellation & Service Credit SOP.",
                "- Historical tickets are treated as context only, not policy authority.",
            ]
        )
    if confidence != "HIGH":
        lines.extend(
            [
                "",
                "### Human Review Needed",
                "- The available evidence is incomplete or not specific enough for a fully reliable conclusion.",
                "- Create or update a support ticket before taking an account-impacting action.",
            ]
        )
    lines.extend(
        [
            "",
            "### Recommendation",
            "- Review the evidence panel, then generate/edit a company response or take the appropriate support action.",
            "- Do not send or mutate anything automatically; this investigation is advisory until a support agent approves it.",
        ]
    )
    return "\n".join(lines)


def build_agreement_lines(agreements: list[dict]) -> list[str]:
    if not agreements:
        return []
    if len(agreements) > 1:
        return [
            "- Multiple company agreements are in scope; select one company for exact contract terms, or ask using the company name.",
        ]
    agreement = agreements[0]
    terms = agreement.get("terms", {})
    return [
        "",
        "### Contract Terms",
        f"- Support: {terms.get('support', 'Not available')}",
        f"- Cancellation: {terms.get('cancellation', 'Not available')}",
        f"- Service credits: {terms.get('service_credits', 'Not available')}",
        f"- Override rule: {terms.get('override', 'Not available')}",
    ]


def find_similar_tickets(tickets: list[Ticket], question: str) -> list[dict]:
    query_terms = set(tokenize(question))
    scored = []
    for ticket in tickets:
        text_terms = set(tokenize(f"{ticket.subject or ''} {ticket.description or ''}"))
        if not text_terms:
            continue
        overlap = len(query_terms & text_terms)
        score = min(98, 50 + overlap * 8) if overlap else 0
        if score >= 50:
            scored.append(
                {
                    "ticket_id": ticket.ticket_id,
                    "subject": ticket.subject,
                    "account_id": ticket.account_id,
                    "match": score,
                }
            )
    return sorted(scored, key=lambda item: item["match"], reverse=True)[:5]


def match_known_issue(question: str, tickets: list[Ticket]) -> dict | None:
    text = " ".join([question, *[ticket.subject or "" for ticket in tickets], *[ticket.description or "" for ticket in tickets]]).lower()
    if "bulk" in text or "csv" in text:
        return {
            "id": "KI-208",
            "title": "Bulk Upload Failures",
            "match": 96,
            "status": "Investigating",
            "workaround": "Split uploads below 3,000 rows. Individual shipment creation is unaffected.",
        }
    if "swiftship" in text and ("booked" in text or "pickup" in text):
        return {
            "id": "KI-211",
            "title": "SwiftShip pickup webhook delay",
            "match": 91,
            "status": "Known behavior",
            "workaround": "Allow up to 20 minutes for carrier pickup confirmations to reach ParcelPilot.",
        }
    if "500" in text or "creation" in text or "create shipment" in text:
        return {
            "id": "KI-214",
            "title": "Shipment creation failures",
            "match": 88,
            "status": "Needs triage",
            "workaround": "Check affected accounts and escalation priority before advising companies.",
        }
    return None


def build_issue_candidates(tickets: list[Ticket]) -> list[dict]:
    groups: dict[str, list[Ticket]] = {}
    for ticket in tickets:
        key = infer_issue_key(ticket)
        groups.setdefault(key, []).append(ticket)
    candidates = []
    for name, grouped in groups.items():
        accounts = {ticket.account_id for ticket in grouped}
        if len(grouped) < 2:
            continue
        candidates.append(
            {
                "name": name,
                "ticket_count": len(grouped),
                "customer_count": len(accounts),
                "severity": "Potential platform incident" if len(accounts) > 1 else "Recurring account issue",
                "ticket_ids": [ticket.ticket_id for ticket in grouped[:5]],
            }
        )
    return sorted(candidates, key=lambda item: (-item["customer_count"], -item["ticket_count"], item["name"]))[:5]


def build_sla_risks(tickets: list[Ticket]) -> list[dict]:
    risky = []
    for ticket in tickets:
        state = str(ticket.sla_state or "").upper()
        priority = normalize_priority(ticket.priority)
        if "BREACH" in state or priority == "HIGH":
            risky.append(
                {
                    "ticket_id": ticket.ticket_id,
                    "priority": priority,
                    "state": "BREACHED" if "BREACH" in state else "AT_RISK",
                    "subject": ticket.subject,
                }
            )
    return risky[:6]


def build_recommendations(confidence: str, known_issue: dict | None, issue_candidates: list[dict]) -> list[str]:
    recommendations = ["Review evidence before taking action.", "Generate a draft response only after checking the cited records."]
    if known_issue:
        recommendations.append(f"Use the known issue workaround for {known_issue['id']} if it matches the company impact.")
    if issue_candidates:
        recommendations.append("Consider escalating as a recurring issue or incident candidate.")
    if confidence != "HIGH":
        recommendations.append("Create or update a support ticket instead of making a final claim.")
    return recommendations


def infer_issue_key(ticket: Ticket) -> str:
    text = f"{ticket.subject or ''} {ticket.description or ''} {ticket.category or ''}".lower()
    if "bulk" in text or "csv" in text:
        return "Bulk Upload Failures"
    if "creation" in text or "500" in text:
        return "Shipment Creation Failures"
    if "pickup" in text:
        return "Pickup Delay / Pickup Status"
    if "cancel" in text:
        return "Cancellation Requests"
    return (ticket.category or "General Support").replace("_", " ").title()


def serialize_account(account: Account) -> dict:
    return {
        "account_id": account.account_id,
        "account_name": account.account_name,
        "plan": account.plan,
        "csm": account.csm,
        "premium_support": account.premium_support,
    }


def serialize_order(order: Order) -> dict:
    return {
        "order_id": order.order_id,
        "account_id": order.account_id,
        "carrier": order.carrier,
        "status": order.status,
        "origin": order.origin,
        "destination": order.destination,
        "current_location": order.current_location,
    }


def serialize_ticket(ticket: Ticket) -> dict:
    return {
        "ticket_id": ticket.ticket_id,
        "account_id": ticket.account_id,
        "subject": ticket.subject,
        "category": ticket.category,
        "subcategory": ticket.subcategory,
        "priority": normalize_priority(ticket.priority),
        "status": ticket.status,
    }


def normalize_priority(priority: str | None) -> str:
    value = (priority or "MEDIUM").upper()
    return {"P1": "HIGH", "P2": "MEDIUM", "P3": "LOW"}.get(value, value)


def clean_label(value: str | None) -> str:
    return str(value or "Unknown").replace("_", " ").title()


def tokenize(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]{3,}", (text or "").lower()) if token not in {"the", "and", "for", "with"}]
