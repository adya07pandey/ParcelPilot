import { ArrowLeft, Plus, Send } from "lucide-react";
import { useMemo, useState } from "react";
import { apiFetch } from "../../api/client";
import Panel from "../components/Panel";
import StatusBadge from "../components/StatusBadge";
import { ticketCategoryOptions } from "../constants";
import { cleanLabel, formatDateTime, formatOptionLabel, sortTickets, uniqueValues, withinDateRange } from "../utils";

export function TicketsPage({ tickets, onCreated, onSelect }) {
  const [showForm, setShowForm] = useState(false);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("ALL");
  const [subcategory, setSubcategory] = useState("ALL");
  const [status, setStatus] = useState("ALL");
  const [priority, setPriority] = useState("ALL");
  const [dateRange, setDateRange] = useState("ALL");
  const categoryOptions = useMemo(() => ["ALL", ...uniqueValues(tickets.map((ticket) => ticket.category))], [tickets]);
  const subcategoryOptions = useMemo(() => ["ALL", ...uniqueValues(tickets.map((ticket) => ticket.subcategory))], [tickets]);
  const statusOptions = useMemo(() => ["ALL", ...uniqueValues(tickets.map((ticket) => ticket.status))], [tickets]);
  const priorityOptions = useMemo(() => ["ALL", ...uniqueValues(tickets.map((ticket) => ticket.priority))], [tickets]);
  const filteredTickets = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return sortTickets(tickets)
      .filter((ticket) => category === "ALL" || ticket.category === category)
      .filter((ticket) => subcategory === "ALL" || ticket.subcategory === subcategory)
      .filter((ticket) => status === "ALL" || ticket.status === status)
      .filter((ticket) => priority === "ALL" || ticket.priority === priority)
      .filter((ticket) => withinDateRange(ticket.last_customer_message_at || ticket.created_at, dateRange))
      .filter((ticket) => {
        if (!needle) return true;
        return [ticket.ticket_id, ticket.subject, ticket.description, ticket.category, ticket.subcategory, ticket.status, ticket.priority]
          .filter(Boolean)
          .join(" ")
          .toLowerCase()
          .includes(needle);
      });
  }, [tickets, query, category, subcategory, status, priority, dateRange]);

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

      <section className="customer-filter-bar">
        <label>
          Search
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ticket, subject, status, issue" />
        </label>
        <FilterSelect label="Category" value={category} onChange={setCategory} options={categoryOptions} />
        <FilterSelect label="Subcategory" value={subcategory} onChange={setSubcategory} options={subcategoryOptions} />
        <FilterSelect label="Status" value={status} onChange={setStatus} options={statusOptions} />
        <FilterSelect label="Priority" value={priority} onChange={setPriority} options={priorityOptions} />
        <FilterSelect label="Updated" value={dateRange} onChange={setDateRange} options={["ALL", "TODAY", "LAST_7_DAYS", "LAST_30_DAYS"]} />
      </section>

      <section className="ticket-list">
        {filteredTickets.map((ticket) => (
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
