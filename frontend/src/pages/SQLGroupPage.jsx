import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  getGroupPresets,
  importGroupTables,
  listGroups,
  runGroupSqlQuery,
} from '../api/groups.js';
import { ColumnHeadersPanel } from '../components/ColumnHeadersPanel.jsx';
import { SQLCommandPicker } from '../components/SQLCommandPicker.jsx';
import { SelectableDataTable } from '../components/SelectableDataTable.jsx';

/**
 * SQLGroupPage
 *
 * Multi-table SQL workflow for a grouped set of CSV files.
 */
export function SQLGroupPage() {
  const { groupId: routeGroupId } = useParams();
  const groupId = Number(routeGroupId);
  const [group, setGroup] = useState(null);
  const [importInfo, setImportInfo] = useState(null);
  const [presets, setPresets] = useState([]);
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [step, setStep] = useState('import');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!Number.isFinite(groupId)) {
      return;
    }
    listGroups()
      .then((response) => {
        const match = response.items.find((item) => item.id === groupId);
        setGroup(match ?? null);
      })
      .catch((err) => setError(err.message));
  }, [groupId]);

  const handleImport = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await importGroupTables(groupId);
      setImportInfo(response);
      const presetResponse = await getGroupPresets(groupId);
      setPresets(presetResponse.presets ?? []);
      if (response.tables[0]) {
        setQuery(`SELECT * FROM "${response.tables[0].table_name}"`);
      }
      setStep('query');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const runQuery = async (sql) => {
    setLoading(true);
    setError(null);
    setQuery(sql);
    try {
      const response = await runGroupSqlQuery(groupId, sql);
      setResult(response);
      setStep('results');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!Number.isFinite(groupId)) {
    return (
      <main className="page-shell page-shell--wide">
        <h1>Group SQL</h1>
        <Link to="/groups">Back to groups</Link>
      </main>
    );
  }

  return (
    <main className="page-shell page-shell--wide">
      <header className="page-header">
        <h1>{group?.name ?? 'Dataset group SQL'}</h1>
        <p className="page-lead">
          Import all grouped CSV files (headers only), then run SQL across tables — for
          example JOIN customers with prices.
        </p>
        <p className="page-meta">
          <Link to="/groups">All groups</Link> · <Link to="/dashboard">Dashboard</Link>
        </p>
      </header>

      <ol className="stepper" aria-label="Group SQL workflow steps">
        <li className={step === 'import' ? 'is-active' : importInfo ? 'is-done' : ''}>
          1. Import group headers
        </li>
        <li className={step === 'query' ? 'is-active' : step === 'results' ? 'is-done' : ''}>
          2. Build SQL
        </li>
        <li className={step === 'results' ? 'is-active' : ''}>3. View results</li>
      </ol>

      <section className="panel-card">
        <h2>Grouped files</h2>
        {group?.members?.length ? (
          <ul className="file-list">
            {group.members.map((member) => (
              <li key={member.file_id}>
                <div>
                  <strong>{member.original_filename}</strong>
                  <span>
                    SQL alias: <code>{member.table_alias}</code>
                  </span>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p>No files in this group yet.</p>
        )}
        <button
          type="button"
          className="primary-button"
          onClick={handleImport}
          disabled={loading || Boolean(importInfo) || !group?.members?.length}
        >
          {importInfo ? 'Headers imported' : 'Import all group CSV rows'}
        </button>
      </section>

      {importInfo?.tables?.map((table) => (
        <ColumnHeadersPanel
          key={table.file_id}
          alias={table.table_alias}
          tableName={table.table_name}
          columns={table.columns}
          importedRows={table.imported_rows}
        />
      ))}

      {importInfo && step !== 'import' && (
        <section className="panel-card">
          <h2>SQL command library</h2>
          {importInfo.tables[0] && (
            <SQLCommandPicker
              tableName={importInfo.tables[0].table_name}
              columns={importInfo.tables[0].columns}
              serverPresets={presets}
              disabled={loading}
              onLoad={setQuery}
              onRun={runQuery}
            />
          )}
          <label htmlFor="group-sql-query">Custom SQL (JOIN supported)</label>
          <textarea
            id="group-sql-query"
            rows={8}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            spellCheck={false}
          />
          <button
            type="button"
            className="primary-button"
            onClick={() => runQuery(query)}
            disabled={loading || !query.trim()}
          >
            Continue — run query
          </button>
        </section>
      )}

      {loading && <p className="status-text">Running…</p>}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      {step === 'results' && result && (
        <section className="panel-card">
          <h2>Results ({result.row_count} rows)</h2>
          <SelectableDataTable columns={result.columns} rows={result.rows} />
        </section>
      )}
    </main>
  );
}
