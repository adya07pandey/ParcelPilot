export default function PageHeader({ title, subtitle, meta }) {
  return (
    <header className="support-page-header">
      <h1>{title}</h1>
      <p>{subtitle}</p>
      {meta ? <span>{meta}</span> : null}
    </header>
  );
}
