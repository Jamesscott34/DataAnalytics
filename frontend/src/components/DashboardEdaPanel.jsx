import { Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { getEda, runEda } from '../api/eda.js';

/**
 * DashboardEdaPanel
 *
 * Compact EDA snapshot for the dashboard focus file.
 */
export function DashboardEdaPanel({ fileId, filename }) {
  const [eda, setEda] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [notRun, setNotRun] = useState(false);

  useEffect(() => {
    if (!fileId) {
      setLoading(false);
      return;
    }

    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      setNotRun(false);
      try {
        const response = await getEda(fileId);
        if (!cancelled) {
          setEda(response);
        }
      } catch (err) {
        if (!cancelled) {
          if (/not been run|not found/i.test(err.message)) {
            setNotRun(true);
            setEda(null);
          } else {
            setError(err.message);
          }
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [fileId]);

  const handleRun = async () => {
    setAnalyzing(true);
    setError(null);
    try {
      const response = await runEda(fileId, { forceRefresh: false });
      setEda(response);
      setNotRun(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  if (!fileId) {
    return (
      <section className="panel-card dashboard-eda-panel">
        <div className="panel-card-header">
          <h2>Exploratory analysis</h2>
        </div>
        <p>Upload a CSV or pick a sample dataset to see column types and quality checks here.</p>
      </section>
    );
  }

  return (
    <section className="panel-card dashboard-eda-panel">
      <div className="panel-card-header">
        <h2>Exploratory analysis</h2>
        <Link to={`/eda/${fileId}`}>Open full EDA</Link>
      </div>
      <p className="dashboard-eda-file">
        Focus file: <strong>{filename}</strong>
      </p>

      {loading && <p>Loading EDA snapshot…</p>}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      {!loading && notRun && (
        <div className="dashboard-eda-empty">
          <p>EDA has not been run for this file yet.</p>
          <button
            type="button"
            className="primary-button"
            onClick={handleRun}
            disabled={analyzing}
          >
            {analyzing ? 'Analyzing…' : 'Run EDA from dashboard'}
          </button>
        </div>
      )}

      {!loading && eda && (
        <>
          <div className="eda-summary-grid dashboard-eda-summary">
            <article className="eda-stat-card">
              <h3>Rows</h3>
              <p>{eda.summary.row_count}</p>
            </article>
            <article className="eda-stat-card">
              <h3>Columns</h3>
              <p>{eda.summary.column_count}</p>
            </article>
            <article className="eda-stat-card">
              <h3>Missing</h3>
              <p>{eda.summary.missing_percent.toFixed(1)}%</p>
            </article>
            <article className="eda-stat-card">
              <h3>Warnings</h3>
              <p>{eda.quality_warnings?.length ?? 0}</p>
            </article>
          </div>
          {eda.quality_warnings?.length > 0 && (
            <p className="dashboard-eda-warning">
              {eda.quality_warnings[0]}
              {eda.quality_warnings.length > 1 &&
                ` (+${eda.quality_warnings.length - 1} more)`}
            </p>
          )}
          <div className="inline-links">
            <Link to={`/eda/${fileId}`}>View charts &amp; columns</Link>
            <button
              type="button"
              className="text-button"
              onClick={handleRun}
              disabled={analyzing}
            >
              {analyzing ? 'Refreshing…' : 'Refresh analysis'}
            </button>
          </div>
        </>
      )}
    </section>
  );
}
