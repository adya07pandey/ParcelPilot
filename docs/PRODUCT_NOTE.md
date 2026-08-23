# Product Note

## Additional Client Problem Chosen

I chose the support team's operational visibility problem: support agents need to understand urgent tickets, customer context, related shipments, agreement overrides, and recurring issue patterns without jumping between separate tools.

To address this, ParcelPilot includes a support-team portal with:

- Dashboard KPIs for open tickets, high-priority tickets, SLA risk, breached SLA, and unassigned tickets.
- Priority queue sorted by severity and SLA risk.
- Recent AI escalations created from customer AI support.
- Ticket queue with filters for company, priority, status, source, and date.
- Ticket detail workspace with customer context, linked order, SLA, timeline, and AI conversation context.
- Customer 360 view with account overview, orders, tickets, and agreement summary.
- Orders investigation page with carrier/status/account search and related tickets.
- Policies & Agreements page showing general policies, customer agreements, and override behavior.
- Issues & Incidents page showing simple detected patterns from ticket data.

This makes the project more than a customer chatbot. It shows how AI support handoff becomes useful to the actual team that must resolve issues.

## What Else I Would Build

Next, I would build the advanced support-side AI layer:

- AI investigation button on ticket detail.
- Similar-ticket detection with embeddings.
- Incident clustering across accounts.
- Known-issue matching from product operations documentation.
- Suggested customer replies for support agents.
- SLA breach prediction.
- Escalation recommendation with audit trail.
- Support analytics for categories, carriers, and product areas.
- Real cancellation/service-credit backend actions after approval and audit logging.

## What I Intentionally Left Out

- Fully automated shipment cancellation. The current flow creates a support request after confirmation rather than mutating shipment state directly.
- Automatic incident declaration. Part 1 shows detected patterns but does not yet create incidents autonomously.
- Payment/billing integrations.
- Full support-agent workflow actions such as assignment mutation, status updates, and resolution notes.
- Complex admin configuration screens.
- Full evaluation harness for measuring answer accuracy across many test prompts.

These were left out to keep the submission focused on trustworthy account-aware support, clean handoff, and safe action confirmation.

## Metric for Usefulness

Primary metric:

```text
AI-assisted ticket deflection or resolution rate with no increase in reopened tickets.
```

This should be paired with:

- Percentage of AI answers with high-confidence evidence.
- Number of support tickets created with complete account/order/context data.
- Time-to-first-meaningful-support-action for AI escalations.
- Reopen rate or correction rate for AI-assisted answers.

The product is useful only if it reduces support effort while preserving trust and correctness.
