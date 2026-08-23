import { orderStatusRank, priorityRank } from "./constants";

export const CUSTOMER_VIEW_KEY = "parcelpilot.customer.view";

export function readCustomerView() {
  try {
    return JSON.parse(localStorage.getItem(CUSTOMER_VIEW_KEY) || "{}");
  } catch {
    return {};
  }
}

export function sortTickets(items) {
  return [...items].sort((a, b) => {
    const priorityDelta = (priorityRank[a.priority] ?? 9) - (priorityRank[b.priority] ?? 9);
    if (priorityDelta !== 0) return priorityDelta;
    return new Date(b.last_customer_message_at || b.created_at || 0) - new Date(a.last_customer_message_at || a.created_at || 0);
  });
}

export function sortOrders(items) {
  return [...items].sort((a, b) => {
    const statusDelta = (orderStatusRank[a.status] ?? 9) - (orderStatusRank[b.status] ?? 9);
    if (statusDelta !== 0) return statusDelta;
    return new Date(b.booked_at || 0) - new Date(a.booked_at || 0);
  });
}

export function uniqueValues(values) {
  return Array.from(new Set(values.filter(Boolean))).sort((a, b) => String(a).localeCompare(String(b)));
}

export function withinDateRange(value, range) {
  if (range === "ALL" || !value) return true;
  const date = new Date(value);
  const now = new Date();
  const start = new Date(now);
  start.setHours(0, 0, 0, 0);
  if (range === "TODAY") return date >= start;
  if (range === "LAST_7_DAYS") {
    start.setDate(start.getDate() - 7);
    return date >= start;
  }
  if (range === "LAST_30_DAYS") {
    start.setDate(start.getDate() - 30);
    return date >= start;
  }
  return true;
}

export function formatOptionLabel(value) {
  if (value === "ALL") return "All";
  if (value === "TODAY") return "Today";
  if (value === "LAST_7_DAYS") return "Last 7 days";
  if (value === "LAST_30_DAYS") return "Last 30 days";
  return cleanLabel(value);
}

export function formatSource(source) {
  if (source.type === "document") return `document: ${source.document_id || source.chunk_id}`;
  if (source.type === "orders") return `orders: ${source.id}${source.count ? ` (${source.count})` : ""}`;
  return `${source.type}: ${source.id || source.document_id || source.chunk_id}`;
}

export function firstName(name) {
  return String(name || "there").split(" ")[0];
}

export function cleanLabel(value) {
  return String(value || "Unknown").replaceAll("_", " ");
}

export function formatDateTime(value) {
  if (!value) return "Not available";
  return new Intl.DateTimeFormat("en-IN", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  }).format(new Date(value));
}

export function formatMoney(value) {
  if (value === null || value === undefined || value === "") return "Not available";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0
  }).format(value);
}
