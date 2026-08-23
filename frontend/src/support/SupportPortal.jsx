import {
  AlertTriangle,
  Bot,
  LogOut
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../auth/AuthProvider";
import Badge, { SlaBadge } from "./components/Badge";
import DataTable, { EmptyState } from "./components/DataTable";
import { SearchBox, SelectFilter } from "./components/Filters";
import PageHeader from "./components/PageHeader";
import Panel from "./components/Panel";
import { NAV_ITEMS, orderStatusRank, priorityRank, SUPPORT_BRAND_ICON } from "./constants";
import { supportApi } from "./supportApi";
import InvestigationPage from "./pages/InvestigationPage";
import {
  formatOptionLabel,
  formatDate,
  formatTime,
  readSupportView,
  SUPPORT_VIEW_KEY,
  uniqueValues,
  withinDateRange
} from "./utils";
import "./support.css";

const BrandIcon = SUPPORT_BRAND_ICON;

export default function SupportPortal() {
  const { user, logout } = useAuth();
  const initialView = useMemo(() => readSupportView(), []);
  const initialPage = NAV_ITEMS.some((item) => item.key === initialView.activePage) ? initialView.activePage : "dashboard";
  const [activePage, setActivePage] = useState(initialPage);
  const [overview, setOverview] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [orders, setOrders] = useState([]);
  const [policies, setPolicies] = useState(null);
  const [issues, setIssues] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [selectedTicketId, setSelectedTicketId] = useState(initialView.selectedTicketId || null);
  const [selectedCustomerId, setSelectedCustomerId] = useState(initialView.selectedCustomerId || null);
  const [selectedOrderId, setSelectedOrderId] = useState(initialView.selectedOrderId || null);
  const [investigationSeed, setInvestigationSeed] = useState(initialView.investigationSeed || null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadWorkspace();
  }, []);

  useEffect(() => {
    localStorage.setItem(
      SUPPORT_VIEW_KEY,
        JSON.stringify({
          activePage,
          selectedTicketId,
          selectedCustomerId,
          selectedOrderId,
          investigationSeed
        })
      );
  }, [activePage, selectedTicketId, selectedCustomerId, selectedOrderId, investigationSeed]);

  useEffect(() => {
    if (activePage === "ticket-detail" && selectedTicketId) {
      openTicket(selectedTicketId);
    } else if (activePage === "customer-detail" && selectedCustomerId) {
      openCustomer(selectedCustomerId);
    } else if (activePage === "order-detail" && selectedOrderId) {
      openOrder(selectedOrderId);
    }
  }, []);

  function navigate(page) {
    setActivePage(page);
    setSelectedTicket(null);
    setSelectedCustomer(null);
    setSelectedOrder(null);
    setSelectedTicketId(null);
    setSelectedCustomerId(null);
    setSelectedOrderId(null);
    setInvestigationSeed(null);
  }

  function openInvestigation(seed = null) {
    setInvestigationSeed(seed);
  }

  function closeInvestigation() {
    setInvestigationSeed(null);
  }

  async function loadWorkspace() {
    setLoading(true);
    setError("");
    try {
      const [overviewData, ticketsData, customersData, ordersData, policiesData, issuesData] = await Promise.all([
        supportApi.overview(),
        supportApi.tickets(),
        supportApi.customers(),
        supportApi.orders(),
        supportApi.policies(),
        supportApi.issues()
      ]);
      setOverview(overviewData);
      setTickets(ticketsData);
      setCustomers(customersData);
      setOrders(ordersData);
      setPolicies(policiesData);
      setIssues(issuesData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function openTicket(ticketId) {
    setActivePage("ticket-detail");
    setSelectedTicketId(ticketId);
    setSelectedCustomerId(null);
    setSelectedOrderId(null);
    setSelectedTicket(null);
    setError("");
    try {
      setSelectedTicket(await supportApi.ticket(ticketId));
    } catch (err) {
      setError(err.message);
    }
  }

  async function openCustomer(accountId) {
    setActivePage("customer-detail");
    setSelectedCustomerId(accountId);
    setSelectedTicketId(null);
    setSelectedOrderId(null);
    setSelectedCustomer(null);
    setError("");
    try {
      setSelectedCustomer(await supportApi.customer(accountId));
    } catch (err) {
      setError(err.message);
    }
  }

  async function openOrder(orderId) {
    setActivePage("order-detail");
    setSelectedOrderId(orderId);
    setSelectedTicketId(null);
    setSelectedCustomerId(null);
    setSelectedOrder(null);
    setError("");
    try {
      setSelectedOrder(await supportApi.order(orderId));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <main className="support-shell">
      <aside className="support-sidebar">
        <div className="support-brand">
          <BrandIcon size={24} />
          <div>
            <strong>ParcelPilot</strong>
            <span>Support</span>
          </div>
        </div>
        <nav className="support-nav">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.key}
                className={activeNavKey(activePage) === item.key ? "active" : ""}
                onClick={() => navigate(item.key)}
                title={item.label}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
        <div className="support-user">
          <strong>{user?.name}</strong>
          <span>{user?.role}</span>
          <button onClick={logout}>
            <LogOut size={16} />
            Sign out
          </button>
        </div>
      </aside>

      <section className="support-main">
        {error ? <div className="support-alert">{error}</div> : null}
        {loading ? (
          <div className="support-loading">Loading support workspace...</div>
        ) : (
          <>
            {activePage === "dashboard" ? <DashboardView overview={overview} tickets={tickets} openTicket={openTicket} openInvestigation={openInvestigation} /> : null}
            {activePage === "tickets" ? <TicketsView tickets={tickets} openTicket={openTicket} /> : null}
            {activePage === "ticket-detail" ? (
              <TicketDetail ticket={selectedTicket} openCustomer={openCustomer} openOrder={openOrder} openInvestigation={openInvestigation} />
            ) : null}
            {activePage === "customers" ? <CustomersView customers={customers} openCustomer={openCustomer} /> : null}
            {activePage === "customer-detail" ? (
              <CustomerDetail data={selectedCustomer} openTicket={openTicket} openOrder={openOrder} openInvestigation={openInvestigation} />
            ) : null}
            {activePage === "orders" ? <OrdersView orders={orders} openOrder={openOrder} openInvestigation={openInvestigation} /> : null}
            {activePage === "order-detail" ? (
              <OrderDetail order={selectedOrder} openTicket={openTicket} openCustomer={openCustomer} openInvestigation={openInvestigation} />
            ) : null}
            {activePage === "policies" ? <PoliciesView policies={policies} /> : null}
            {activePage === "issues" ? <IssuesView issues={issues} openTicket={openTicket} openInvestigation={openInvestigation} /> : null}
            {activePage === "ai-support" ? <InvestigationPage customers={customers} /> : null}
            {investigationSeed ? (
              <EmbeddedInvestigation customers={customers} seed={investigationSeed} onClose={closeInvestigation} />
            ) : null}
          </>
        )}
      </section>
    </main>
  );
}

function activeNavKey(activePage) {
  if (activePage === "ticket-detail") return "tickets";
  if (activePage === "customer-detail") return "customers";
  if (activePage === "order-detail") return "orders";
  return activePage;
}

function DashboardView({ overview, tickets, openTicket, openInvestigation }) {
  const kpis = overview?.kpis || {};
  const priorityCounts = useMemo(
    () =>
      tickets.reduce(
        (counts, ticket) => {
          counts[ticket.priority] = (counts[ticket.priority] || 0) + 1;
          return counts;
        },
        { HIGH: 0, MEDIUM: 0, LOW: 0 }
      ),
    [tickets]
  );
  return (
    <section>
      <PageHeader title="Dashboard" subtitle="What needs attention right now" />
      <div className="support-kpis">
        <Kpi label="Open Tickets" value={kpis.open_tickets} />
        <Kpi label="P1 / High" value={priorityCounts.HIGH} tone="danger" />
        <Kpi label="P2 / Medium" value={priorityCounts.MEDIUM} tone="warning" />
        <Kpi label="P3 / Low" value={priorityCounts.LOW} />
        <Kpi label="SLA At Risk" value={kpis.sla_at_risk} tone="warning" />
        <Kpi label="SLA Breached" value={kpis.sla_breached} tone="danger" />
      </div>
      <div className="support-grid two">
        <Panel title="Priority Queue">
          <TicketStack tickets={overview?.priority_queue || []} openTicket={openTicket} />
        </Panel>
        <Panel title="Recent AI Escalations">
          <TicketStack tickets={overview?.ai_escalations || []} openTicket={openTicket} compact />
        </Panel>
      </div>
      <Panel title="Detected Patterns">
        <IssueGrid issues={overview?.issues || []} />
      </Panel>
    </section>
  );
}

function TicketsView({ tickets, openTicket }) {
  const [query, setQuery] = useState("");
  const [priority, setPriority] = useState("ALL");
  const [status, setStatus] = useState("ALL");
  const [source, setSource] = useState("ALL");
  const [company, setCompany] = useState("ALL");
  const [category, setCategory] = useState("ALL");
  const [subcategory, setSubcategory] = useState("ALL");
  const [dateRange, setDateRange] = useState("ALL");
  const companyOptions = useMemo(() => ["ALL", ...uniqueValues(tickets.map((ticket) => ticket.account_name))], [tickets]);
  const categoryOptions = useMemo(() => ["ALL", ...uniqueValues(tickets.map((ticket) => ticket.category))], [tickets]);
  const subcategoryOptions = useMemo(() => ["ALL", ...uniqueValues(tickets.map((ticket) => ticket.subcategory))], [tickets]);
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return tickets
      .filter((ticket) => priority === "ALL" || ticket.priority === priority)
      .filter((ticket) => status === "ALL" || ticket.status === status)
      .filter((ticket) => source === "ALL" || ticket.source === source)
      .filter((ticket) => company === "ALL" || ticket.account_name === company)
      .filter((ticket) => category === "ALL" || ticket.category === category)
      .filter((ticket) => subcategory === "ALL" || ticket.subcategory === subcategory)
      .filter((ticket) => withinDateRange(ticket.created_at, dateRange))
      .filter((ticket) => {
        if (!needle) return true;
        return [
          ticket.ticket_id,
          ticket.subject,
          ticket.account_name,
          ticket.category,
          ticket.subcategory,
          ticket.linked_order_id,
          ticket.description,
          ticket.assigned_to
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase()
          .includes(needle);
      })
      .sort((a, b) => {
        const priorityDelta = (priorityRank[a.priority] ?? 9) - (priorityRank[b.priority] ?? 9);
        if (priorityDelta !== 0) return priorityDelta;
        return new Date(b.created_at || 0) - new Date(a.created_at || 0);
      });
  }, [tickets, query, priority, status, source, company, category, subcategory, dateRange]);

  return (
    <section>
      <PageHeader title="Tickets" subtitle="Main support queue" />
      <div className="support-toolbar">
        <SearchBox value={query} onChange={setQuery} placeholder="Search ticket, order, company, issue" />
        <SelectFilter label="Priority" value={priority} onChange={setPriority} options={["ALL", "HIGH", "MEDIUM", "LOW"]} />
        <SelectFilter label="Status" value={status} onChange={setStatus} options={["ALL", "OPEN", "IN_PROGRESS", "WAITING_FOR_CUSTOMER", "RESOLVED"]} />
        <SelectFilter label="Company" value={company} onChange={setCompany} options={companyOptions} />
        <SelectFilter label="Category" value={category} onChange={setCategory} options={categoryOptions} />
        <SelectFilter label="Subcategory" value={subcategory} onChange={setSubcategory} options={subcategoryOptions} />
        <SelectFilter label="Date" value={dateRange} onChange={setDateRange} options={["ALL", "TODAY", "LAST_7_DAYS", "LAST_30_DAYS"]} />
        <SelectFilter label="Source" value={source} onChange={setSource} options={["ALL", "AI Support", "Customer Portal", "Email", "Chat", "Internal"]} />
      </div>
      <DataTable
        columns={["Ticket", "Priority", "Subject", "Category", "Account", "Assignee", "Status", "SLA", "Created"]}
        rows={filtered.map((ticket) => ({
          key: ticket.ticket_id,
          onClick: () => openTicket(ticket.ticket_id),
          cells: [
            ticket.ticket_id,
            <Badge key="priority" value={ticket.priority} />,
            ticket.subject,
            `${formatOptionLabel(ticket.category || "OTHER")} / ${formatOptionLabel(ticket.subcategory || "OTHER")}`,
            ticket.account_name,
            ticket.assigned_to || "Unassigned",
            ticket.status,
            <SlaBadge key="sla" sla={ticket.sla} />,
            formatDate(ticket.created_at)
          ]
        }))}
      />
    </section>
  );
}

function TicketDetail({ ticket, openCustomer, openOrder, openInvestigation }) {
  if (!ticket) return <div className="support-loading">Loading ticket...</div>;
  return (
    <section>
      <PageHeader
        title={ticket.ticket_id}
        subtitle={ticket.subject}
        meta={`${ticket.account?.account_name || ticket.account_name || "Unknown company"} · ${ticket.account_id}`}
      />
      <div className="support-detail-grid">
        <Panel title="Ticket">
          <div className="support-fields">
            <Field label="Company" value={ticket.account?.account_name || ticket.account_name} />
            <Field label="Category" value={formatOptionLabel(ticket.category || "OTHER")} />
            <Field label="Subcategory" value={formatOptionLabel(ticket.subcategory || "OTHER")} />
            <Field label="Priority" value={<Badge value={ticket.priority} />} />
            <Field label="Status" value={ticket.status} />
            <Field label="Source" value={ticket.source} />
            <Field label="Assignee" value={ticket.assigned_to || "Unassigned"} />
            <Field label="Linked order" value={ticket.linked_order_id || "None detected"} />
          </div>
          <div className="support-actions">
            <button>Assign to me</button>
            <button>Mark in progress</button>
            <button>Waiting for company</button>
          </div>
        </Panel>
        <Panel title="Company">
          {ticket.account ? (
            <button className="support-link-card" onClick={() => openCustomer(ticket.account.account_id)}>
              <strong>{ticket.account.account_name}</strong>
              <span>{ticket.account.plan} · {ticket.account.account_id}</span>
              <span>CSM: {ticket.account.csm || "Not assigned"}</span>
            </button>
          ) : (
            <EmptyState text="No company context found." />
          )}
        </Panel>
        <Panel title="Issue">
          <p className="support-description">{ticket.description}</p>
        </Panel>
        <Panel title="SLA">
          <div className="support-fields">
            <Field label="Target" value={ticket.sla?.target} />
            <Field label="Deadline" value={formatDate(ticket.sla?.deadline)} />
            <Field label="Current" value={<SlaBadge sla={ticket.sla} />} />
          </div>
        </Panel>
        <Panel title="AI Investigation">
          <button
            className="primary-action"
            onClick={() => openInvestigation({
              account_id: ticket.account_id,
              question: ticket.description || ticket.subject || `Investigate ${ticket.ticket_id}`
            })}
          >
            <Bot size={18} />
            Investigate
          </button>
          <p className="muted">Opens the support AI with this company account and issue already in context.</p>
        </Panel>
        <Panel title="Linked Order">
          {ticket.linked_order ? (
            <button className="support-link-card" onClick={() => openOrder(ticket.linked_order.order_id)}>
              <strong>{ticket.linked_order.order_id}</strong>
              <span>{ticket.linked_order.carrier} · {ticket.linked_order.status}</span>
              <span>{ticket.linked_order.origin} to {ticket.linked_order.destination}</span>
            </button>
          ) : (
            <EmptyState text="No linked order detected from this ticket." />
          )}
        </Panel>
      </div>
      <div className="support-grid two">
        <Panel title="Conversation">
          <Conversation messages={ticket.conversation || []} />
        </Panel>
        <Panel title="Timeline">
          <Timeline events={ticket.events || []} />
        </Panel>
      </div>
    </section>
  );
}

function CustomersView({ customers, openCustomer }) {
  const [query, setQuery] = useState("");
  const filtered = customers.filter((customer) =>
    [customer.account_id, customer.account_name, customer.plan, customer.csm]
      .filter(Boolean)
      .join(" ")
      .toLowerCase()
      .includes(query.toLowerCase())
  );
  return (
    <section>
      <PageHeader title="Companies" subtitle="Company account directory" />
      <div className="support-toolbar">
        <SearchBox value={query} onChange={setQuery} placeholder="Search Northstar, LumenWorks, Beacon" />
      </div>
      <DataTable
        columns={["Account ID", "Company", "Plan", "Status", "CSM", "Premium Support", "Open Tickets"]}
        rows={filtered.map((customer) => ({
          key: customer.account_id,
          onClick: () => openCustomer(customer.account_id),
          cells: [
            customer.account_id,
            customer.account_name,
            customer.plan,
            customer.status,
            customer.csm || "Unassigned",
            customer.premium_support ? "Yes" : "No",
            customer.open_tickets
          ]
        }))}
      />
    </section>
  );
}

function CustomerDetail({ data, openTicket, openOrder, openInvestigation }) {
  if (!data) return <div className="support-loading">Loading company...</div>;
  const { account, orders, tickets, agreement } = data;
  return (
    <section>
      <PageHeader title={account.account_name} subtitle="Company 360" />
      <div className="support-detail-grid">
        <Panel title="Overview">
          <div className="support-fields">
            <Field label="Account" value={account.account_id} />
            <Field label="Plan" value={account.plan} />
            <Field label="Status" value={account.status} />
            <Field label="CSM" value={account.csm || "Unassigned"} />
            <Field label="Premium Support" value={account.premium_support ? "Yes" : "No"} />
          </div>
        </Panel>
        <Panel title="Policies & Agreement">
          <div className="support-fields">
            <Field label="Agreement" value={agreement.document || "No signed file"} />
            <Field label="Support" value={agreement.terms.support} />
            <Field label="Cancellation" value={agreement.terms.cancellation} />
            <Field label="Service credits" value={agreement.terms.service_credits} />
          </div>
        </Panel>
        <Panel title="AI Investigation">
          <button
            className="primary-action"
            onClick={() => openInvestigation({
              account_id: account.account_id,
              question: `Investigate account ${account.account_name} and summarize current support risk.`
            })}
          >
            <Bot size={18} />
            Investigate Account
          </button>
        </Panel>
      </div>
      <div className="support-grid two">
        <Panel title="Orders">
          <MiniList
            items={orders}
            empty="No orders."
            render={(order) => (
              <button key={order.order_id} className="mini-row" onClick={() => openOrder(order.order_id)}>
                <strong>{order.order_id}</strong>
                <span>{order.carrier}</span>
                <Badge value={order.status} />
              </button>
            )}
          />
        </Panel>
        <Panel title="Tickets">
          <MiniList
            items={tickets}
            empty="No tickets."
            render={(ticket) => (
              <button key={ticket.ticket_id} className="mini-row" onClick={() => openTicket(ticket.ticket_id)}>
                <strong>{ticket.ticket_id}</strong>
                <span>{ticket.subject}</span>
                <Badge value={ticket.priority} />
              </button>
            )}
          />
        </Panel>
      </div>
    </section>
  );
}

function OrdersView({ orders, openOrder, openInvestigation }) {
  const [query, setQuery] = useState("");
  const [company, setCompany] = useState("ALL");
  const [carrier, setCarrier] = useState("ALL");
  const [status, setStatus] = useState("ALL");
  const [origin, setOrigin] = useState("ALL");
  const [destination, setDestination] = useState("ALL");
  const [dateRange, setDateRange] = useState("ALL");
  const companyOptions = useMemo(() => ["ALL", ...uniqueValues(orders.map((order) => order.account_name))], [orders]);
  const carrierOptions = useMemo(() => ["ALL", ...uniqueValues(orders.map((order) => order.carrier))], [orders]);
  const statusOptions = useMemo(() => ["ALL", ...uniqueValues(orders.map((order) => order.status))], [orders]);
  const originOptions = useMemo(() => ["ALL", ...uniqueValues(orders.map((order) => order.origin))], [orders]);
  const destinationOptions = useMemo(() => ["ALL", ...uniqueValues(orders.map((order) => order.destination))], [orders]);
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return orders
      .filter((order) => company === "ALL" || order.account_name === company)
      .filter((order) => carrier === "ALL" || order.carrier === carrier)
      .filter((order) => status === "ALL" || order.status === status)
      .filter((order) => origin === "ALL" || order.origin === origin)
      .filter((order) => destination === "ALL" || order.destination === destination)
      .filter((order) => withinDateRange(order.booked_at, dateRange))
      .filter((order) => {
        if (!needle) return true;
        return [order.order_id, order.carrier, order.account_name, order.status, order.origin, order.destination]
          .filter(Boolean)
          .join(" ")
          .toLowerCase()
          .includes(needle);
      })
      .sort((a, b) => {
        const companyDelta = String(a.account_name || "").localeCompare(String(b.account_name || ""));
        if (companyDelta !== 0) return companyDelta;
        const statusDelta = (orderStatusRank[a.status] ?? 9) - (orderStatusRank[b.status] ?? 9);
        if (statusDelta !== 0) return statusDelta;
        return new Date(b.booked_at || 0) - new Date(a.booked_at || 0);
      });
  }, [orders, query, company, carrier, status, origin, destination, dateRange]);
  return (
    <section>
      <PageHeader title="Orders" subtitle="Shipment investigation" />
      <div className="support-toolbar">
        <SearchBox value={query} onChange={setQuery} placeholder="Search order ID, carrier, account, status" />
        <SelectFilter label="Company" value={company} onChange={setCompany} options={companyOptions} />
        <SelectFilter label="Carrier" value={carrier} onChange={setCarrier} options={carrierOptions} />
        <SelectFilter label="Status" value={status} onChange={setStatus} options={statusOptions} />
        <SelectFilter label="Origin" value={origin} onChange={setOrigin} options={originOptions} />
        <SelectFilter label="Destination" value={destination} onChange={setDestination} options={destinationOptions} />
        <SelectFilter label="Booked Date" value={dateRange} onChange={setDateRange} options={["ALL", "TODAY", "LAST_7_DAYS", "LAST_30_DAYS"]} />
      </div>
      <DataTable
        columns={["Order", "Account", "Carrier", "Status", "Origin", "Destination", "Booked"]}
        rows={filtered.map((order) => ({
          key: order.order_id,
          onClick: () => openOrder(order.order_id),
          cells: [
            order.order_id,
            order.account_name,
            order.carrier,
            <Badge key="status" value={order.status} />,
            order.origin,
            order.destination,
            formatDate(order.booked_at)
          ]
        }))}
      />
      <Panel title="AI Investigation">
        <button
          className="primary-action"
          onClick={() => openInvestigation({
            question: "Investigate the current shipment risk and explain any delay."
          })}
        >
          <Bot size={18} />
          Investigate Shipments
        </button>
      </Panel>
    </section>
  );
}

