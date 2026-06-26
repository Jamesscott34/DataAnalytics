import { useNavigate, useParams } from 'react-router-dom';
import { useEffect } from 'react';
import { DatasetFilePicker } from '../components/DatasetFilePicker.jsx';
import { DatasetFileToolbar } from '../components/DatasetFileToolbar.jsx';
import { RegressionForm } from '../components/RegressionForm.jsx';
import { RegressionResults } from '../components/RegressionResults.jsx';
import { useRegression } from '../hooks/useRegression.js';
import { getLastFile, setLastFile } from '../utils/lastFile.js';
import { workspaceLinks } from '../utils/workspaceLinks.js';

/**
 * RegressionPage
 *
 * Train regression models on an uploaded CSV file.
 */
export function RegressionPage() {
  const navigate = useNavigate();
  const { fileId: routeFileId } = useParams();
  const fileId = routeFileId ? Number(routeFileId) : null;
  const hasFileId = Number.isFinite(fileId);
  const lastFile = getLastFile();
  const {
    algorithms,
    columns,
    suggestions,
    result,
    loading,
    preparing,
    error,
    train,
  } = useRegression(hasFileId ? fileId : null);

  useEffect(() => {
    if (hasFileId && lastFile?.filename && lastFile.fileId === fileId) {
      setLastFile({ file_id: fileId, filename: lastFile.filename });
    }
  }, [fileId, hasFileId, lastFile]);

  if (!hasFileId) {
    return (
      <main className="page-shell page-shell--wide">
        <header className="page-header">
          <h1>Regression models</h1>
          <p className="page-lead">
            Choose an existing CSV or upload a new one. Security scanning runs in the
            background during upload.
          </p>
        </header>
        <DatasetFilePicker
          title="Choose a dataset for regression"
          description="Pick from your uploads or add a new CSV without leaving this page."
          onSelect={(file) => {
            setLastFile({ file_id: file.file_id, filename: file.filename });
            navigate(`/regression/${file.file_id}`);
          }}
        />
      </main>
    );
  }

  const activeFilename = lastFile?.fileId === fileId ? lastFile.filename : null;

  return (
    <main className="page-shell page-shell--wide">
      <header className="page-header">
        <h1>Regression models</h1>
        <p className="page-lead">
          Train linear, polynomial, decision tree, or random forest models and review
          MAE, RMSE, R², and feature importance.
        </p>
      </header>

      <DatasetFileToolbar
        fileId={fileId}
        filename={activeFilename}
        basePath="/regression"
        relatedLinks={workspaceLinks(fileId)}
      />

      <section className="panel-card">
        <h2>Model configuration</h2>
        {preparing && <p>Loading columns and algorithm registry…</p>}
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        {!preparing && (
          <RegressionForm
            algorithms={algorithms}
            columns={columns}
            suggestions={suggestions}
            loading={loading}
            onSubmit={train}
          />
        )}
      </section>

      {result && (
        <section className="panel-card">
          <h2>Results</h2>
          <RegressionResults result={result} />
        </section>
      )}
    </main>
  );
}
