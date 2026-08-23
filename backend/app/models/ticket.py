from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"), index=True, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str | None] = mapped_column(String(64))
    subject: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    channel: Mapped[str | None] = mapped_column(String(64))
    assigned_to: Mapped[str | None] = mapped_column(String(255))
    last_customer_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    historical_resolution: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(128))
    subcategory: Mapped[str | None] = mapped_column(String(128))
    priority: Mapped[str | None] = mapped_column(String(64))
    sla_state: Mapped[str | None] = mapped_column(String(64))

    events = relationship("TicketEvent", back_populates="ticket")


class TicketEvent(Base):
    __tablename__ = "ticket_events"

    ticket_event_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.ticket_id"), index=True, nullable=False)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"), index=True, nullable=False)
    event_type: Mapped[str | None] = mapped_column(String(128))
    event_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actor_type: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text)

    ticket = relationship("Ticket", back_populates="events")


class Escalation(Base):
    __tablename__ = "escalations"

    escalation_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    ticket_id: Mapped[str | None] = mapped_column(ForeignKey("tickets.ticket_id"), index=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"), index=True, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    priority: Mapped[str | None] = mapped_column(String(64))
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(64))
    prepared_by: Mapped[str | None] = mapped_column(String(255))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
