from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Role(str, Enum):
    CUSTOMER = "CUSTOMER"
    SUPPORT = "SUPPORT"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    company: Mapped[str | None] = mapped_column(String(255))
    account_id: Mapped[str | None] = mapped_column(ForeignKey("accounts.account_id"))
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)

    account = relationship("Account", back_populates="users")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
