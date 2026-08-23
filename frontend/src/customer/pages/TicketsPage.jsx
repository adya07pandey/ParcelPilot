import { ArrowLeft, Plus, Send } from "lucide-react";
import { useMemo, useState } from "react";
import { apiFetch } from "../../api/client";
import Panel from "../components/Panel";
import StatusBadge from "../components/StatusBadge";
import { ticketCategoryOptions } from "../constants";
import { cleanLabel, formatDateTime, sortTickets } from "../utils";

export function TicketsPage({ tickets, onCreated, onSelect }) {
  const [showForm, setShowForm] = useState(false);
  const sortedTickets = useMemo(() => sortTickets(tickets), [tickets]);

  return (
    <div className="page-stack">
      <section className="toolbar-row">
        <div>
          <p className="eyebrow">Support</p>
          <h2>My Tickets</h2>
        </div>
        <button className="icon-button" onClick={() => setShowForm((value) => !value)}>
          <Plus size={18} />
          New ticket
        </button>
      </section>

      {showForm ? (
        <CreateTicketForm
          onCreated={() => {
            setShowForm(false);
            onCreated();
          }}
        />
      ) : null}

      <section className="ticket-list">
        {sortedTickets.map((ticket) => (
          <button className="ticket-card" key={ticket.ticket_id} onClick={() => onSelect(ticket.ticket_id)}>
            <div>
              <strong>{ticket.ticket_id}</strong>
              <h3>{ticket.subject}</h3>
              <p>{ticket.description}</p>
            </div>
            <div className="ticket-meta">
              <StatusBadge value={ticket.category || "OTHER"} />
              <StatusBadge value={ticket.subcategory || "OTHER"} />
              <StatusBadge value={ticket.status} />
              <StatusBadge value={ticket.priority} />
              <span>Last updated {formatDateTime(ticket.last_customer_message_at || ticket.created_at)}</span>
            </div>
          </button>
        ))}
      </section>
    </div>
  );
}

function CreateTicketForm({ onCreated }) {
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("SHIPMENT");
  const [subcategory, setSubcategory] = useState("SHIPMENT_LOCATION");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const selectedCategory = ticketCategoryOptions.find((item) => item.value === category) || ticketCategoryOptions[0];

  function handleCategoryChange(value) {
    const nextCategory = ticketCategoryOptions.find((item) => item.value === value) || ticketCategoryOptions[0];
    setCategory(nextCategory.value);
    setSubcategory(nextCategory.subcategories[0][0]);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await apiFetch("/tickets", {
        method: "POST",
        body: JSON.stringify({ subject, description, category, subcategory })
      });
      setSubject("");
      setDescription("");
      setCategory("SHIPMENT");
      setSubcategory("SHIPMENT_LOCATION");
      onCreated();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="form-panel" onSubmit={handleSubmit}>
      <label>
        Subject
        <input value={subject} onChange={(event) => setSubject(event.target.value)} />
      </label>
      <label>
        Category
        <select value={category} onChange={(event) => handleCategoryChange(event.target.value)}>
          {ticketCategoryOptions.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
      </label>
      <label>
        Subcategory
        <select value={subcategory} onChange={(event) => setSubcategory(event.target.value)}>
          {selectedCategory.subcategories.map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <label>
        Description
        <textarea value={description} onChange={(event) => setDescription(event.target.value)} />
      </label>
      {error ? <p className="error-text">{error}</p> : null}
      <button type="submit" disabled={saving}>
        {saving ? "Creating..." : "Create ticket"}
      </button>
    </form>
  );
}

export function TicketDetail({ ticket, onBack, onMessageSent }) {
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function sendMessage(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await apiFetch(`/tickets/${ticket.ticket_id}/messages`, {
        method: "POST",
        body: JSON.stringify({ message })
      });
      setMessage("");
      await onMessageSent();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="page-stack">
      <button className="back-button" onClick={onBack}>
        <ArrowLeft size={18} />
        Back to Tickets
      </button>

      <section className="detail-header">
        <div>
          <p className="eyebrow">{ticket.category}</p>
          <h2>{ticket.subject}</h2>
          <span>{cleanLabel(ticket.subcategory || "OTHER")}</span>
        </div>
        <StatusBadge value={ticket.priority} />
      </section>

      <section className="detail-grid">
        <Panel title="Ticket Activity">
          <div className="timeline">
            {(ticket.events || []).map((event) => (
              <div className="timeline-item" key={event.ticket_event_id}>
                <span className="timeline-dot" />
                <div>
                  <strong>{cleanLabel(event.event_type)}</strong>
                  <p>{formatDateTime(event.event_time)}</p>
                  <span>{event.description}</span>
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Add Message">
          <form className="message-form" onSubmit={sendMessage}>
            <textarea value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Add more context..." />
            {error ? <p className="error-text">{error}</p> : null}
            <button className="icon-button" disabled={saving || !message.trim()}>
              <Send size={18} />
              {saving ? "Sending..." : "Send message"}
            </button>
          </form>
        </Panel>
      </section>
    </div>
  );
}
