# ParcelPilot

### AI-Powered Customer Support & Operations Platform

> From customer question to operational resolution — with evidence at every step.

[Live Demo] [Demo Video] [Architecture] [Product Note]

---

## What is ParcelPilot?

ParcelPilot is a multi-tenant AI support platform for B2B logistics.

It provides:

- Customer-facing AI support
- Account-aware shipment and ticket investigation
- Contract-aware policy reasoning
- Human-in-the-loop support escalation
- AI-powered support investigation
- Proactive issue detection

---

## The Problem

ParcelPilot support teams must reason across:

Customer agreements
→ Current policies
→ Product documentation
→ Orders
→ Tickets
→ Historical support context

These sources may conflict, become outdated, or contain incorrect historical guidance.

ParcelPilot provides an AI layer that retrieves the right evidence,
respects source authority, enforces tenant isolation, and escalates
when it cannot reliably answer.

---

## Product

### Customer Portal

Customer
→ Choose problem category
→ Ask AI
→ Retrieve account-specific data
→ Retrieve applicable policies
→ Answer / explain uncertainty
→ Create support ticket when required

### Support Portal

Ticket
→ AI Investigation
→ Orders + Account + Tickets + Knowledge
→ Policy / Agreement resolution
→ Evidence
→ Confidence
→ Recommendation
→ Human resolution

---

## Key Design Decisions

### Customer agreements override general policies

### Historical tickets are context, not policy authority

### Customer data is tenant-scoped

### State-changing workflows require confirmation

### Confidence is deterministic

### AI recommendations remain human-reviewable

---

## Architecture

[diagram]

See [Architecture Note](docs/02_ARCHITECTURE.md).

---

## Tech Stack

React · FastAPI · PostgreSQL · LangGraph · Qdrant · Voyage AI · Groq · JWT · Docker

---

## Documentation

| Document | Purpose |
|---|---|
| Product Overview | Product and user workflows |
| Architecture | System architecture |
| Customer AI | Customer-facing agent |
| Support AI | Support investigation agent |
| Trust & Reliability | Source hierarchy and confidence |
| Security | RBAC and tenant isolation |
| Proactive Detection | Recurring issue detection |
| Data & RAG | Qdrant and structured data |
| Product Decisions | Product reasoning |
| Trade-offs | Technical decisions |
| Demo Script | 5-minute walkthrough |
| AI Tool Usage | Coding AI usage |
| Submission Checklist | Final submission |

---

## Running Locally

...

## Demo Accounts

...

## License
