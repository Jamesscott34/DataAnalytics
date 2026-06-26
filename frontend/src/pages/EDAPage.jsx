import { useNavigate, useParams } from 'react-router-dom';
import { useEffect } from 'react';
import { DatasetFilePicker } from '../components/DatasetFilePicker.jsx';
import { DatasetFileToolbar } from '../components/DatasetFileToolbar.jsx';
import { EDADashboard } from '../components/EDADashboard.jsx';
import { useEDA } from '../hooks/useEDA.js';
import { getLastFile, setLastFile } from '../utils/lastFile.js';
import { workspaceLinks } from '../utils/workspaceLinks.js';

/**
 * EDAPage
 *
 * Exploratory data analysis for an uploaded CSV file.
 */
export function EDAPage() {
  const navigate = useNavigate();
  const { fileId: routeFileId } = useParams();
  const fileId = routeFileId ? Number(routeFileId) : null;
  const hasFileId = Number.isFinite(fileId);
  const lastFile = getLastFile();
  const { eda, suggestions, loading, error, analyze } = useEDA(hasFileId ? fileId : null);

  useEffect(() => {
    if (hasFileId && lastFile?.filename && lastFile.fileId === fileId) {
      setLastFile({ file_id: fileId, filename: lastFile.filename });
    }
  }, [fileId, hasFileId, lastFile]);

  if (!hasFileId) {
    return (
      <main className="page-shell page-shell--wide">
        <header className="page-header">
          <h1>Exploratory analysis</h1>
          <p className="page-lead">
            Choose an existing CSV or upload a new one. Security scanning runs in the
            background during upload.
          </p>
        </header>
        <DatasetFilePicker
          title="Choose a dataset for EDA"
          description="Pick from your uploads or add a new CSV without leaving this page."
          onSelect={(file) => {
            setLastFile({ file_id: file.file_id, filename: file.filename });
            navigate(`/eda/${file.file_id}`);
          }}
        />
      </main>
    );
  }

  const activeFilename = lastFile?.fileId === fileId ? lastFile.filename : null;

  return (
    <main className="page-shell page-shell--wide">
      <header className="page-header">
        <h1>Exploratory analysis</h1>
        <p className="page-lead">
          Column types, missing values, distributions, and quality warnings.
        </p>
      </header>

      <DatasetFileToolbar
        fileId={fileId}
        filename={activeFilename}
        basePath="/eda"
        relatedLinks={workspaceLinks(fileId)}
      />

      <section className="panel-card">
        <div className="panel-card-header">
          <h2>Run analysis</h2>
          <div className="inline-links">
            <button
              type="button"
              className="primary-button"
              onClick={() => analyze(false)}
              disabled={loading}
            >
              {loading ? 'Analyzing…' : eda ? 'Refresh from cache' : 'Run EDA'}
            </button>
            {eda && (
              <button
                type="button"
                className="secondary-button"
                onClick={() => analyze(true)}
                disabled={loading}
              >
                Force recompute
              </button>
            )}
          </div>
        </div>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        {!eda && !loading && !error && (
          <p>Run EDA to inspect column types, missing values, and chart summaries.</p>
        )}
      </section>

      <EDADashboard eda={eda} suggestions={suggestions} />
    </main>
  );
}
