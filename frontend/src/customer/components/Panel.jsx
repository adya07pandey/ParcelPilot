export default function Panel({ title, action, onAction, children }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>{title}</h2>
        {action ? (
          <button className="text-button" onClick={onAction}>
            {action}
          </button>
        ) : null}
      </div>
      {children}
    </section>
  );
}
