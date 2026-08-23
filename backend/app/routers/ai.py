from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.ai.service import (
    confirm_cancellation_action,
    create_ticket_from_pending_action,
    get_current_conversation_state,
    reset_current_conversation,
    run_customer_agent,
)
from app.core.config import get_settings
from app.core.database import get_db
from app.models import User

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = None
    category: str | None = Field(default=None, max_length=128)
    subcategory: str | None = Field(default=None, max_length=128)
    order_id: str | None = None
    ticket_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    confidence: str
    confidence_score: int
    active_context: dict
    sources: list[dict]
    provider_ready: bool
    ticket_preview: dict | None = None
    action_preview: dict | None = None


class TicketConfirmRequest(BaseModel):
    conversation_id: str
    subject: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, min_length=3, max_length=2000)


class ActionConfirmRequest(BaseModel):
    conversation_id: str


@router.get("/providers")
def provider_status(current_user: User = Depends(get_current_user)) -> dict:
    settings = get_settings()
    return {
        "voyage": {
            "configured": bool(settings.voyage_api_key),
            "embedding_model": settings.voyage_embedding_model,
        },
        "qdrant": {
            "configured": bool(settings.qdrant_url),
            "collection": settings.qdrant_collection,
        },
        "groq": {
            "configured": bool(settings.groq_api_key),
            "model": settings.groq_model,
        },
        "dataset_snapshot_time": settings.dataset_snapshot_time,
    }


@router.get("/conversation")
def current_conversation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return get_current_conversation_state(db, current_user=current_user)


@router.post("/conversation/new")
def new_conversation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return reset_current_conversation(db, current_user=current_user)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return await run_customer_agent(
        db,
        current_user=current_user,
        message=payload.message,
        conversation_id=payload.conversation_id,
        category=payload.category,
        subcategory=payload.subcategory,
        order_id=payload.order_id,
        ticket_id=payload.ticket_id,
    )


@router.post("/tickets/confirm")
def confirm_ticket(
    payload: TicketConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return create_ticket_from_pending_action(
        db,
        current_user=current_user,
        conversation_id=payload.conversation_id,
        subject=payload.subject,
        description=payload.description,
    )


@router.post("/actions/cancel/confirm")
def confirm_cancel(
    payload: ActionConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return confirm_cancellation_action(
        db,
        current_user=current_user,
        conversation_id=payload.conversation_id,
    )
