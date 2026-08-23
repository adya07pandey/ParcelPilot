import {
  ArrowLeft,
  Bell,
  HelpCircle,
  LogOut,
  PackageCheck,
  Plus,
  Send,
  TicketCheck,
  Truck,
  User
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../api/client";
import { useAuth } from "../auth/AuthProvider";
import StatusBadge from "../customer/components/StatusBadge";
import CustomerOverview from "../customer/pages/CustomerOverview";
import { OrderDetail, OrdersPage } from "../customer/pages/OrdersPage";
import { TicketDetail, TicketsPage } from "../customer/pages/TicketsPage";
import {
  navItems,
  supportCategories
} from "../customer/constants";
import {
  cleanLabel,
  CUSTOMER_VIEW_KEY,
  formatSource,
  readCustomerView,
  sortOrders,
  sortTickets
} from "../customer/utils";

export default function Dashboard() {
  const { user, logout } = useAuth();
  const initialView = useMemo(() => readCustomerView(), []);
  const [activePage, setActivePage] = useState(initialView.activePage || "dashboard");
  const [orders, setOrders] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [selectedOrderId, setSelectedOrderId] = useState(initialView.selectedOrderId || null);
  const [selectedTicketId, setSelectedTicketId] = useState(initialView.selectedTicketId || null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function loadData() {
    setError("");
    setLoading(true);
    try {
      const [ordersPayload, ticketsPayload] = await Promise.all([
        apiFetch("/orders"),
        apiFetch("/tickets")
      ]);
      setOrders(sortOrders(ordersPayload));
      setTickets(sortTickets(ticketsPayload));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    localStorage.setItem(
      CUSTOMER_VIEW_KEY,
      JSON.stringify({
        activePage,
        selectedOrderId,
        selectedTicketId
      })
    );
  }, [activePage, selectedOrderId, selectedTicketId]);

  const selectedOrder = orders.find((order) => order.order_id === selectedOrderId);
  const selectedTicket = tickets.find((ticket) => ticket.ticket_id === selectedTicketId);

  function goTo(page) {
    setActivePage(page);
    setSelectedOrderId(null);
    setSelectedTicketId(null);
  }

  return (
    <main className="customer-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <Truck size={24} />
          <span>ParcelPilot</span>
        </div>
        <nav className="sidebar-nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                className={activePage === item.id ? "nav-item active" : "nav-item"}
                disabled={item.disabled}
                key={item.id}
                onClick={() => !item.disabled && goTo(item.id)}
                title={item.disabled ? "Coming next" : item.label}
              >
                <Icon size={18} />
                {item.label}
              </button>
            );
          })}
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Customer Portal</p>
            <h1>{pageTitle(activePage, selectedOrder, selectedTicket)}</h1>
          </div>
          <div className="topbar-actions">
            <button className="icon-only" title="Notifications">
              <Bell size={18} />
            </button>
            <div className="profile-pill">
              <User size={17} />
              <span>
                <strong>{user.name}</strong>
                <small>{user.company || user.account_id || "Account"}</small>
              </span>
            </div>
            <button className="icon-button" onClick={logout} title="Sign out">
              <LogOut size={18} />
              Sign out
            </button>
          </div>
        </header>

        {error ? <p className="error-text">{error}</p> : null}
        {loading ? <div className="empty-state">Loading your ParcelPilot workspace...</div> : null}

        {!loading && activePage === "dashboard" ? (
          <CustomerOverview user={user} orders={orders} tickets={tickets} onNavigate={goTo} />
        ) : null}

        {!loading && activePage === "orders" && !selectedOrder ? (
          <OrdersPage orders={orders} onSelect={setSelectedOrderId} />
        ) : null}
        {!loading && activePage === "orders" && selectedOrder ? (
          <OrderDetail order={selectedOrder} onBack={() => setSelectedOrderId(null)} />
        ) : null}

        {!loading && activePage === "tickets" && !selectedTicket ? (
          <TicketsPage tickets={tickets} onCreated={loadData} onSelect={setSelectedTicketId} />
        ) : null}
        {!loading && activePage === "tickets" && selectedTicket ? (
          <TicketDetail
            ticket={selectedTicket}
            onBack={() => setSelectedTicketId(null)}
            onMessageSent={loadData}
          />
        ) : null}

        {!loading && activePage === "ai" ? <AiSupportPage /> : null}
      </section>
    </main>
  );
}

