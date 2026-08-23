import { CircleAlert, PackageCheck, TicketCheck, Truck } from "lucide-react";
import { useMemo } from "react";
import Metric from "../components/Metric";
import Panel from "../components/Panel";
import StatusBadge from "../components/StatusBadge";
import { firstName } from "../utils";

export default function CustomerOverview({ user, orders, tickets, onNavigate }) {
  const stats = useMemo(() => {
    const inTransit = orders.filter((order) =>
      ["PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY"].includes(order.status)
    ).length;
    const issues = tickets.filter((ticket) => ticket.status !== "closed").length;
    return { inTransit, issues, openTickets: issues };
  }, [orders, tickets]);

  return (
    <div className="page-stack">
      <section className="welcome-band">
        <div>
          <p className="eyebrow">Good morning, {firstName(user.name)}</p>
          <h2>Here&apos;s what&apos;s happening with your shipments.</h2>
        </div>
        <button className="secondary-button" onClick={() => onNavigate("orders")}>
          View orders
        </button>
      </section>

      <section className="status-grid">
        <Metric icon={PackageCheck} label="Orders" value={orders.length} />
        <Metric icon={Truck} label="In transit" value={stats.inTransit} />
        <Metric icon={CircleAlert} label="Issues" value={stats.issues} />
        <Metric icon={TicketCheck} label="Open tickets" value={stats.openTickets} />
      </section>

      <section className="split-grid">
        <Panel title="Recent Shipments" action="All orders" onAction={() => onNavigate("orders")}>
          <div className="compact-list">
            {orders.slice(0, 5).map((order) => (
              <button className="list-row" key={order.order_id} onClick={() => onNavigate("orders")}>
                <strong>{order.order_id}</strong>
                <span>{order.carrier}</span>
                <StatusBadge value={order.status} />
              </button>
            ))}
          </div>
        </Panel>
        <Panel title="Recent Tickets" action="All tickets" onAction={() => onNavigate("tickets")}>
          <div className="compact-list">
            {tickets.slice(0, 5).map((ticket) => (
              <button className="list-row" key={ticket.ticket_id} onClick={() => onNavigate("tickets")}>
                <strong>{ticket.ticket_id}</strong>
                <span>{ticket.subject}</span>
                <StatusBadge value={ticket.priority} />
              </button>
            ))}
          </div>
        </Panel>
      </section>
    </div>
  );
}
