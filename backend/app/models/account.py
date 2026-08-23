from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Account(Base):
    __tablename__ = "accounts"

    account_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str | None] = mapped_column(String(64))
    csm: Mapped[str | None] = mapped_column(String(255))
    contract_file: Mapped[str | None] = mapped_column(String(255))
    premium_support: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    users = relationship("User", back_populates="account")