function pageTitle(activePage, selectedOrder, selectedTicket) {
  if (selectedOrder) return selectedOrder.order_id;
  if (selectedTicket) return selectedTicket.ticket_id;
  if (activePage === "orders") return "Orders";
  if (activePage === "tickets") return "Tickets";
  if (activePage === "ai") return "AI Support";
  return "Dashboard";
}

function AiSupportPage() {
  const initialAiMessage = {
    role: "assistant",
    content: "Hi, I can help with shipments, cancellations, service credits, tickets, product help, and account support. Choose a topic to start, or describe your issue."
  };
  const [conversationId, setConversationId] = useState(null);
  const [input, setInput] = useState("");
  const [selectedCategoryId, setSelectedCategoryId] = useState(null);
  const [selectedSubcategory, setSelectedSubcategory] = useState(null);
  const [messages, setMessages] = useState([initialAiMessage]);
  const [sending, setSending] = useState(false);
  const [creatingTicket, setCreatingTicket] = useState(false);
  const [confirmingAction, setConfirmingAction] = useState(false);
  const [restoring, setRestoring] = useState(true);
  const [error, setError] = useState("");
  const selectedCategory = supportCategories.find((category) => category.id === selectedCategoryId);
  const selectedTopic = Boolean(selectedSubcategory);

  useEffect(() => {
    let cancelled = false;
    async function restoreConversation() {
      setRestoring(true);
      try {
        const payload = await apiFetch("/ai/conversation");
        if (cancelled) return;
        if (payload.conversation_id && payload.messages?.length) {
          setConversationId(payload.conversation_id);
          const restoredMessages = payload.messages.map((message) => ({
            role: message.role,
            content: message.content,
            confidence: message.metadata?.confidence,
            sources: []
          }));
          const pendingAction = payload.active_context?.pending_action;
          if (pendingAction?.type === "CANCELLATION_REQUEST" && restoredMessages.length) {
            restoredMessages[restoredMessages.length - 1] = {
              ...restoredMessages[restoredMessages.length - 1],
              actionPreview: {
                type: "CANCELLATION_REQUEST",
                title: "Cancellation Request",
                order_id: pendingAction.order_id,
                carrier: pendingAction.draft?.carrier,
                status: pendingAction.draft?.shipment_status,
                fee_inr: pendingAction.fee_inr ?? 0,
                warning: "This will create a support ticket for the ParcelPilot team to process the cancellation request.",
                confirm_label: "Create Cancellation Request"
              }
            };
          }
          if (pendingAction?.type === "CREATE_TICKET" && pendingAction.draft && restoredMessages.length) {
            restoredMessages[restoredMessages.length - 1] = {
              ...restoredMessages[restoredMessages.length - 1],
              ticketPreview: pendingAction.draft
            };
          }
          setMessages(restoredMessages);
          const category = String(payload.active_context?.category || "").toLowerCase().replaceAll("_", "-");
          if (supportCategories.some((item) => item.id === category)) {
            setSelectedCategoryId(category);
            setSelectedSubcategory({ id: "restored", label: "Restored conversation" });
          } else {
            setSelectedSubcategory({ id: "restored", label: "Restored conversation" });
          }
        }
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setRestoring(false);
      }
    }
    restoreConversation();
    return () => {
      cancelled = true;
    };
  }, []);

  async function submitPrompt(prompt) {
    const userMessage = prompt.trim();
    if (!userMessage || sending) return;
    setMessages((existing) => [...existing, { role: "user", content: userMessage }]);
    setSending(true);
    setError("");
    try {
      const payload = await apiFetch("/ai/chat", {
        method: "POST",
        body: JSON.stringify({
          message: userMessage,
          conversation_id: conversationId,
          category: selectedCategory?.id || null,
          subcategory: selectedSubcategory?.id || null
        })
      });
      setConversationId(payload.conversation_id);
      setMessages((existing) => [
        ...existing,
        {
          role: "assistant",
          content: payload.answer,
          confidence: payload.confidence,
          sources: payload.sources,
          ticketPreview: payload.ticket_preview,
          actionPreview: payload.action_preview
        }
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setSending(false);
    }
  }

  function chooseCategory(categoryId) {
    setSelectedCategoryId(categoryId);
    setSelectedSubcategory(null);
  }

  function chooseSubcategory(subcategory) {
    setSelectedSubcategory(subcategory);
    setMessages((existing) => [
      ...existing,
      {
        role: "assistant",
        content: `How can I help you with ${subcategory.label.toLowerCase()}?`
      }
    ]);
  }

  function chooseOther() {
    const prompt = selectedCategory?.otherPrompt || "No problem. Describe your issue and I'll help.";
    setSelectedSubcategory({ id: "other", label: "Other" });
    setMessages((existing) => [...existing, { role: "assistant", content: prompt }]);
  }

  async function sendMessage(event) {
    event.preventDefault();
    if (!input.trim()) return;
    const userMessage = input.trim();
    setInput("");
    await submitPrompt(userMessage);
  }

  async function startNewConversation() {
    setError("");
    try {
      await apiFetch("/ai/conversation/new", { method: "POST" });
      setConversationId(null);
      setSelectedCategoryId(null);
      setSelectedSubcategory(null);
      setMessages([initialAiMessage]);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="ai-layout">
      <section className="chat-panel">
        <div className="chat-stream">
          {messages.map((message, index) => (
            <div className={`chat-message ${message.role}`} key={`${message.role}-${index}`}>
              {message.role === "assistant" ? (
                <AssistantContent content={message.content} />
              ) : (
                <p>{message.content}</p>
              )}
              {message.confidence ? (
                <div className="chat-meta">
                  <StatusBadge value={`${message.confidence} confidence`} />
                  {message.sources?.map((source) => (
                    <span key={`${source.type}-${source.id || source.chunk_id}`}>
                      {formatSource(source)}
                    </span>
                  ))}
                </div>
              ) : null}
              {message.ticketPreview ? (
                <TicketPreviewCard
                  preview={message.ticketPreview}
                  conversationId={conversationId}
                  creating={creatingTicket}
                  onCreate={async (draft) => {
                    setCreatingTicket(true);
                    setError("");
                    try {
                      const payload = await apiFetch("/ai/tickets/confirm", {
                        method: "POST",
                        body: JSON.stringify({
                          conversation_id: conversationId,
                          subject: draft.subject,
                          description: draft.description
                        })
                      });
                      setMessages((existing) => [
                        ...existing,
                        {
                          role: "assistant",
                          content: `Ticket **${payload.ticket.ticket_id}** has been created.`,
                          confidence: "HIGH",
                          sources: [{ type: "ticket", id: payload.ticket.ticket_id }]
                        }
                      ]);
                    } catch (err) {
                      setError(err.message);
                    } finally {
                      setCreatingTicket(false);
                    }
                  }}
                />
              ) : null}
              {message.actionPreview ? (
                <ActionPreviewCard
                  preview={message.actionPreview}
                  conversationId={conversationId}
                  confirming={confirmingAction}
                  onConfirm={async () => {
                    setConfirmingAction(true);
                    setError("");
                    try {
                      const payload = await apiFetch("/ai/actions/cancel/confirm", {
                        method: "POST",
                        body: JSON.stringify({ conversation_id: conversationId })
                      });
                      setMessages((existing) => [
                        ...existing,
                        {
                          role: "assistant",
                          content: payload.message,
                          confidence: "HIGH",
                          sources: [
                            { type: "ticket", id: payload.ticket.ticket_id },
                            { type: "order", id: payload.order.order_id }
                          ]
                        }
                      ]);
                    } catch (err) {
                      setError(err.message);
                    } finally {
                      setConfirmingAction(false);
                    }
                  }}
                />
              ) : null}
            </div>
          ))}
        </div>
        {selectedTopic ? (
          <div className="chat-topic-bar">
            {selectedCategory ? (
              <>
                <span>{selectedCategory.label}</span>
                <ArrowLeft size={14} />
              </>
            ) : null}
            <strong>{selectedSubcategory.label}</strong>
          </div>
        ) : null}
        <form className="chat-input-row" onSubmit={sendMessage}>
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            disabled={!selectedTopic}
            placeholder={
              selectedTopic
                ? "Describe your query, include an order or ticket ID if you have one"
                : "Select a category and subcategory first, or choose Other"
            }
          />
          <button className="icon-button" type="submit" disabled={sending || !selectedTopic}>
            <Send size={18} />
            {sending ? "Sending..." : "Send"}
          </button>
        </form>
        {error ? <p className="error-text">{error}</p> : null}
      </section>

      <section className="panel ai-side-panel guided-support-panel">
        <div className="panel-header">
          <h2>{selectedCategory ? selectedCategory.label : "Start With A Topic"}</h2>
          {selectedCategory ? (
            <button
              className="text-button"
              onClick={() => {
                setSelectedCategoryId(null);
                setSelectedSubcategory(null);
              }}
            >
              <ArrowLeft size={16} />
              Change
            </button>
          ) : null}
        </div>
        <button className="secondary-button full-width" onClick={startNewConversation} disabled={restoring || sending}>
          <Plus size={18} />
          New Conversation
        </button>
        {!selectedCategory ? (
          <div className="support-category-list">
            {supportCategories.map((category) => {
              const Icon = category.icon;
              return (
                <button className="support-category" key={category.id} onClick={() => chooseCategory(category.id)}>
                  <Icon size={19} />
                  <span>
                    <strong>{category.label}</strong>
                    <small>{category.description}</small>
                  </span>
                </button>
              );
            })}
            <button className="support-category" onClick={chooseOther}>
              <HelpCircle size={19} />
              <span>
                <strong>Other</strong>
                <small>Describe your problem in your own words</small>
              </span>
            </button>
          </div>
        ) : (
          <div className="support-subcategory-list">
            <p className="panel-copy">What do you need help with?</p>
            {selectedCategory.subcategories.map((subcategory) => {
              const Icon = subcategory.icon;
              return (
                <button
                  className="support-subcategory"
                  key={subcategory.label}
                  onClick={() => chooseSubcategory(subcategory)}
                  disabled={sending}
                >
                  <Icon size={18} />
                  {subcategory.label}
                </button>
              );
            })}
            <button
              className="secondary-button full-width"
              onClick={chooseOther}
              disabled={sending}
            >
              <HelpCircle size={18} />
              Other
            </button>
          </div>
        )}
      </section>
    </div>
  );
}

function TicketPreviewCard({ preview, conversationId, creating, onCreate }) {
  const [draft, setDraft] = useState({
    subject: preview.subject || "",
    description: preview.description || ""
  });

  return (
    <div className="ticket-preview-card">
      <div className="ticket-preview-header">
        <span>CREATE SUPPORT TICKET</span>
        <StatusBadge value={preview.priority || "MEDIUM"} />
      </div>
      <label>
        Subject
        <input
          value={draft.subject}
          onChange={(event) => setDraft((current) => ({ ...current, subject: event.target.value }))}
        />
      </label>
      <label>
        Description
        <textarea
          value={draft.description}
          onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))}
        />
      </label>
      <div className="ticket-preview-grid">
        <span>Account</span>
        <strong>{preview.account_name || preview.account_id || "Current account"}</strong>
        <span>Order</span>
        <strong>{preview.order_id || "Not linked"}</strong>
        <span>Carrier</span>
        <strong>{preview.carrier || "Not linked"}</strong>
        <span>Status</span>
        <strong>{cleanLabel(preview.shipment_status || "Unknown")}</strong>
        <span>Priority</span>
        <strong>{preview.priority} - {preview.priority_reason}</strong>
        <span>SLA</span>
        <strong>{preview.response_target || "Not available"}</strong>
      </div>
      <p className="ticket-preview-reason">{preview.escalation_reason}</p>
      <button
        className="icon-button full-width"
        disabled={creating || !conversationId || draft.subject.trim().length < 3 || draft.description.trim().length < 3}
        onClick={() => onCreate(draft)}
      >
        <TicketCheck size={18} />
        {creating ? "Creating..." : "Create Ticket"}
      </button>
    </div>
  );
}

