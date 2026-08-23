# ParcelPilot — Security & Multi-Tenancy

## 1. Roles

ParcelPilot has three roles:
```text
CUSTOMER / SUPPORT / ADMIN
```
Each role has a distinct access scope.

| Role | Access |
| :--- | :--- |
| **Customer** | Own account and company data |
| **Support** | Authorized customer accounts and support data |
| **Admin** | Platform-level management and platform configuration |

---

## 2. Authentication

Users authenticate through the following process:
```text
Email + Password ──► Password Verification ──► JWT ──► HTTP-only Cookie
```
The backend validates the session cookie on every protected request.

---

## 3. RBAC (Role-Based Access Control)

Role checks are explicitly enforced by the backend on the API layer.
* **Customer** — Cannot access another customer's account or operational logs.
* **Support** — Cannot access unauthorized internal or administrative accounts.
* **Admin** — Can manage users, adjust platform configuration, and view audit trails.

The frontend only controls what is displayed in the UI; it is not considered a security boundary.

---

## 4. Tenant Isolation

Every customer-owned resource is associated with an `account_id` at the database level.

```text
Authenticated User ──► Account Context ──► Authorized Tools ──► Scoped Data
```

For a customer, access is strictly limited to their own structural hierarchy:
```text
Own Account
 ├── Orders
 ├── Tickets
 └── Agreement
```
Data from another account cannot be queried or returned by customer-facing backend routes.

---

## 5. Qdrant Isolation

Qdrant documents contain tenant metadata attributes for vector-space filtering:
```text
account_id
scope
document_type
```

Customer retrieval is restricted to:
```text
GLOBAL documents + Authenticated customer's documents
```
For example, a Northstar customer can retrieve the Northstar agreement but cannot retrieve the LumenWorks agreement.

---

## 6. Tool-Level Authorization

Security is enforced inside the tool/data layer rather than relying on LLM prompt instructions. Before tools execute, the backend validates the user's identity, role, and account access constraints.

**Protected Read/Write Tools:**
* `get_order()`
* `get_ticket()`
* `search_orders()`
* `create_ticket()`
* `cancel_shipment()`

---

## 7. State-Changing Actions

Actions require both explicit user confirmation and final backend authorization and validation.

```text
AI prepares action
       │
       ▼
User confirms
       │
       ▼
Backend checks authorization
       │
       ▼
Backend re-checks current state
       │
       ▼
Action executed
       │
       ▼
Audit logged
```
This prevents the AI from directly mutating or changing application state without a verified user transaction loop.

---

## 8. Security Principle

The core security principle is:
> **The LLM is never trusted to enforce access control.**

Authentication, RBAC, tenant isolation, business rules, and state-changing permissions are exclusively enforced by the deterministic backend.
