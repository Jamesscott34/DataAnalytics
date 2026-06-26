/**
 * ColumnHeadersPanel
 *
 * Shows imported column headers without loading row data into the UI.
 *
 * @param {{ tableName: string, columns: string[], importedRows?: number, alias?: string }} props
 */
export function ColumnHeadersPanel({
  tableName,
  columns,
  importedRows,
  alias,
}) {
  return (
    <article className="headers-card">
      <header className="headers-card-header">
        <div>
          <h3>{alias ?? tableName}</h3>
          <p>
            Table <code>{tableName}</code>
            {typeof importedRows === 'number' && (
              <>
                {' '}
                · <strong>{importedRows}</strong> rows loaded
              </>
            )}
          </p>
        </div>
      </header>
      <ul className="headers-list">
        {columns.map((column) => (
          <li key={column}>
            <code>{column}</code>
          </li>
        ))}
      </ul>
    </article>
  );
}
