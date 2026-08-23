export const SUPPORT_VIEW_KEY = "parcelpilot.support.view";

export function readSupportView() {
  try {
    return JSON.parse(localStorage.getItem(SUPPORT_VIEW_KEY) || "{}");
  } catch {
    return {};
  }
}

export function uniqueValues(values) {
  return Array.from(new Set(values.filter(Boolean))).sort((a, b) => String(a).localeCompare(String(b)));
}

export function withinDateRange(value, range) {
  if (range === "ALL" || !value) {
    return true;
  }
  const date = new Date(value);
  const now = new Date();
  const start = new Date(now);
  start.setHours(0, 0, 0, 0);
  if (range === "TODAY") {
    return date >= start;
  }
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

export function formatOptionLabel(option) {
  if (option === "ALL") return "All";
  if (option === "TODAY") return "Today";
  if (option === "LAST_7_DAYS") return "Last 7 days";
  if (option === "LAST_30_DAYS") return "Last 30 days";
  return String(option).replaceAll("_", " ");
}

export function formatDate(value) {
  if (!value) return "";
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

export function formatTime(value) {
  if (!value) return "Not set";
  return new Intl.DateTimeFormat("en-IN", {
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}
