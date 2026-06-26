import { Link } from 'react-router-dom';
import { useCallback, useEffect, useState } from 'react';
import { getScanResultViewPath, listScanResults } from '../api/export.js';

function formatBytes(bytes) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatSavedAt(iso) {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

/**
 * ScanResultsPanel
 *
 * Dashboard list of saved analytics reports in scan_results/.
 */
export function ScanResultsPanel({ refreshKey = 0 }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadResults = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await listScanResults();
      setItems(response.items ?? []);
    } catch (err) {
      setError(err.message);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadResults();
  }, [loadResults, refreshKey]);

  return (
    <section className="panel-card">
      <div className="panel-card-header">
        <h2>Saved scan reports</h2>
        <button type="button" className="text-button" onClick={loadResults} disabled={loading}>
          Refresh
        </button>
      </div>
      <p className="upload-help">
        Exports are saved as <code>{'{filename}_Analytics_dd-mm-yy.md'}</code> or{' '}
        <code>.pdf</code> in the <code>scan_results</code> folder.
      </p>
      {loading && <p>Loading saved reports…</p>}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      {!loading && !error && items.length === 0 && (
        <p>
          No saved reports yet. Run a{' '}
          <Link to="/scan">full analysis scan</Link> and export to Markdown or PDF.
        </p>
      )}
      {!loading && items.length > 0 && (
        <ul className="file-list">
          {items.map((item) => (
            <li key={item.filename}>
              <div>
                <strong>{item.filename}</strong>
                <span>
                  {item.format.toUpperCase()} · {formatBytes(item.size_bytes)} · saved{' '}
                  {formatSavedAt(item.saved_at)}
                </span>
              </div>
              <div className="inline-links">
                <Link to={getScanResultViewPath(item.filename)}>View in browser</Link>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
