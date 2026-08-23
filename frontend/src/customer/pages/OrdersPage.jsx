import { ArrowLeft } from "lucide-react";
import { useMemo, useState } from "react";
import Panel from "../components/Panel";
import StatusBadge from "../components/StatusBadge";
import { formatDateTime, formatMoney, formatOptionLabel, sortOrders, uniqueValues, withinDateRange } from "../utils";

export function OrdersPage({ orders, onSelect }) {
  const [query, setQuery] = useState("");
  const [carrier, setCarrier] = useState("ALL");
  const [status, setStatus] = useState("ALL");
  const [origin, setOrigin] = useState("ALL");
  const [destination, setDestination] = useState("ALL");
  const [dateRange, setDateRange] = useState("ALL");
  const carrierOptions = useMemo(() => ["ALL", ...uniqueValues(orders.map((order) => order.carrier))], [orders]);
  const statusOptions = useMemo(() => ["ALL", ...uniqueValues(orders.map((order) => order.status))], [orders]);
  const originOptions = useMemo(() => ["ALL", ...uniqueValues(orders.map((order) => order.origin))], [orders]);
  const destinationOptions = useMemo(() => ["ALL", ...uniqueValues(orders.map((order) => order.destination))], [orders]);
  const filteredOrders = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return sortOrders(orders)
      .filter((order) => carrier === "ALL" || order.carrier === carrier)
      .filter((order) => status === "ALL" || order.status === status)
      .filter((order) => origin === "ALL" || order.origin === origin)
      .filter((order) => destination === "ALL" || order.destination === destination)
      .filter((order) => withinDateRange(order.booked_at, dateRange))
      .filter((order) => {
        if (!needle) return true;
        return [order.order_id, order.carrier, order.status, order.origin, order.destination, order.current_location]
          .filter(Boolean)
          .join(" ")
          .toLowerCase()
          .includes(needle);
      });
  }, [orders, query, carrier, status, origin, destination, dateRange]);

  return (
    <div className="page-stack">
      <section className="toolbar-row">
        <div>
          <p className="eyebrow">Shipments</p>
          <h2>All Orders</h2>
        </div>
        <span className="count-pill">{filteredOrders.length} visible</span>
      </section>
      <section className="customer-filter-bar">
        <label>
          Search
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Order, carrier, city, status" />
        </label>
        <FilterSelect label="Carrier" value={carrier} onChange={setCarrier} options={carrierOptions} />
        <FilterSelect label="Status" value={status} onChange={setStatus} options={statusOptions} />
        <FilterSelect label="Origin" value={origin} onChange={setOrigin} options={originOptions} />
        <FilterSelect label="Destination" value={destination} onChange={setDestination} options={destinationOptions} />
        <FilterSelect label="Booked" value={dateRange} onChange={setDateRange} options={["ALL", "TODAY", "LAST_7_DAYS", "LAST_30_DAYS"]} />
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
              {filteredOrders.map((order) => (
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

function FilterSelect({ label, value, onChange, options }) {
  return (
    <label>
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option} value={option}>
            {formatOptionLabel(option)}
          </option>
        ))}
      </select>
    </label>
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
