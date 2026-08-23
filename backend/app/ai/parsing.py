import re

from app.models import AgentConversation

ORDER_RE = re.compile(r"\bORD[-\s]?(\d+)\b", re.IGNORECASE)
BARE_ORDER_RE = re.compile(
    r"\b(?:(?:order|shipment)\s*#?\s*(\d{4,6})|(\d{4,6})\s*(?:order|shipment))\b",
    re.IGNORECASE,
)
TICKET_RE = re.compile(r"\bTKT[-\s]?(\d+)\b", re.IGNORECASE)
CARRIERS = ("BlueDart Pro", "SwiftShip")


def extract_entities(message: str) -> dict[str, str | None]:
    order_match = ORDER_RE.search(message)
    bare_order_match = BARE_ORDER_RE.search(message)
    bare_order_id = next((group for group in (bare_order_match.groups() if bare_order_match else []) if group), None)
    ticket_match = TICKET_RE.search(message)
    carrier = next((carrier for carrier in CARRIERS if carrier.lower() in message.lower()), None)
    return {
        "order_id": f"ORD-{order_match.group(1) if order_match else bare_order_id}" if order_match or bare_order_id else None,
        "ticket_id": f"TKT-{ticket_match.group(1)}" if ticket_match else None,
        "carrier": carrier,
    }


def normalize_context_value(value: str | None) -> str | None:
    if not value:
        return None
    normalized = re.sub(r"[^A-Za-z0-9_ -]", "", value).strip().replace("-", "_").upper()
    return normalized[:128] or None


def infer_category(message: str) -> str | None:
    text = message.lower()
    if any(word in text for word in ["cancel", "cancellation", "fee"]):
        return "CANCELLATION"
    if any(word in text for word in ["credit", "late", "delay", "pickup"]):
        return "SERVICE_CREDIT"
    if "sla" in text or "support" in text:
        return "SUPPORT_SLA"
    if "ticket" in text:
        return "TICKET"
    return None


def infer_intent(message: str, *, conversation: AgentConversation, entities: dict[str, str | None]) -> str:
    text = message.lower().strip()
    if any(phrase in text for phrase in ["create ticket", "open ticket", "raise ticket", "create the ticket", "open a ticket"]):
        return "CREATE_TICKET"
    if "restart" in text:
        return "UNSUPPORTED_RESTART"
    if any(word in text for word in ["where", "status", "track", "tracking"]) and (
        entities.get("order_id") or entities.get("carrier") or "order" in text or "shipment" in text
    ):
        return "ORDER_STATUS"
    if entities.get("order_id") and conversation.category in {"SHIPMENT", "PRODUCT_HELP"}:
        return "ORDER_STATUS"
    if any(word in text for word in ["cancel", "cancellation", "fee"]):
        return "CANCELLATION"
    return "GENERAL"