function OrderDetail({ order, openTicket, openCustomer, openInvestigation }) {
  if (!order) return <div className="support-loading">Loading order...</div>;
  return (
    <section>
      <PageHeader
        title={order.order_id}
        subtitle={`${order.carrier} · ${order.status}`}
        meta={`${order.account?.account_name || order.account_name || "Unknown company"} · ${order.account_id}`}
      />
      <div className="support-detail-grid">
        <Panel title="Shipment">
          <div className="support-fields">
            <Field label="Company" value={order.account?.account_name || order.account_name} />
            <Field label="Account ID" value={order.account?.account_id || order.account_id} />
            <Field label="Carrier" value={order.carrier} />
            <Field label="Status" value={<Badge value={order.status} />} />
            <Field label="Booked" value={formatDate(order.booked_at)} />
            <Field label="Pickup window" value={`${formatTime(order.pickup_window_start)} - ${formatTime(order.pickup_window_end)}`} />
            <Field label="Pickup" value={formatDate(order.pickup_actual_at) || "Not confirmed"} />
            <Field label="Shipment fee" value={order.shipment_fee_inr ? `INR ${order.shipment_fee_inr}` : "Not set"} />
          </div>
          {order.account ? (
            <button className="primary-action" onClick={() => openCustomer(order.account.account_id)}>Open Company</button>
          ) : null}
        </Panel>
        <Panel title="Related Tickets">
          <MiniList
            items={order.related_tickets || []}
            empty="No related tickets detected."
            render={(ticket) => (
              <button key={ticket.ticket_id} className="mini-row" onClick={() => openTicket(ticket.ticket_id)}>
                <strong>{ticket.ticket_id}</strong>
                <span>{ticket.subject}</span>
                <Badge value={ticket.priority} />
              </button>
            )}
          />
        </Panel>
        <Panel title="Applicable Policies">
          <MiniList
            items={order.applicable_policies || []}
            empty="No policies."
            render={(policy) => (
              <div key={policy.document_id || policy.account_id} className="policy-row">
                <strong>{policy.name || policy.account_name}</strong>
                <span>{policy.status || policy.plan}</span>
              </div>
            )}
          />
        </Panel>
        <Panel title="AI Investigation">
          <button
            className="primary-action"
            onClick={() => openInvestigation({
              account_id: order.account_id,
              question: `Investigate order ${order.order_id} and explain the current shipment state.`
            })}
          >
            <Bot size={18} />
            Investigate Order
          </button>
        </Panel>
      </div>
      <Panel title="Timeline">
        <Timeline events={order.events || []} />
      </Panel>
    </section>
  );
}