function ActionPreviewCard({ preview, conversationId, confirming, onConfirm }) {
  return (
    <div className="action-preview-card">
      <div className="ticket-preview-header">
        <span>{preview.title || "Confirm Action"}</span>
        <StatusBadge value={cleanLabel(preview.status || "Pending")} />
      </div>
      <div className="ticket-preview-grid">
        <span>Order</span>
        <strong>{preview.order_id}</strong>
        <span>Carrier</span>
        <strong>{preview.carrier || "Unknown"}</strong>
        <span>Status</span>
        <strong>{cleanLabel(preview.status || "Unknown")}</strong>
        <span>Fee</span>
        <strong>INR {preview.fee_inr ?? 0}</strong>
      </div>
      <p className="ticket-preview-reason">{preview.warning || "Please confirm before this action is executed."}</p>
      <button
        className="icon-button full-width"
        disabled={confirming || !conversationId}
        onClick={onConfirm}
      >
        <PackageCheck size={18} />
        {confirming ? "Confirming..." : preview.confirm_label || "Confirm"}
      </button>
    </div>
  );
}

function AssistantContent({ content }) {
  const blocks = toAssistantBlocks(content);
  return (
    <div className="assistant-content">
      {blocks.map((block, index) => {
        if (block.type === "heading") {
          return <h3 key={`${block.type}-${index}`}>{renderInline(block.text)}</h3>;
        }
        if (block.type === "list") {
          return (
            <ul key={`${block.type}-${index}`}>
              {block.items.map((item, itemIndex) => (
                <li key={`${item}-${itemIndex}`}>{renderInline(item)}</li>
              ))}
            </ul>
          );
        }
        if (block.type === "ordered") {
          return (
            <ol key={`${block.type}-${index}`}>
              {block.items.map((item, itemIndex) => (
                <li key={`${item}-${itemIndex}`}>{renderInline(item)}</li>
              ))}
            </ol>
          );
        }
        return <p key={`${block.type}-${index}`}>{renderInline(block.text)}</p>;
      })}
    </div>
  );
}

