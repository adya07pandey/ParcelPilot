from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import can_access_account, get_current_user
from app.core.database import get_db
from app.core.exceptions import AuthorizationError, NotFoundError
from app.models import Order, ShipmentEvent, User

router = APIRouter(prefix="/orders", tags=["orders"])


def serialize_order(order: Order) -> dict:
    return {
        "order_id": order.order_id,
        "account_id": order.account_id,
        "carrier": order.carrier,
        "status": order.status,
        "booked_at": order.booked_at,
        "pickup_window_start": order.pickup_window_start,
        "pickup_window_end": order.pickup_window_end,
        "pickup_actual_at": order.pickup_actual_at,
        "shipment_fee_inr": order.shipment_fee_inr,
        "carrier_fault": order.carrier_fault,
        "customer_fault": order.customer_fault,
        "cancellation_requested_at": order.cancellation_requested_at,
        "notes": order.notes,
        "origin": order.origin,
        "destination": order.destination,
        "estimated_delivery_at": order.estimated_delivery_at,
        "actual_delivery_at": order.actual_delivery_at,
        "current_location": order.current_location,
        "pickup_delay_minutes": order.pickup_delay_minutes,
        "delivery_delay_minutes": order.delivery_delay_minutes,
        "events": [
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "event_time": event.event_time,
                "description": event.description,
                "source": event.source,
            }
            for event in sorted(order.events, key=lambda e: e.event_time or "")
        ],
    }


@router.get("")
def list_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = select(Order).order_by(Order.order_id)
    if current_user.role == "CUSTOMER":
        query = query.where(Order.account_id == current_user.account_id)
    return [serialize_order(order) for order in db.scalars(query).all()]


@router.get("/{order_id}")
def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    order = db.scalar(select(Order).where(Order.order_id == order_id).options(selectinload(Order.events)))
    if not order:
        raise NotFoundError("Order not found", code="ORDER_NOT_FOUND")
    if not can_access_account(current_user, order.account_id):
        raise AuthorizationError("Order not found or not accessible", code="ORDER_NOT_ACCESSIBLE")
    return serialize_order(order)


@router.get("/{order_id}/events")
def get_order_events(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    order = db.get(Order, order_id)
    if not order:
        raise NotFoundError("Order not found", code="ORDER_NOT_FOUND")
    if not can_access_account(current_user, order.account_id):
        raise AuthorizationError("Order not found or not accessible", code="ORDER_NOT_ACCESSIBLE")

    events = db.scalars(
        select(ShipmentEvent)
        .where(ShipmentEvent.order_id == order_id)
        .order_by(ShipmentEvent.event_time.asc().nullslast())
    ).all()
    return [
        {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "event_time": event.event_time,
            "carrier": event.carrier,
            "location": event.location,
            "description": event.description,
            "source": event.source,
        }
        for event in events
    ]
