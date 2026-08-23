import { cleanLabel } from "../utils";

export default function StatusBadge({ value }) {
  const normalized = String(value || "Unknown").toLowerCase();
  return <span className={`status-badge ${normalized.replaceAll("_", "-")}`}>{cleanLabel(value)}</span>;
}
