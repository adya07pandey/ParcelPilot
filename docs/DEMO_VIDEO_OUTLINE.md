# Demo Video Outline

Target length: about 5 minutes.

## 1. Introduction: 20-30 seconds

Show the README and hosted app links.

Cover:

- ParcelPilot is a logistics support portal.
- It has customer, support, and admin roles.
- The main AI feature is an account-aware support assistant with document and structured-data access.

## 2. Architecture: 60-75 seconds

Show the architecture note or briefly explain the stack.

Cover:

- React/Vite frontend.
- FastAPI backend.
- Neon PostgreSQL for structured operational data.
- Qdrant for retrieved document chunks.
- Voyage AI for embeddings.
- Groq for LLM responses.
- JWT access token plus HttpOnly refresh cookie.
- RBAC and account-level authorization.

Mention that the LLM does not get raw SQL access. It uses scoped backend tools for orders, tickets, account data, and document search.

## 3. Customer Demo: 90 seconds

Log in as:

```text
aarav@northstar.example
Demo@123
```

Show:

- Customer dashboard.
- Orders page and an order detail page.
- Tickets page.
- AI Support guided category/subcategory flow.

Suggested AI prompts:

```text
What are my contract terms?
Can I cancel ORD-1001 without a cancellation fee?
Where is my SwiftShip order?
```

Point out:

- The assistant can use customer agreement terms.
- It can inspect order status itself.
- It only shows data for the authenticated account.
- Medium/low confidence flows offer ticket creation instead of guessing.

## 4. Support-Team Demo: 90 seconds

Log in as:

```text
rohit@parcelpilot.example
Demo@123
```

Show:

- Support dashboard.
- Ticket queue sorted by priority.
- Filters by company, priority, status, source, and date.
- Ticket detail page with customer, order, and AI context.
- Customer 360 page.
- Orders investigation page.
- Policies & Agreements page.
- Issues & Incidents page.

Explain that this support portal is the additional client problem: support agents need operational visibility after AI escalation.

## 5. Technical Decisions: 45-60 seconds

Cover:

- Guided UX gives users a starting point but does not restrict retrieval.
- Account isolation is enforced in backend queries and Qdrant metadata filters.
- Customer agreement overrides generic policy only when applicable.
- Historical/deprecated documents are lower authority.
- Ticket/action creation requires explicit confirmation.
- Conversation state is persisted so users can leave AI support and return.

## 6. Closing: 15-20 seconds

Summarize:

- Working hosted application.
- Public GitHub repo.
- Architecture/product notes included.
- What would come next: deeper support-side AI workflows, incident clustering, SLA prediction, and real audited operational actions.
