import { useNavigate, useParams } from 'react-router-dom';
import { useEffect } from 'react';
import { ClassificationForm } from '../components/ClassificationForm.jsx';
import { ClassificationResults } from '../components/ClassificationResults.jsx';
import { DatasetFilePicker } from '../components/DatasetFilePicker.jsx';
import { DatasetFileToolbar } from '../components/DatasetFileToolbar.jsx';
import { useClassification } from '../hooks/useClassification.js';
import { getLastFile, setLastFile } from '../utils/lastFile.js';
import { workspaceLinks } from '../utils/workspaceLinks.js';

/**
 * ClassificationPage
 *
 * Train classification models on an uploaded CSV file.
 */
export function ClassificationPage() {
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
  } = useClassification(hasFileId ? fileId : null);

  useEffect(() => {
    if (hasFileId && lastFile?.filename && lastFile.fileId === fileId) {
      setLastFile({ file_id: fileId, filename: lastFile.filename });
    }
  }, [fileId, hasFileId, lastFile]);

  if (!hasFileId) {
    return (
      <main className="page-shell page-shell--wide">
        <header className="page-header">
          <h1>Classification models</h1>
          <p className="page-lead">
            Choose an existing CSV or upload a new one. Security scanning runs in the
            background during upload.
          </p>
        </header>
        <DatasetFilePicker
          title="Choose a dataset for classification"
          description="Pick from your uploads or add a new CSV without leaving this page."
          onSelect={(file) => {
            setLastFile({ file_id: file.file_id, filename: file.filename });
            navigate(`/classification/${file.file_id}`);
          }}
        />
      </main>
    );
  }

  const activeFilename = lastFile?.fileId === fileId ? lastFile.filename : null;

  return (
    <main className="page-shell page-shell--wide">
      <header className="page-header">
        <h1>Classification models</h1>
        <p className="page-lead">
          Train logistic, tree, forest, k-NN, SVM, or naive Bayes models and review
          accuracy, F1, confusion matrix, and confidence scores.
        </p>
      </header>

      <DatasetFileToolbar
        fileId={fileId}
        filename={activeFilename}
        basePath="/classification"
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
          <ClassificationForm
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
          <ClassificationResults result={result} />
        </section>
      )}
    </main>
  );
}
