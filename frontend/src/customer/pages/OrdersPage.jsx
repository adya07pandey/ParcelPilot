import { ArrowLeft } from "lucide-react";
import Panel from "../components/Panel";
import StatusBadge from "../components/StatusBadge";
import { formatDateTime, formatMoney } from "../utils";

export function OrdersPage({ orders, onSelect }) {
  return (
    <div className="page-stack">
      <section className="toolbar-row">
        <div>
          <p className="eyebrow">Shipments</p>
          <h2>All Orders</h2>
        </div>
        <span className="count-pill">{orders.length} visible</span>
      </section>
      <section className="table-wrap">
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Order</th>
                <th>Carrier</th>
                <th>Status</th>
                <th>Booked</th>
                <th>Pickup</th>
                <th>Fee</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <tr className="clickable-row" key={order.order_id} onClick={() => onSelect(order.order_id)}>
                  <td>{order.order_id}</td>
                  <td>{order.carrier}</td>
                  <td>
                    <StatusBadge value={order.status} />
                  </td>
                  <td>{formatDateTime(order.booked_at)}</td>
                  <td>{formatDateTime(order.pickup_window_start)}</td>
                  <td>{formatMoney(order.shipment_fee_inr)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export function OrderDetail({ order, onBack }) {
  const events = order.events || [];
  return (
    <div className="page-stack">
      <button className="back-button" onClick={onBack}>
        <ArrowLeft size={18} />
        Back to Orders
      </button>

      <section className="detail-header">
        <div>
          <p className="eyebrow">{order.carrier}</p>
          <h2>{order.order_id}</h2>
        </div>
        <StatusBadge value={order.status} />
      </section>

      <section className="detail-grid">
        <Panel title="Shipment Timeline">
          <div className="timeline">
            {events.map((event) => (
              <div className="timeline-item" key={event.event_id}>
                <span className="timeline-dot" />
                <div>
                  <strong>{String(event.event_type || "Unknown").replaceAll("_", " ")}</strong>
                  <p>{formatDateTime(event.event_time)}</p>
                  <span>{event.description}</span>
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Shipment Details">
          <dl className="details-list">
            <dt>Origin</dt>
            <dd>{order.origin || "Not provided"}</dd>
            <dt>Destination</dt>
            <dd>{order.destination || "Not provided"}</dd>
            <dt>Carrier</dt>
            <dd>{order.carrier}</dd>
            <dt>Shipment Fee</dt>
            <dd>{formatMoney(order.shipment_fee_inr)}</dd>
            <dt>Expected Delivery</dt>
            <dd>{formatDateTime(order.estimated_delivery_at)}</dd>
            <dt>Current Location</dt>
            <dd>{order.current_location || "Not available"}</dd>
          </dl>
          <button className="secondary-button full-width" disabled title="AI Support will be added next">
            Ask ParcelPilot AI
          </button>
        </Panel>
      </section>
    </div>
  );
}
