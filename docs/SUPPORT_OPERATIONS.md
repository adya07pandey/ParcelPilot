# ParcelPilot — Support Operations

## 1. Support Dashboard

The Support Dashboard gives the operations team a single centralized view of current platform support activity.

It tracks:
* Open tickets
* P1 / P2 / P3 priority distribution
* SLA-at-risk tickets
* SLA breaches
* Unassigned tickets
* Recurring operational issues

---

## 2. Ticket Queue

Support agents can filter tickets dynamically using multiple fields:
```text
Company / Priority / Status / Assignee / SLA Status / Category
```
Opening a ticket provides its full operational context, including related order parameters, tenant customer profile information, and previous message history.

---

## 3. Support AI Investigation

Support agents can investigate complex multi-domain issues using natural language queries.

### Practical Query Example
> Why is ORD-1001 eligible for cancellation without a fee?

The AI dynamically merges multiple data fields to answer:
```text
Customer + Order + Ticket + Customer Agreement + Current Policy + Product Documentation + Known Issues
```
It returns a fully compiled, evidence-backed explanation rather than requiring the agent to search each independent storage system manually.

---

## 4. Company & Category Filtering

Support agents can pre-select a company scope:
```text
Northstar Logistics / LumenWorks / Beacon Retail / Axis Labs / All Customers
```

And then select an operational category:
```text
Shipments / Cancellations / Service Credits / Tickets / Product Issues / Support & SLA / Account / Other
```
These selections act as retrieval hints to narrow the semantic investigation space. They do not act as security controls; the core backend authorization engine determines actual data access boundaries.

---

## 5. SLA Analysis

The system continually evaluates active tickets against the applicable platform support Service Level Agreement (SLA).

Tickets are labeled as:
```text
ON TRACK ──► AT RISK ──► BREACHED
```
Customer-specific agreements are analyzed when calculating response targets. For example, Northstar's explicit company agreement overrides the global standard support-policy SLA timeline.

---

## 6. Proactive Issue Visibility

The support operations dashboard surfaces anomalies and trends that require immediate human intervention:
* Recurring complaints
* Similar issues discovered across multiple distinct customers
* Known platform issue signatures
* High-probability SLA risks
* Unusual support conversation activity spikes

### System Notification Example
```text
[Potential Issue Detected]
Description: Shipment creation failures
Impact: 7 related tickets across 4 customer accounts
Common Symptom: HTTP 500 error logs
Action: [Investigate with Support AI]
```
Support AI can then ingest the related tickets and logs to investigate the root cause across authorized operations.

---

## 7. Support Actions

Support users can trigger authorized actions within the console environment:
* Update ticket state, metadata, and status
* Create automated follow-up tasks
* Escalate issues to senior tier groups
* Investigate related historical order fields
* Review customer agreement legal clauses

All state-changing actions are validated at the API layer and logged into the append-only database audit collection.

---

## 8. Support Workflow

```text
       Ticket / Issue
             │
             ▼
 Select Company / Category
             │
             ▼
      AI Investigation
             │
├────────────┼────────────┐
│            │            │
▼            ▼            ▼
Orders    Tickets    Knowledge
│            │            │
└────────────┼────────────┘
             │
             ▼
 Evidence & Recommendation
             │
             ▼
    Support Agent Review
             │
             ▼
     Authorized Action
             │
             ▼
         Resolution
```
The architecture minimizes the manual coordination cost required to jump between tools, while keeping final operational decisions under strict human control.
