export default function DataTable({ columns, rows }) {
  if (!rows.length) return <EmptyState text="No records match this view." />;
  return (
    <div className="support-table-wrap">
      <table className="support-table">
        <thead>
          <tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.key} onClick={row.onClick}>
              {row.cells.map((cell, index) => <td key={`${row.key}-${index}`}>{cell}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function EmptyState({ text }) {
  return <p className="support-empty">{text}</p>;
}
