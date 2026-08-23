# Architecture Note

## System Overview

ParcelPilot is split into a React frontend and a FastAPI backend. The backend owns authentication, authorization, data access, AI orchestration, and all tenant boundaries. The frontend provides two role-specific portals:

- Customer portal: dashboard, orders, tickets, AI support.
- Support portal: ticket queue, customer 360, order investigation, policy/agreement views, incident pattern views.

The core design principle is:

```text
Guided UX, flexible reasoning, strict data isolation.
```

## Agent Design

The customer AI support agent starts with a guided category and subcategory flow. Categories are routing hints, not hard boundaries. After the user selects a topic, they can ask a natural-language question. The agent maintains conversation context in PostgreSQL, including:

```text
conversation_id
user_id
account_id
category
subcategory
active_order_id
active_ticket_id
pending_action
last_confidence
```

The agent workflow is:

```text
Customer message
  -> restore authenticated user/account context
  -> restore conversation context
  -> extract order/ticket/carrier entities
  -> infer intent
  -> load account-scoped structured data
  -> retrieve allowed documents from Qdrant
  -> filter document versions
  -> calculate deterministic confidence
  -> answer or prepare an explicit confirmation action
```

State-changing actions are not executed silently. For example, cancellation creates a support-ticket request only after the customer confirms the preview.

## Tool Design

The agent does not receive raw SQL access. It uses backend-controlled tool-style functions:

- `get_authorized_account`
- `get_authorized_order`
- `find_authorized_order`
- `list_authorized_orders_by_carrier`
- `get_authorized_ticket`
- `search_authorized_documents`
- `create_ticket_from_pending_action`
- `confirm_cancellation_action`

Every structured-data tool receives the authenticated user and enforces account scope before returning data. Customer users only see their account; support/admin users can inspect cross-account records.

## Document Handling

Documents are extracted from PDFs and chunked by the ingest script. Chunks are embedded with Voyage AI and stored in Qdrant with metadata such as:

```json
{
  "document_id": "northstar-enterprise-agreement",
  "document_type": "customer_agreement",
  "scope": "ACCOUNT",
  "account_id": "ACCT-001",
  "status": "CURRENT",
  "effective_from": "2026-01-01",
  "effective_to": "2026-12-31"
}
```

Retrieval is restricted to:

```text
GLOBAL documents OR documents matching current_user.account_id
```

This restriction is enforced in backend retrieval code, not by prompting the LLM.

## Structured Data Handling

Operational data lives in PostgreSQL:

- accounts
- users
- orders
- shipment events
- tickets
- ticket events
- AI conversations
- AI messages
- refresh tokens

Orders and tickets are the source of truth for shipment status, event history, ticket state, and customer context. Documents explain policy, agreements, and product behavior; structured tables establish operational facts.

## Source Reliability and Conflict Handling

The source hierarchy is:

1. Account-specific signed agreement, when it explicitly covers the issue.
2. Current global policy/SOP.
3. Current product operations documentation.
4. Structured operational data for order/ticket/account facts.
5. Historical tickets only as context, never as policy.

When a customer agreement conflicts with a general policy, the agreement wins only for that customer and only for the covered clause. Example: Northstar's agreement overrides the generic cancellation fee for booked shipments before pickup.

Confidence is deterministic and based on evidence availability, not an LLM self-rating. Signals include account match, authoritative document availability, current policy version, agreement match, and structured operational evidence.

## Major Technical Trade-Offs

- Used FastAPI and SQLAlchemy instead of a heavier backend framework to keep the assessment focused and transparent.
- Used guided chat categories to improve UX while keeping retrieval flexible.
- Used backend-enforced data-access helpers instead of giving the LLM raw database access.
- Used Qdrant metadata filters for tenant isolation because prompt-only isolation is not reliable.
- Kept state-changing workflows confirmation-based rather than fully automated to avoid unsafe cancellation or ticket creation behavior.
- Built a production-deployable structure, but left advanced support-side AI recommendations and automatic incident clustering as future work.
