export default function Metric({ icon: Icon, label, value }) {
  return (
    <div className="metric">
      <Icon size={20} />
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
