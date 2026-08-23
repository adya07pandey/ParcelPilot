# ParcelPilot — System Architecture

## 1. Architecture Overview

ParcelPilot follows a multi-tenant architecture where authentication, structured data, knowledge retrieval, and AI reasoning are separated.

```text
Customer / Support / Admin
            │
        Web Application
            │
          API
            │
      Authentication
          + RBAC
            │
     ┌──────┴──────┐
     │             │
 Structured     Knowledge
   Data          Base
     │             │
     └──────┬──────┘
            │
        LangGraph
            │
      Tool Selection
            │
     Evidence Analysis
            │
     Confidence Check
            │
      Response / Action
```

---

## 2. Agent Architecture

LangGraph manages the state of an AI interaction and coordinates multiple tools when a request requires information from different sources.

```text
User Query
    │
    ▼
Understand Intent
    │
    ▼
Identify Required Information
    │
    ├───────────────────┬───────────────────┐
    │                                       │
    ▼                                       ▼
Structured Data                     Knowledge Search
    │                                       │
 Orders / Tickets                    Policies / Agreements
 Accounts                            SOPs / Product Docs
    │                                       │
    └───────────────────┬───────────────────┘
                        │
                        ▼
                 Evidence Merge
                        │
                        ▼
             Source Conflict Check
                        │
                        ▼
             Deterministic Confidence
                        │
                  ┌─────┴─────┐
                  │           │
                  ▼           ▼
                Answer      Uncertain
                              │
                              ▼
                        Ticket Proposal
```

A request can execute multiple tools before the final response is generated.

---

## 3. Tool Architecture

The agent does not directly access databases or application state. It interacts through controlled backend tools.

### Structured-Data Tools
```text
get_account()
get_order()
search_orders()
get_ticket()
search_tickets()
```

### Knowledge Retrieval
```text
search_knowledge()
```
This retrieves relevant documents from Qdrant using semantic search and metadata filters.

### Calculation / Decision Tools
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
State-changing tools require explicit user confirmation.

---

## 4. Customer AI Flow

```text
Customer Query
      │
      ▼
Authenticated Account Context
      │
      ▼
Intent + Entity Detection
      │
      ▼
Select Tools
      │
      ├──────────────────┬──────────────────┐
      │                                     │
      ▼                                     ▼
Order / Ticket                      Policy / Agreement
Lookup                              Retrieval
      │                                     │
      └──────────────────┬──────────────────┘
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
                       Answer
```

### Flow Example
```text
"Can I cancel ORD-1001 without a fee?"

        │
        ├──► Get Order
        ├──► Get Customer Account
        ├──► Retrieve Cancellation SOP
        ├──► Retrieve Customer Agreement
        ├──► Resolve Agreement vs SOP
        ├──► Determine Eligibility
        └──► Answer
```

---

## 5. Support AI Flow

Support AI follows the same core architecture but can investigate a broader scope of authorized customer data.

```text
Support Agent
      │
Company / Category
      │
Investigation Question
      │
Authorization Check
      │
┌─────┼─────────┬─────────┐
│               │         │
▼               ▼         ▼
Orders        Tickets   Knowledge
│               │         │
└───────────────┼─────────┘
                │
                ▼
         Evidence Analysis
                │
                ▼
          AI Investigation
                │
                ▼
          Recommendation
```
Company and category selections act as retrieval hints. They do not replace backend authorization and do not prevent the agent from retrieving information from another relevant category.

---

## 6. Knowledge Retrieval

Documents are stored with metadata so retrieval can respect both tenant scope and document applicability.

### Metadata Schema Example
```text
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

For a customer request, retrieval is compiled from:
```text
Global Documents + Documents belonging to the authenticated account
```
Documents belonging to other customer accounts are strictly excluded by the metadata layer.

---

## 7. Source Resolution

When multiple sources are retrieved, the agent applies the defined source precedence rules:

```text
Signed Customer Agreement > Current ParcelPilot Policy > Current Product Documentation > Historical Tickets
```

This structural hierarchy prevents an outdated policy or incorrect historical ticket resolution from overriding an applicable customer agreement or current corporate standard.

---

## 8. State-Changing Actions

The LLM never directly mutates application state.

```text
AI determines action
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
Audit / Log
```
For example, before cancelling an order, the backend checks the latest operational order status and cancellation eligibility parameters again.

---

## 9. Multi-Tenant Boundary

Tenant isolation is strictly enforced at the backend and tool layer.

### Customer Isolation
```text
Authenticated Customer
        │
        ▼
   Own Account
        ├──► Own Orders
        ├──► Own Tickets
        ├──► Own Agreement
        └──► Global Knowledge
```

### Support User Isolation
```text
Authorized Support User
        │
        ▼
Authorized Accounts
        ├──► Orders
        ├──► Tickets
        ├──► Agreements
        └──► Global Knowledge
```
The LLM is never trusted to calculate or enforce these logical boundaries.

---

## 10. Conversation State

The active AI conversation is persisted so that a customer can navigate away from the AI Support view and return without losing their active session context.

An active session schema tracks:
```text
conversation_id
account_id
selected_category
selected_order
messages
current_intent
```
Starting a new conversation explicitly closes out the active session.

---

## 11. Key Architectural Principle

The LLM is exclusively responsible for reasoning and deciding which tools are required. The application backend holds the definitive responsibility for security enforcement and state validation.

```text
              LLM
               │
        Reasoning / Planning
               │
               ▼
        Controlled Tools
               │
       Authorization +
       Business Rules
               │
               ▼
       Data / Application State
```
This engineering pattern keeps the generative AI layers modular and flexible, while ensuring security and critical business logic remain deterministic and safe.
