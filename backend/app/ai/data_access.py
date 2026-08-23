from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import AuthorizationError, NotFoundError
from app.models import Account, Order, Ticket, User
from app.routers.orders import serialize_order
from app.routers.tickets import serialize_ticket


def get_authorized_order(db: Session, *, order_id: str, current_user: User) -> dict | None:
    order = db.scalar(select(Order).where(Order.order_id == order_id).options(selectinload(Order.events)))
    if not order:
        raise NotFoundError("Order not found", code="ORDER_NOT_FOUND")
    if str(current_user.role or "").upper() == "CUSTOMER" and order.account_id != current_user.account_id:
        raise AuthorizationError("Order not found or not accessible", code="ORDER_NOT_ACCESSIBLE")
    return serialize_order(order)


def find_authorized_order(db: Session, *, order_id: str, current_user: User) -> dict | None:
    order = db.scalar(select(Order).where(Order.order_id == order_id).options(selectinload(Order.events)))
    if not order:
        return None
    if str(current_user.role or "").upper() == "CUSTOMER" and order.account_id != current_user.account_id:
        return None
    return serialize_order(order)


def list_authorized_orders_by_carrier(db: Session, *, carrier: str, current_user: User) -> list[dict]:
    query = select(Order).where(Order.carrier.ilike(carrier)).options(selectinload(Order.events)).order_by(Order.order_id)
    if str(current_user.role or "").upper() == "CUSTOMER":
        query = query.where(Order.account_id == current_user.account_id)
    return [serialize_order(order) for order in db.scalars(query).unique().all()]


def get_authorized_ticket(db: Session, *, ticket_id: str, current_user: User) -> dict | None:
    ticket = db.scalar(select(Ticket).where(Ticket.ticket_id == ticket_id).options(selectinload(Ticket.events)))
    if not ticket:
        raise NotFoundError("Ticket not found", code="TICKET_NOT_FOUND")
    if str(current_user.role or "").upper() == "CUSTOMER" and ticket.account_id != current_user.account_id:
        raise AuthorizationError("Ticket not found or not accessible", code="TICKET_NOT_ACCESSIBLE")
    return serialize_ticket(ticket)


def get_authorized_account(db: Session, *, current_user: User) -> dict | None:
    if not current_user.account_id:
        return None
    account = db.get(Account, current_user.account_id)
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
