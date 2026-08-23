from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"), index=True, nullable=False)
    carrier: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str | None] = mapped_column(String(64))
    booked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pickup_window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pickup_window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pickup_actual_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    shipment_fee_inr: Mapped[float | None] = mapped_column(Float)
    carrier_fault: Mapped[bool | None] = mapped_column(Boolean)
    customer_fault: Mapped[bool | None] = mapped_column(Boolean)
    cancellation_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    origin: Mapped[str | None] = mapped_column(String(255))
    destination: Mapped[str | None] = mapped_column(String(255))
    estimated_delivery_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_delivery_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_location: Mapped[str | None] = mapped_column(String(255))
    pickup_delay_minutes: Mapped[int | None] = mapped_column(Integer)
    delivery_delay_minutes: Mapped[int | None] = mapped_column(Integer)

    events = relationship("ShipmentEvent", back_populates="order")


class ShipmentEvent(Base):
    __tablename__ = "shipment_events"

    event_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.order_id"), index=True, nullable=False)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.account_id"), index=True, nullable=False)
    event_type: Mapped[str | None] = mapped_column(String(128))
    event_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    carrier: Mapped[str | None] = mapped_column(String(128))
    location: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(64))

    order = relationship("Order", back_populates="events")
