from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AgentConversation(Base):
    __tablename__ = "agent_conversations"

    conversation_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), index=True, nullable=False)
    account_id: Mapped[str | None] = mapped_column(ForeignKey("accounts.account_id"), index=True)
    category: Mapped[str | None] = mapped_column(String(128))
    subcategory: Mapped[str | None] = mapped_column(String(128))
    order_id: Mapped[str | None] = mapped_column(String(32))
    ticket_id: Mapped[str | None] = mapped_column(String(32))
    pending_action: Mapped[dict | None] = mapped_column(JSON)
    last_confidence: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    messages = relationship("AgentMessage", back_populates="conversation")


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    message_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("agent_conversations.conversation_id"),
        index=True,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_metadata: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    conversation = relationship("AgentConversation", back_populates="messages")
