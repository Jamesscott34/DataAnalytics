/**
 * DataTable
 *
 * Renders tabular query or preview results.
 *
 * @param {{ columns: string[], rows: Array<Array<unknown>>, caption?: string }} props
 */
export function DataTable({ columns, rows, caption }) {
  if (!columns?.length) {
    return <p>No columns to display.</p>;
  }

  return (
    <div className="data-table-wrap">
      <table className="data-table">
        {caption && <caption>{caption}</caption>}
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length}>No rows returned.</td>
            </tr>
          ) : (
            rows.map((row, rowIndex) => (
              <tr key={`row-${rowIndex}`}>
                {row.map((cell, cellIndex) => (
                  <td key={`${rowIndex}-${cellIndex}`}>{String(cell ?? '')}</td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
