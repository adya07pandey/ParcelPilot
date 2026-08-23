# ParcelPilot — Product & User Experience

## 1. Product Overview

ParcelPilot is a multi-tenant AI support platform for B2B logistics businesses.

It has three roles:
* **Customer** — manages shipments and gets AI-powered support.
* **Support** — investigates customer issues and manages tickets.
* **Admin** — manages users, accounts, knowledge, and platform configuration.

The platform has two AI experiences:
* **Customer AI Support**
* **Support AI Investigation**

---

## 2. Customer Portal

### Pages
```text
Dashboard
Orders
Tickets
AI Support
Account
```

Customers can only access data belonging to their own account.

### Orders
Customers can view:
* Order ID
* Carrier
* Shipment status
* Pickup/delivery information
* Expected timestamps
* Shipment fee

Opening an order can provide that order as context to AI Support.

### Tickets
Customers can view their own tickets, including status, priority, subject, and updates.

---

## 3. Customer AI Support

The customer starts by selecting a category:
```text
Shipments
Cancellations
Service Credits
Tickets
Product Help
Account Support
Other
```

Each category can contain subcategories. For example:
```text
Cancellations
└── Cancellation Eligibility
    ├── Cancellation Fee
    ├── Cancel Shipment
    ├── Cancellation Failure
    ├── Return-to-Origin
    └── Other
```

After selecting a subcategory, the customer enters their question.

Categories act as **retrieval hints**, not strict boundaries. If a question requires multiple sources, the AI can retrieve information across categories.

### Example
```text
Customer:
Can I cancel ORD-1001 without a fee?

AI:
Account → Order → Customer Agreement → Current SOP
                         │
                  Conflict Resolution
                         │
                       Answer
```

The AI supports multi-turn conversations and can retain the current order/conversation context.

---

## 4. Customer AI Actions

The AI can prepare actions such as:
* Create support ticket
* Cancel eligible shipment

State-changing actions require explicit confirmation. For tickets, the AI automatically fills known information:
```text
Subject
Description
Account
Order
Priority
```

The customer can edit the draft and click **Create Ticket**. For shipment cancellation, the backend verifies eligibility again before executing the cancellation.

---

## 5. Support Portal

### Pages
```text
Dashboard
Tickets
Customers
Orders
Policies & Agreements
AI Investigation
Issues & Incidents
Analytics
```

### Support Dashboard
Shows:
* Open tickets
* Priority distribution
* SLA-at-risk tickets
* SLA breaches
* Unassigned tickets
* Recurring issues

---

## 6. Support AI Investigation

Support agents can investigate an issue using:
```text
Customer
Order
Ticket
Customer Agreement
Current Policies
Product Documentation
Known Issues
Historical Tickets
```

Agents can select a company first:
```text
Northstar Logistics
LumenWorks
Beacon Retail
Axis Labs
All Customers
Other
```

They can then select a category:
```text
Shipments
Cancellations
Service Credits
Tickets
Product Issues
Support & SLA
Account
Other
```

Company and category selections help narrow the investigation and retrieval process. They do not replace backend authorization.

---

## 7. Admin Portal

### Pages
```text
Dashboard
Users
Accounts
Knowledge
Configuration
Audit Logs
Analytics
```

Admins can manage:
* Users and roles
* Customer accounts
* Agreements
* Policies and knowledge
* Platform configuration
* Audit information

---

## 8. End-to-End Flow

```text
                         LOGIN
                           │
                           ▼
                          RBAC
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
      CUSTOMER          SUPPORT           ADMIN
          │                │                │
    Customer AI       Support AI       Admin Console
          │                │
     Self-Service      Investigation
          │                │
          └────────┬───────┘
                   │
                   ▼
              Resolution
```

---

## Product Goal

ParcelPilot combines:
```text
Customer Self-Service + Evidence-Based AI + Human-Confirmed Actions + Support Investigation + Proactive Issue Visibility
```
to reduce the manual effort required to resolve logistics support issues.
