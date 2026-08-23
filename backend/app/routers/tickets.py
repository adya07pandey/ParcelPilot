from datetime import datetime, timezone
import secrets

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import can_access_account, get_current_user
from app.core.database import get_db
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.models import Ticket, TicketEvent, User

router = APIRouter(prefix="/tickets", tags=["tickets"])


class TicketCreateRequest(BaseModel):
    subject: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3, max_length=2000)
    category: str = Field(default="SUPPORT", max_length=128)
    subcategory: str = Field(default="OTHER", max_length=128)


class TicketMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


def serialize_ticket(ticket: Ticket) -> dict:
    return {
        "ticket_id": ticket.ticket_id,
        "account_id": ticket.account_id,
        "created_at": ticket.created_at,
        "status": ticket.status,
        "subject": ticket.subject,
        "description": ticket.description,
        "category": ticket.category,
        "subcategory": ticket.subcategory,
        "priority": ticket.priority,
        "sla_state": ticket.sla_state,
        "assigned_to": ticket.assigned_to,
        "events": [
            {
                "ticket_event_id": event.ticket_event_id,
                "event_type": event.event_type,
                "event_time": event.event_time,
                "actor_type": event.actor_type,
                "description": event.description,
            }
            for event in sorted(ticket.events, key=lambda e: e.event_time or "")
        ],
    }


@router.get("")
def list_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = select(Ticket).order_by(Ticket.created_at.desc().nullslast())
    if current_user.role == "CUSTOMER":
        query = query.where(Ticket.account_id == current_user.account_id)
    return [serialize_ticket(ticket) for ticket in db.scalars(query.options(selectinload(Ticket.events))).all()]


@router.get("/{ticket_id}")
def get_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    ticket = db.scalar(select(Ticket).where(Ticket.ticket_id == ticket_id).options(selectinload(Ticket.events)))
    if not ticket:
        raise NotFoundError("Ticket not found", code="TICKET_NOT_FOUND")
    if not can_access_account(current_user, ticket.account_id):
        raise AuthorizationError("Ticket not found or not accessible", code="TICKET_NOT_ACCESSIBLE")
    return serialize_ticket(ticket)


@router.post("")
def create_ticket(
    payload: TicketCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if not current_user.account_id:
        raise ValidationError("Customer account is required to create a ticket", code="ACCOUNT_REQUIRED")

    now = datetime.now(timezone.utc)
    ticket_id = f"TKT-{secrets.randbelow(900000) + 100000}"
    event_id = f"TEV-{secrets.randbelow(900000) + 100000}"
    ticket = Ticket(
        ticket_id=ticket_id,
        account_id=current_user.account_id,
        created_at=now,
        status="open",
        subject=payload.subject,
        description=payload.description,
        channel="web",
        assigned_to=None,
        last_customer_message_at=now,
        historical_resolution=None,
        category=payload.category.upper(),
        subcategory=payload.subcategory.upper(),
        priority="MEDIUM",
        sla_state="WITHIN_SLA",
    )
    event = TicketEvent(
        ticket_event_id=event_id,
        ticket_id=ticket_id,
        account_id=current_user.account_id,
        event_type="CREATED",
        event_time=now,
        actor_type="CUSTOMER" if current_user.role == "CUSTOMER" else "SUPPORT",
        description=payload.description,
    )
    db.add_all([ticket, event])
    db.commit()
    db.refresh(ticket)
    ticket.events = [event]
    return serialize_ticket(ticket)


@router.post("/{ticket_id}/messages")
def add_ticket_message(
    ticket_id: str,
    payload: TicketMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    ticket = db.scalar(select(Ticket).where(Ticket.ticket_id == ticket_id).options(selectinload(Ticket.events)))
    if not ticket:
        raise NotFoundError("Ticket not found", code="TICKET_NOT_FOUND")
    if not can_access_account(current_user, ticket.account_id):
        raise AuthorizationError("Ticket not found or not accessible", code="TICKET_NOT_ACCESSIBLE")

    now = datetime.now(timezone.utc)
    event = TicketEvent(
        ticket_event_id=f"TEV-{secrets.randbelow(900000) + 100000}",
        ticket_id=ticket.ticket_id,
        account_id=ticket.account_id,
        event_type="CUSTOMER_MESSAGE" if current_user.role == "CUSTOMER" else "SUPPORT_MESSAGE",
        event_time=now,
        actor_type="CUSTOMER" if current_user.role == "CUSTOMER" else "SUPPORT",
        description=payload.message,
    )
    ticket.last_customer_message_at = now if current_user.role == "CUSTOMER" else ticket.last_customer_message_at
    if ticket.status == "closed":
        ticket.status = "open"
    db.add(event)
    db.commit()
    db.refresh(ticket)
    return get_ticket(ticket_id, current_user, db)
