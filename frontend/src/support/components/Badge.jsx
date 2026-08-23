export default function Badge({ value }) {
  const text = String(value || "UNKNOWN").replaceAll("_", " ");
  return <span className={`support-badge ${text.toLowerCase().replaceAll(" ", "-")}`}>{text}</span>;
}

export function SlaBadge({ sla }) {
  return <Badge value={sla?.state || "WITHIN_SLA"} />;
}
