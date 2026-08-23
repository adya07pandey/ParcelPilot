# ParcelPilot — AI, RAG & Trust

## 1. RAG Architecture

ParcelPilot uses Qdrant for semantic retrieval over support policies, cancellation/SLA SOPs, product documentation, known issues, customer agreements, and historical tickets. The LLM receives retrieved evidence instead of relying only on its internal knowledge.

```text
User Query
    │
    ▼
Intent + Context
    │
    ▼
Qdrant + Structured Data
    │
    ▼
Evidence
    │
    ▼
Conflict Resolution
    │
    ▼
Confidence
    │
    ▼
Response / Action
```

---

## 2. Tenant-Aware Retrieval

Every document has metadata such as:
```text
account_id
scope
document_type
version
status
effective_from
effective_to
category
authority
```

For a customer, retrieval is strictly limited to:
```text
Global Documents + That Customer's Documents
```
Documents belonging to other customers are never retrieved. Categories are used as retrieval hints, not hard boundaries.

---

## 3. Policy Versioning

The knowledge base stores policy versions and their status.
```text
Support Policy v2 ──► DEPRECATED
Support Policy v3 ──► CURRENT
```
Current requests use the applicable current policy. Deprecated policies are retained for historical context but are not treated as current authority.

---

## 4. Source Precedence

When sources conflict, the system enforces a strict hierarchical order:

```text
Signed Customer Agreement > Current ParcelPilot Policy > Current Product Documentation > Historical Tickets
```

* **Customer Agreements**: Customer-specific agreements override general policies when applicable.
* **Historical Tickets**: Resolutions are treated only as context because they may contain incorrect guidance.

---

## 5. Deterministic Confidence

The LLM does not generate its own confidence score. Confidence is calculated programmatically from evidence quality, including required data availability, source authority, source freshness, customer applicability, and conflicts.

### Confidence Tiers
* **HIGH (80–100)** — Answer directly.
* **MEDIUM (50–79)** — Explain what is known and what is missing, then offer ticket creation.
* **LOW (0–49)** — Do not guess. Explain the limitation and recommend escalation.

---

## 6. Practical Scenario Example

For the request:
> Can Northstar cancel ORD-1001 without a fee?

The agent retrieves:
```text
ORD-1001 + Northstar Agreement + Cancellation SOP
```
If the corporate SOP dictates that a cancellation fee applies but the unique Northstar customer agreement waives it, the agreement takes precedence. The response explains the override and provides the resulting answer with its deterministic confidence.

---

## 7. Trust Principle

ParcelPilot separates:
```text
LLM Reasoning + Retrieved Evidence + Business Rules + Deterministic Confidence
```
The LLM can reason over evidence, but it does not decide access permissions, policy precedence, or its own confidence boundaries.
