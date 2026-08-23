from __future__ import annotations

from app.models import Ticket

RULES = [
    ("CANCELLATION", "CANCEL_SHIPMENT", ["cancel my", "cancel order", "cancellation request", "cancel shipment"]),
    ("CANCELLATION", "CANCELLATION_FEE", ["fee", "cancellation fee"]),
    ("SERVICE_CREDIT", "PICKUP_DELAY_CREDIT", ["service credit", "credit", "pickup delay credit"]),
    ("SHIPMENT", "PICKUP_DELAYED", ["pickup is delayed", "pickup delayed", "pickup delay"]),
    ("SHIPMENT", "STATUS_WRONG", ["still shows booked", "status still", "status looks wrong"]),
    ("SHIPMENT", "SHIPMENT_LOCATION", ["shipment support request", "where is", "tracking", "location", "out for delivery"]),
    ("PRODUCT_HELP", "BULK_UPLOAD", ["bulk upload"]),
    ("PRODUCT_HELP", "SHIPMENT_CREATION", ["shipment creation", "creation is failing", "http 500"]),
    ("ACCOUNT_SUPPORT", "BILLING_ACCOUNT", ["billing"]),
    ("TICKETS", "CHECK_TICKET", ["ticket"]),
]

CATEGORY_ALIASES = {
    "SUPPORT": "OTHER",
    "PRODUCT": "PRODUCT_HELP",
    "BILLING": "ACCOUNT_SUPPORT",
    "CANCELLATION_REQUEST": "CANCELLATION",
}


def infer_ticket_terms(ticket: Ticket) -> tuple[str, str]:
    raw_category = (ticket.category or "").upper()
    category = CATEGORY_ALIASES.get(raw_category, raw_category or "OTHER")
    text_value = f"{ticket.subject or ''} {ticket.description or ''} {ticket.category or ''}".lower()
    for inferred_category, subcategory, needles in RULES:
        if any(needle in text_value for needle in needles):
            return inferred_category, subcategory
    return category if category else "OTHER", "OTHER"
