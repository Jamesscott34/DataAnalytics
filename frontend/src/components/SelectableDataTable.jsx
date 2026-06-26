/**
 * SelectableDataTable
 *
 * Data table with optional multi-select checkboxes for building SQL filters.
 *
 * @param {{
 *   columns: string[],
 *   rows: Array<Array<unknown>>,
 *   caption?: string,
 *   selectable?: boolean,
 *   selectedRowIndexes?: Set<number>,
 *   onToggleRow?: (rowIndex: number) => void,
 *   onToggleAll?: (checked: boolean) => void,
 *   onColumnClick?: (column: string) => void,
 * }} props
 */
export function SelectableDataTable({
  columns,
  rows,
  caption,
  selectable = false,
  selectedRowIndexes = new Set(),
  onToggleRow,
  onToggleAll,
  onColumnClick,
}) {
  if (!columns?.length) {
    return <p>No columns to display.</p>;
  }

  const allSelected = rows.length > 0 && selectedRowIndexes.size === rows.length;
  const someSelected = selectedRowIndexes.size > 0 && !allSelected;

  return (
    <div className="data-table-wrap">
      <table className="data-table data-table--selectable">
        {caption && <caption>{caption}</caption>}
        <thead>
          <tr>
            {selectable && (
              <th scope="col" className="select-col">
                <input
                  type="checkbox"
                  aria-label="Select all rows"
                  checked={allSelected}
                  ref={(input) => {
                    if (input) {
                      input.indeterminate = someSelected;
                    }
                  }}
                  onChange={(event) => onToggleAll?.(event.target.checked)}
                />
              </th>
            )}
            {columns.map((column) => (
              <th key={column} scope="col">
                {onColumnClick ? (
                  <button
                    type="button"
                    className="column-header-button"
                    onClick={() => onColumnClick(column)}
                    title={`Use column ${column} in SQL`}
                  >
                    {column}
                  </button>
                ) : (
                  column
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length + (selectable ? 1 : 0)}>No rows returned.</td>
            </tr>
          ) : (
            rows.map((row, rowIndex) => {
              const selected = selectedRowIndexes.has(rowIndex);
              return (
                <tr key={`row-${rowIndex}`} className={selected ? 'is-selected' : undefined}>
                  {selectable && (
                    <td className="select-col">
                      <input
                        type="checkbox"
                        aria-label={`Select row ${rowIndex + 1}`}
                        checked={selected}
                        onChange={() => onToggleRow?.(rowIndex)}
                      />
                    </td>
                  )}
                  {row.map((cell, cellIndex) => (
                    <td key={`${rowIndex}-${cellIndex}`}>{String(cell ?? '')}</td>
                  ))}
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
