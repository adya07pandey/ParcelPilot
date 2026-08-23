# ParcelPilot — System Architecture

## 1. Architecture Overview

ParcelPilot uses a multi-tenant architecture with separate layers for:
* Authentication and RBAC
* Structured operational data
* Document retrieval
* AI agent orchestration
* State-changing actions

```text
Customer / Support / Admin
            │
         React
            │
         FastAPI
            │
     Authentication + RBAC
            │
     ┌──────┴──────┐
     │             │
PostgreSQL       Qdrant
     │             │
Orders          Policies
Tickets         Agreements
Accounts        SOPs
Users           Product Docs
     │             │
     └──────┬──────┘
            │
        LangGraph
            │
           LLM
            │
      Tool Selection
            │
      Evidence + Reasoning
            │
      Response / Action
```

---

## 2. Frontend

The frontend is built with React. It provides separate interfaces based on the authenticated user's role:
```text
Customer → Customer Portal
Support  → Support Portal
Admin    → Admin Portal
```

The frontend communicates with the backend through REST APIs and handles:
* Chat interface
* Dashboards
* Order and ticket views
* Category selection
* Action confirmation
* Ticket draft editing
* Role-based navigation

Authorization is not trusted to the frontend; the backend performs the actual access checks.

---

## 3. Backend

The backend is built with FastAPI. It handles:
* Authentication
* RBAC
* Tenant isolation
* Business logic
* Database access
* AI agent execution
* Tool execution
* State-changing actions
* Logging and error handling

The AI agent never receives unrestricted database access. Instead, it interacts through controlled backend tools.

---

## 4. PostgreSQL

PostgreSQL stores structured operational data. Main entities include:
```text
Users
Accounts
Orders
Tickets
Conversations
Actions
Audit Logs
```

Example relationships:
```text
Account
  ├── Users
  ├── Orders
  └── Tickets
```
The authenticated account context is used to restrict customer queries to their own data.

---

## 5. Qdrant

Qdrant is used as the vector database for ParcelPilot's document knowledge base. Documents include support policies, cancellation SOPs, customer agreements, product documentation, and known issues.

Each chunk contains metadata such as:
```text
document_id
document_type
account_id
scope
version
status
effective_from
effective_to
category
authority
```
This allows retrieval to be filtered by tenant, document status, category, and applicability.

---

## 6. LangGraph Agent

LangGraph orchestrates the AI workflow. A typical customer request follows:

```text
User Query
    │
    ▼
Intent / Entity Identification
    │
    ▼
Determine Required Tools
    │
    ├───────────────────┬───────────────────┐
    │                                       │
    ▼                                       ▼
Structured Lookup                       Qdrant Retrieval
    │                                       │
    └───────────────────┬───────────────────┘
                        │
                        ▼
                Evidence Analysis
                        │
                        ▼
               Conflict Resolution
                        │
                        ▼
             Deterministic Confidence
                        │
                        ▼
                  Final Response
```
Complex questions can execute multiple tools before producing an answer.

---

## 7. Agent Tools

The agent uses controlled tools rather than directly accessing databases.

### Read Tools
```text
get_account()
get_order()
search_orders()
get_ticket()
search_tickets()
```

### Knowledge Tool
```text
search_knowledge()
```
This searches Qdrant using semantic retrieval and metadata filters.

### Calculation / Decision Tools
Examples:
```text
calculate_sla()
check_cancellation_eligibility()
calculate_service_credit()
```

### State-Changing Tools
```text
create_ticket()
cancel_shipment()
```
State-changing tools require explicit confirmation before execution.

---

## 8. Multi-Step Investigation

A single request may require several tools.

Example:
> Can Northstar cancel ORD-1001 without a fee?

```text
get_account()
      │
      ▼
get_order()
      │
      ▼
search_knowledge()
      │
      ├─► Northstar Agreement
      │
      └─► Cancellation SOP
      │
      ▼
Resolve Policy Conflict
      │
      ▼
Determine Eligibility
      │
      ▼
Generate Answer
```
The same architecture is used by Support AI for more complex investigations.

---

## 9. Support AI Architecture

Support AI has a wider investigation scope than Customer AI.

```text
Support Agent
      │
Company / Category
      │
Investigation Query
      │
Authorization Check
      │
┌─────┼─────────┬─────────┐
│               │         │
▼               ▼         ▼
PostgreSQL     Qdrant   Tickets
│               │         │
└───────────────┼─────────┘
                │
          Evidence Merge
                │
          AI Investigation
                │
          Recommendation
```
Company and category selections help narrow retrieval, while backend authorization determines the actual accessible data.

---

## 10. State-Changing Workflow

Actions are never executed directly from an LLM response.

```text
AI decides action is required
            │
            ▼
     Prepare action
            │
            ▼
    User confirmation
            │
            ▼
   Backend authorization
            │
            ▼
    Re-check current state
            │
            ▼
      Execute action
            │
            ▼
       Audit action
```

Before cancelling a shipment, the backend verifies that:
* The user owns or is authorized to operate on the order.
* The order still exists.
* The order is eligible for cancellation.
* The current state has not changed.

---

## 11. Conversation Architecture

The current AI conversation is stored so users can leave the AI Support page and return without losing the active conversation. 

The system maintains the active conversation context rather than indefinitely storing every conversational state as an active session. Starting a new conversation closes the previous active session. Conversation history can still be retained separately if required for ticket or audit purposes.

---

## 12. Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | React |
| **Backend** | FastAPI |
| **Database** | PostgreSQL |
| **Vector Database** | Qdrant |
| **Agent Orchestration** | LangGraph |
| **LLM** | Groq-hosted open-source LLM |
| **Embeddings** | Voyage AI |
| **Authentication** | JWT + HTTP-only Cookies |
| **Authorization** | RBAC + Tenant Scoping |
| **Containerization** | Docker |

---

## 13. Key Architectural Principle

The LLM is responsible for **reasoning and tool selection**, not for enforcing security or directly changing application state.

```text
LLM
 │
 │ decides what information/action is needed
 ▼
Backend Tools
 │
 │ enforce authorization and business rules
 ▼
Data / State
```
This separation makes the system safer, more deterministic, and easier to audit.
