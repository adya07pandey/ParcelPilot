import re


def cleanLabel(value: str | None) -> str:
    return str(value or "Unknown").replace("_", " ").title()


def format_order_status_answer(order: dict) -> str:
    latest_event = max(order.get("events") or [], key=lambda event: event.get("event_time") or "", default=None)
    details = [
        f"- Status: **{cleanLabel(order.get('status'))}**",
        f"- Carrier: **{order.get('carrier') or 'Unknown'}**",
    ]
    if order.get("current_location"):
        details.append(f"- Current location: **{order['current_location']}**")
    if order.get("estimated_delivery_at"):
        details.append(f"- Estimated delivery: **{order['estimated_delivery_at']}**")
    if latest_event:
        event_label = latest_event.get("event_type") or "Latest event"
        event_time = latest_event.get("event_time") or "time unavailable"
        details.append(f"- Latest event: **{cleanLabel(event_label)}** at {event_time}")
        if latest_event.get("description"):
            details.append(f"- Event note: {latest_event['description']}")
    return (
        f"Here is the current status for **{order['order_id']}**.\n\n"
        "**Shipment details**\n"
        f"{chr(10).join(details)}"
    )


def format_order_choices(orders: list[dict]) -> str:
    return "\n".join(
        f"- **{order['order_id']}** - {order.get('carrier') or 'Unknown carrier'} - "
        f"{cleanLabel(order.get('status'))} - INR {order.get('shipment_fee_inr') or 0:g}"
        for order in orders
    )


def clean_answer(answer: str) -> str:
    return re.sub(r"^\s*(\*\*)?answer\s*:\s*(\*\*)?\s*", "", answer or "", flags=re.IGNORECASE).strip()


def append_ticket_offer(answer: str, confidence: str) -> str:
    if confidence == "HIGH":
        return clean_answer(answer)
    cleaned = clean_answer(answer)
    if "create a support ticket" in cleaned.lower() or "raise a support ticket" in cleaned.lower():
        return cleaned
    return (
        f"{cleaned}\n\n"
        "**Need more help?**\n"
        "- I can create a support ticket so the ParcelPilot team can investigate this with your account context.\n"
        "- Reply **Create ticket** if you want me to prepare one for confirmation."
    )