function toAssistantBlocks(content) {
  const normalized = String(content || "")
    .replace(/^\s*(\*\*)?answer\s*:\s*(\*\*)?\s*/i, "")
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/\r/g, "")
    .replace(/\\(#{1,6}\s*)/g, "$1")
    .replace(/(\\)?#{1,6}\s+/g, "\n## ")
    .replace(/(\\)?(\d+)\\\.\s*/g, "\n$2. ")
    .replace(/\\`/g, "`")
    .replace(/\\\*/g, "*")
    .replace(/\|\s*-{2,}[^|\n]*(\|[^|\n]*)+/g, "\n")
    .replace(/^\s*\|\s*/gm, "- ")
    .replace(/\s+\|\s+/g, "\n")
    .replace(/\s+[-•]\s+/g, "\n- ")
    .replace(/\*\*(What this means[^*]*)\*\*/gi, "\n**$1**\n")
    .replace(/\n{3,}/g, "\n\n");

  const lines = normalized
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .filter((line) => !/^[-|:\s]+$/.test(line));

  const blocks = [];
  let listItems = [];
  let orderedItems = [];

  function flushList() {
    if (listItems.length) {
      blocks.push({ type: "list", items: listItems });
      listItems = [];
    }
    if (orderedItems.length) {
      blocks.push({ type: "ordered", items: orderedItems });
      orderedItems = [];
    }
  }

  lines.forEach((line) => {
    if (/^(source|rule)$/i.test(line)) return;
    const bullet = line.match(/^[-•]\s+(.*)$/);
    if (bullet) {
      if (orderedItems.length) {
        blocks.push({ type: "ordered", items: orderedItems });
        orderedItems = [];
      }
      listItems.push(bullet[1]);
      return;
    }
    const ordered = line.match(/^\d+[.)]\s+(.*)$/);
    if (ordered) {
      if (listItems.length) {
        blocks.push({ type: "list", items: listItems });
        listItems = [];
      }
      orderedItems.push(ordered[1]);
      return;
    }
    flushList();
    const markdownHeading = line.match(/^#{1,6}\s+(.+)$/);
    const boldHeading = line.match(/^\*\*([^*]+)\*\*:?\s*$/);
    const heading = markdownHeading?.[1] || boldHeading?.[1];
    blocks.push({ type: heading ? "heading" : "paragraph", text: heading || line });
  });
  flushList();

  return blocks.length ? blocks : [{ type: "paragraph", text: "No answer returned." }];
}

function renderInline(text) {
  return String(text)
    .split(/(\*\*[^*]+\*\*)/g)
    .map((part, index) =>
      part.startsWith("**") && part.endsWith("**") ? (
        <strong key={`${part}-${index}`}>{part.slice(2, -2)}</strong>
      ) : (
        part
      )
    );
}
