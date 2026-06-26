import { useMemo, useState } from 'react';
import { buildSqlCommandList } from '../utils/sqlQueryBuilder.js';

/**
 * SQLCommandPicker
 *
 * Dropdown of SQL templates with load-into-editor and run actions.
 *
 * @param {{
 *   tableName: string,
 *   columns: string[],
 *   serverPresets?: Array<{ id: string, name: string, description: string, sql: string }>,
 *   disabled?: boolean,
 *   onLoad: (sql: string) => void,
 *   onRun: (sql: string) => void,
 * }} props
 */
export function SQLCommandPicker({
  tableName,
  columns,
  serverPresets = [],
  disabled = false,
  onLoad,
  onRun,
}) {
  const commands = useMemo(() => {
    const local = buildSqlCommandList(tableName, columns);
    const fromServer = serverPresets.map((preset) => ({
      id: `server_${preset.id}`,
      label: preset.name,
      description: preset.description,
      sql: preset.sql,
    }));
    const seen = new Set();
    return [...fromServer, ...local].filter((command) => {
      if (seen.has(command.sql)) {
        return false;
      }
      seen.add(command.sql);
      return true;
    });
  }, [tableName, columns, serverPresets]);

  const [selectedId, setSelectedId] = useState(commands[0]?.id ?? '');

  const selected =
    commands.find((command) => command.id === selectedId) ?? commands[0] ?? null;

  if (!tableName || commands.length === 0) {
    return null;
  }

  return (
    <div className="sql-command-picker">
      <label htmlFor="sql-command-select">SQL command library</label>
      <div className="sql-command-picker-row">
        <select
          id="sql-command-select"
          value={selected?.id ?? ''}
          onChange={(event) => setSelectedId(event.target.value)}
          disabled={disabled}
        >
          {commands.map((command) => (
            <option key={command.id} value={command.id}>
              {command.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          className="secondary-button"
          disabled={disabled || !selected}
          onClick={() => selected && onLoad(selected.sql)}
        >
          Load into editor
        </button>
        <button
          type="button"
          className="primary-button"
          disabled={disabled || !selected}
          onClick={() => selected && onRun(selected.sql)}
        >
          Run command
        </button>
      </div>
      {selected && <p className="field-help">{selected.description}</p>}
      {selected && (
        <pre className="sql-command-preview" aria-label="Selected SQL preview">
          {selected.sql}
        </pre>
      )}
    </div>
  );
}
