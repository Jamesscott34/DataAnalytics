import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ColumnHeadersPanel } from '../components/ColumnHeadersPanel.jsx';
import { DatasetFilePicker } from '../components/DatasetFilePicker.jsx';
import { DatasetFileToolbar } from '../components/DatasetFileToolbar.jsx';
import { SQLCommandPicker } from '../components/SQLCommandPicker.jsx';
import { SelectableDataTable } from '../components/SelectableDataTable.jsx';
import { useSQLAnalysis } from '../hooks/useSQLAnalysis.js';
import { getLastFile, setLastFile } from '../utils/lastFile.js';
import { workspaceLinks } from '../utils/workspaceLinks.js';
import {
  buildSelectColumnQuery,
  buildSelectedRowsQuery,
} from '../utils/sqlQueryBuilder.js';

/**
 * SQLAnalysisPage
 *
 * Step 1: import (headers only) → Step 2: SQL → Step 3: results.
 */
export function SQLAnalysisPage() {
  const navigate = useNavigate();
  const { fileId: routeFileId } = useParams();
  const fileId = routeFileId ? Number(routeFileId) : null;
  const hasFileId = Number.isFinite(fileId);
  const lastFile = getLastFile();
  const [step, setStep] = useState('import');
  const [query, setQuery] = useState('');
  const [selectedRowIndexes, setSelectedRowIndexes] = useState(new Set());
  const {
    importInfo,
    presets,
    result,
    loading,
    error,
    importRows,
    executeQuery,
  } = useSQLAnalysis(hasFileId ? fileId : null);

  useEffect(() => {
    if (hasFileId && lastFile?.filename && lastFile.fileId === fileId) {
      setLastFile({ file_id: fileId, filename: lastFile.filename });
    }
  }, [fileId, hasFileId, lastFile]);

  useEffect(() => {
    if (importInfo?.table_name) {
      setQuery(`SELECT * FROM "${importInfo.table_name}"`);
      setStep('query');
      setSelectedRowIndexes(new Set());
    }
  }, [importInfo]);

  const runQuery = useCallback(
    async (sql) => {
      setQuery(sql);
      await executeQuery(sql);
      setStep('results');
    },
    [executeQuery],
  );

  const handleImport = async () => {
    await importRows();
  };

  const toggleRow = (rowIndex) => {
    setSelectedRowIndexes((current) => {
      const next = new Set(current);
      if (next.has(rowIndex)) {
        next.delete(rowIndex);
      } else {
        next.add(rowIndex);
      }
      return next;
    });
  };

  const toggleAllRows = (checked) => {
    if (!result?.rows) {
      return;
    }
    if (!checked) {
      setSelectedRowIndexes(new Set());
      return;
    }
    setSelectedRowIndexes(new Set(result.rows.map((_, index) => index)));
  };

  const applySelectedRowsQuery = () => {
    if (!importInfo?.table_name || !result) {
      return;
    }
    setQuery(
      buildSelectedRowsQuery(
        importInfo.table_name,
        result.columns,
        result.rows,
        selectedRowIndexes,
      ),
    );
    setStep('query');
  };

  const handleColumnClick = (column) => {
    if (!importInfo?.table_name) {
      return;
    }
    setQuery(buildSelectColumnQuery(importInfo.table_name, column));
    setStep('query');
  };

  const selectionSummary = useMemo(() => {
    if (selectedRowIndexes.size === 0) {
      return 'No rows selected';
    }
    return `${selectedRowIndexes.size} row${selectedRowIndexes.size === 1 ? '' : 's'} selected`;
  }, [selectedRowIndexes]);

  if (!hasFileId) {
    return (
      <main className="page-shell page-shell--wide">
        <header className="page-header">
          <h1>SQL analysis</h1>
          <p className="page-lead">
            Choose an existing CSV or upload a new one. Security scanning runs in the
            background during upload.
          </p>
        </header>
        <DatasetFilePicker
          title="Choose a dataset for SQL"
          description="Pick from your uploads or add a new CSV without leaving this page."
          onSelect={(file) => {
            setLastFile({ file_id: file.file_id, filename: file.filename });
            navigate(`/sql/${file.file_id}`);
          }}
        />
      </main>
    );
  }

  const activeFilename = lastFile?.fileId === fileId ? lastFile.filename : null;

  return (
    <main className="page-shell page-shell--wide">
      <header className="page-header">
        <h1>SQL analysis</h1>
        <p className="page-lead">
          Import to load headers first, choose a SQL command or write your own, then
          continue to see row results.
        </p>
        <p className="page-meta">
          <Link to="/groups">Dataset groups</Link> · <Link to="/dashboard">Dashboard</Link>
        </p>
      </header>

      <DatasetFileToolbar
        fileId={fileId}
        filename={activeFilename}
        basePath="/sql"
        relatedLinks={workspaceLinks(fileId)}
      />

      <ol className="stepper" aria-label="SQL workflow steps">
        <li className={step === 'import' ? 'is-active' : importInfo ? 'is-done' : ''}>
          1. Import headers
        </li>
        <li className={step === 'query' ? 'is-active' : step === 'results' ? 'is-done' : ''}>
          2. Build SQL
        </li>
        <li className={step === 'results' ? 'is-active' : ''}>3. View results</li>
      </ol>

      <section className="panel-card">
        <h2>Step 1 — Import column headers</h2>
        <p>
          Rows are loaded on the server, but you only see column names until you run a
          query.
        </p>
        <button
          type="button"
          className="primary-button"
          onClick={handleImport}
          disabled={loading || Boolean(importInfo)}
        >
          {importInfo ? 'Headers imported' : loading ? 'Importing…' : 'Import all CSV rows'}
        </button>
        {importInfo && (
          <ColumnHeadersPanel
            tableName={importInfo.table_name}
            columns={importInfo.columns}
            importedRows={importInfo.imported_rows}
          />
        )}
      </section>

      {importInfo && step !== 'import' && (
        <section className="panel-card">
          <h2>Step 2 — Choose or write SQL</h2>
          <SQLCommandPicker
            tableName={importInfo.table_name}
            columns={importInfo.columns}
            serverPresets={presets}
            disabled={loading}
            onLoad={(sql) => {
              setQuery(sql);
              setStep('query');
            }}
            onRun={runQuery}
          />
          <label htmlFor="sql-query">Custom SQL</label>
          <textarea
            id="sql-query"
            rows={8}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            spellCheck={false}
          />
          <div className="button-row">
            <button
              type="button"
              className="primary-button"
              onClick={() => runQuery(query)}
              disabled={loading || !query.trim()}
            >
              Continue — run query
            </button>
          </div>
        </section>
      )}

      {loading && <p className="status-text">Running…</p>}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      {step === 'results' && result && (
        <section className="panel-card" aria-live="polite">
          <div className="panel-card-header">
            <h2>Step 3 — Results ({result.row_count} rows)</h2>
            <span className="selection-badge">{selectionSummary}</span>
          </div>
          <div className="button-row">
            <button
              type="button"
              className="secondary-button"
              onClick={applySelectedRowsQuery}
              disabled={selectedRowIndexes.size === 0}
            >
              Refine query from selected rows
            </button>
            <button
              type="button"
              className="secondary-button"
              onClick={() => setStep('query')}
            >
              Back to SQL editor
            </button>
          </div>
          <SelectableDataTable
            columns={result.columns}
            rows={result.rows}
            selectable
            selectedRowIndexes={selectedRowIndexes}
            onToggleRow={toggleRow}
            onToggleAll={toggleAllRows}
            onColumnClick={handleColumnClick}
          />
        </section>
      )}
    </main>
  );
}