function PoliciesView({ policies }) {
  const [query, setQuery] = useState("");
  if (!policies) return <div className="support-loading">Loading policies...</div>;
  const needle = query.trim().toLowerCase();
  const generalPolicies = policies.general_policies.filter((policy) =>
    [policy.name, policy.type, policy.status, policy.effective, policy.summary]
      .filter(Boolean)
      .join(" ")
      .toLowerCase()
      .includes(needle)
  );
  const agreements = policies.customer_agreements.filter((agreement) =>
    [
      agreement.account_id,
      agreement.account_name,
      agreement.status,
      agreement.document,
      agreement.plan,
      agreement.terms?.support,
      agreement.terms?.cancellation,
      agreement.terms?.service_credits,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase()
      .includes(needle)
  );
  return (
    <section>
      <PageHeader title="Policies & Agreements" subtitle="Authoritative rules and company overrides" />
      <div className="support-toolbar">
        <SearchBox value={query} onChange={setQuery} placeholder="Search policy, agreement, company, effective date" />
      </div>
      <div className="support-grid two">
        <Panel title="General Policies">
          <MiniList
            items={generalPolicies}
            empty="No matching policies."
            render={(policy) => (
              <div key={policy.document_id} className="policy-row">
                <strong>{policy.name}</strong>
                <span>{policy.status} · Effective {policy.effective}</span>
                <small>{policy.summary}</small>
              </div>
            )}
          />
        </Panel>
        <Panel title="Company Agreements">
          <MiniList
            items={agreements}
            empty="No matching agreements."
            render={(agreement) => (
              <div key={agreement.account_id} className="policy-row">
                <strong>{agreement.account_name}</strong>
                <span>{agreement.status} · {agreement.document || "No file"}</span>
                <small>Support: {agreement.terms.support}</small>
                <small>Cancellation: {agreement.terms.cancellation}</small>
                <small>Service credits: {agreement.terms.service_credits}</small>
              </div>
            )}
          />
        </Panel>
      </div>
      <Panel title="Policy Conflict / Override">
        <div className="override-box">
          <div>
            <strong>General policy</strong>
            <span>{policies.override_example.general_policy}</span>
          </div>
          <div>
            <strong>Company agreement</strong>
            <span>{policies.override_example.customer_agreement}</span>
          </div>
          <div className="override-result">
            <AlertTriangle size={18} />
            <span>{policies.override_example.result}</span>
          </div>
        </div>
      </Panel>
    </section>
  );
}

function EmbeddedInvestigation({ customers, seed, onClose }) {
  return (
    <section className="embedded-investigation">
      <div className="embedded-investigation-header">
        <div>
          <p className="muted">Embedded workspace</p>
          <h2>AI Investigation</h2>
        </div>
        <button className="support-close-button" onClick={onClose}>Close</button>
      </div>
      <InvestigationPage customers={customers} seed={seed} embedded />
    </section>
  );
}

function IssuesView({ issues, openTicket, openInvestigation }) {
  return (
    <section>
      <PageHeader title="Issues & Incidents" subtitle="Detected ticket patterns" />
      <Panel title="AI Investigation">
        <button
          className="primary-action"
          onClick={() => openInvestigation({
            question: "Investigate the recurring incident pattern and summarize root cause signals."
          })}
        >
          <Bot size={18} />
          Start Proactive Investigation
        </button>
      </Panel>
      <IssueGrid issues={issues} openTicket={openTicket} />
    </section>
  );
}

function Kpi({ label, value = 0, tone = "" }) {
  return (
    <div className={`support-kpi ${tone}`}>
      <span>{label}</span>
      <strong>{value ?? 0}</strong>
    </div>
  );
}

function TicketStack({ tickets, openTicket, compact = false }) {
  if (!tickets.length) return <EmptyState text="Nothing waiting here." />;
  return (
    <div className={compact ? "ticket-stack compact" : "ticket-stack"}>
      {tickets.map((ticket) => (
        <button key={ticket.ticket_id} onClick={() => openTicket(ticket.ticket_id)} className="ticket-stack-row">
          <div>
            <Badge value={ticket.priority} />
            <strong>{ticket.subject}</strong>
          </div>
          <span>{ticket.account_name}</span>
          <small>{ticket.sla?.state === "BREACHED" ? "SLA breached" : `${ticket.sla?.remaining_minutes ?? 0} min remaining`}</small>
        </button>
      ))}
    </div>
  );
}

function IssueGrid({ issues, openTicket }) {
  if (!issues.length) return <EmptyState text="No recurring patterns found." />;
  return (
    <div className="issue-grid">
      {issues.map((issue) => (
        <article key={issue.name} className="issue-card">
          <span className={issue.severity === "Potential incident" ? "issue-severity danger" : "issue-severity"}>
            {issue.severity}
          </span>
          <h3>{issue.name}</h3>
          <p>{issue.ticket_count} tickets · {issue.customer_count} companies</p>
          <small>Latest: {formatDate(issue.latest_at)}</small>
          {openTicket && issue.ticket_ids?.length ? (
            <button onClick={() => openTicket(issue.ticket_ids[0])}>View Related Tickets</button>
          ) : null}
        </article>
      ))}
    </div>
  );
}

function Field({ label, value }) {
  return (
    <div className="support-field">
      <span>{label}</span>
      <strong>{value || "Not available"}</strong>
    </div>
  );
}

function Timeline({ events }) {
  if (!events.length) return <EmptyState text="No timeline events." />;
  return (
    <ol className="support-timeline">
      {events.map((event) => (
        <li key={event.ticket_event_id || event.event_id || `${event.event_time}-${event.description}`}>
          <span>{formatDate(event.event_time)}</span>
          <strong>{event.event_type}</strong>
          <p>{event.description}</p>
        </li>
      ))}
    </ol>
  );
}

function Conversation({ messages }) {
  if (!messages.length) return <EmptyState text="No AI conversation linked yet." />;
  return (
    <div className="support-conversation">
      {messages.map((message, index) => (
        <article key={`${message.created_at}-${index}`} className={message.role}>
          <span>{message.role}</span>
          <p>{message.content}</p>
        </article>
      ))}
    </div>
  );
}

function MiniList({ items, render, empty = "No data." }) {
  if (!items?.length) return <EmptyState text={empty} />;
  return <div className="mini-list">{items.map(render)}</div>;
}
