import re
from datetime import date, datetime

from app.models import AgentConversation

HISTORICAL_RE = re.compile(r"\b(202[0-5]|previous|old|deprecated|historical|last year|past)\b", re.IGNORECASE)


def filter_applicable_document_chunks(chunks, *, message: str, effective_at: str):
    if HISTORICAL_RE.search(message):
        return chunks

    effective_date = parse_iso_date(effective_at) or date.today()
    filtered = []
    for chunk in chunks:
        metadata = chunk.metadata or {}
        status = str(metadata.get("status") or "").upper()
        effective_to = parse_iso_date(metadata.get("effective_to"))
        if status == "DEPRECATED" and effective_to and effective_to < effective_date:
            continue
        filtered.append(chunk)
    return filtered


def parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except ValueError:
        return None


def calculate_confidence(*, evidence: list[dict], document_chunks, conversation: AgentConversation) -> tuple[int, str]:
    score = 0
    types = {item["type"] for item in evidence}
    document_types = {chunk.metadata.get("document_type") for chunk in document_chunks if chunk.metadata}
    has_current_doc = any(str(chunk.metadata.get("status") or "").upper() == "CURRENT" for chunk in document_chunks if chunk.metadata)
    has_account_doc = any((chunk.metadata or {}).get("scope") == "ACCOUNT" for chunk in document_chunks)

    if "account" in types:
        score += 15
    if document_chunks:
        score += 25
    if has_current_doc:
        score += 15
    if has_account_doc:
        score += 20
    if conversation.order_id and "order" in types:
        score += 15
    if conversation.ticket_id and "ticket" in types:
        score += 15
    if "customer_agreement" in document_types:
        score += 10

    score = max(0, min(score, 100))
    if score >= 80:
        return score, "HIGH"
    if score >= 55:
        return score, "MEDIUM"
    return score, "LOW"


def summarize_sources(evidence: list[dict]) -> list[dict]:
    sources = []
    seen = set()

    def add_source(source: dict):
        key = (
            source.get("type"),
            source.get("id"),
            source.get("document_id"),
            None if source.get("document_id") else source.get("chunk_id"),
        )
        if key not in seen:
            seen.add(key)
            sources.append(source)

    for item in evidence:
        if item["type"] == "account":
            add_source({"type": "account", "id": item["data"]["account_id"]})
        elif item["type"] == "order":
            add_source({"type": "order", "id": item["data"]["order_id"]})
        elif item["type"] == "order_list":
            add_source(
                {
                    "type": "orders",
                    "id": item.get("carrier") or "matching-orders",
                    "count": len(item.get("data") or []),
                }
            )
        elif item["type"] == "ticket":
            add_source({"type": "ticket", "id": item["data"]["ticket_id"]})
        elif item["type"] == "document":
            add_source(
                {
                    "type": "document",
                    "chunk_id": item["chunk_id"],
                    "document_id": item["metadata"].get("document_id"),
                    "score": item["score"],
                }
            )
    return sources
