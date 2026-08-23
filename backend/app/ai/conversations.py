import secrets
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ai.parsing import normalize_context_value
from app.core.exceptions import AuthorizationError
from app.models import AgentConversation, AgentMessage, User


def get_or_create_conversation(
    db: Session,
    *,
    current_user: User,
    conversation_id: str | None,
    category: str | None = None,
    subcategory: str | None = None,
    order_id: str | None = None,
    ticket_id: str | None = None,
) -> AgentConversation:
    now = datetime.now(timezone.utc)
    conversation = db.get(AgentConversation, conversation_id) if conversation_id else None
    if conversation and conversation.user_id != current_user.user_id:
        raise AuthorizationError("Conversation not accessible", code="CONVERSATION_NOT_ACCESSIBLE")
    if not conversation:
        conversation = AgentConversation(
            conversation_id=f"CONV-{secrets.token_urlsafe(12)}",
            user_id=current_user.user_id,
            account_id=current_user.account_id,
            category=normalize_context_value(category),
            subcategory=normalize_context_value(subcategory),
            order_id=order_id,
            ticket_id=ticket_id,
            created_at=now,
            updated_at=now,
        )
        db.add(conversation)
    else:
        conversation.updated_at = now
        conversation.category = normalize_context_value(category) or conversation.category
        conversation.subcategory = normalize_context_value(subcategory) or conversation.subcategory
        conversation.order_id = order_id or conversation.order_id
        conversation.ticket_id = ticket_id or conversation.ticket_id
    return conversation


def append_message(
    db: Session,
    *,
    conversation_id: str,
    role: str,
    content: str,
    metadata: dict | None = None,
) -> AgentMessage:
    message = AgentMessage(
        message_id=f"MSG-{secrets.token_urlsafe(12)}",
        conversation_id=conversation_id,
        role=role,
        content=content,
        message_metadata=metadata,
        created_at=datetime.now(timezone.utc),
    )
    db.add(message)
    return message


def get_current_conversation_state(db: Session, *, current_user: User) -> dict:
    conversation = db.scalar(
        select(AgentConversation)
        .where(AgentConversation.user_id == current_user.user_id)
        .order_by(AgentConversation.updated_at.desc())
        .limit(1)
    )
    if not conversation:
        return {"conversation_id": None, "messages": [], "active_context": {}}

    messages = db.scalars(
        select(AgentMessage)
        .where(AgentMessage.conversation_id == conversation.conversation_id)
        .order_by(AgentMessage.created_at.asc())
    ).all()
    return {
        "conversation_id": conversation.conversation_id,
        "messages": [
            {
                "role": message.role,
                "content": message.content,
                "metadata": message.message_metadata or {},
                "created_at": message.created_at,
            }
            for message in messages
        ],
        "active_context": {
            "category": conversation.category,
            "subcategory": conversation.subcategory,
            "order_id": conversation.order_id,
            "ticket_id": conversation.ticket_id,
            "account_id": conversation.account_id,
            "pending_action": conversation.pending_action,
        },
    }


def reset_current_conversation(db: Session, *, current_user: User) -> dict:
    conversation_ids = [
        row[0]
        for row in db.execute(
            select(AgentConversation.conversation_id).where(AgentConversation.user_id == current_user.user_id)
        ).all()
    ]
    if conversation_ids:
        db.execute(delete(AgentMessage).where(AgentMessage.conversation_id.in_(conversation_ids)))
        db.execute(delete(AgentConversation).where(AgentConversation.conversation_id.in_(conversation_ids)))
        db.commit()
    return {"conversation_id": None, "messages": [], "active_context": {}}
