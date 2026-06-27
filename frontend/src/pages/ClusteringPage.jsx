import { useNavigate, useParams } from 'react-router-dom';
import { useEffect } from 'react';
import { ClusteringForm } from '../components/ClusteringForm.jsx';
import { ClusteringResults } from '../components/ClusteringResults.jsx';
import { DatasetFilePicker } from '../components/DatasetFilePicker.jsx';
import { DatasetFileToolbar } from '../components/DatasetFileToolbar.jsx';
import { useClustering } from '../hooks/useClustering.js';
import { getLastFile, setLastFile } from '../utils/lastFile.js';
import { workspaceLinks } from '../utils/workspaceLinks.js';

export function ClusteringPage() {
  const navigate = useNavigate();
  const { fileId: routeFileId } = useParams();
  const fileId = routeFileId ? Number(routeFileId) : null;
  const hasFileId = Number.isFinite(fileId);
  const lastFile = getLastFile();
  const { algorithms, columns, suggestions, result, loading, preparing, error, cluster } =
    useClustering(hasFileId ? fileId : null);

  useEffect(() => {
    if (hasFileId && lastFile?.filename && lastFile.fileId === fileId) {
      setLastFile({ file_id: fileId, filename: lastFile.filename });
    }
  }, [fileId, hasFileId, lastFile]);

  if (!hasFileId) {
    return (
      <main className="page-shell page-shell--wide">
        <header className="page-header">
          <h1>Clustering</h1>
          <p className="page-lead">Choose a dataset for k-means or hierarchical clustering.</p>
        </header>
        <DatasetFilePicker
          title="Choose a dataset for clustering"
          onSelect={(file) => {
            setLastFile({ file_id: file.file_id, filename: file.filename });
            navigate(`/clustering/${file.file_id}`);
          }}
        />
      </main>
    );
  }

  return (
    <main className="page-shell page-shell--wide">
      <header className="page-header">
        <h1>Clustering</h1>
        <p className="page-lead">Group similar rows with k-means or hierarchical clustering.</p>
      </header>
      <DatasetFileToolbar
        fileId={fileId}
        filename={lastFile?.fileId === fileId ? lastFile.filename : null}
        basePath="/clustering"
        relatedLinks={workspaceLinks(fileId)}
      />
      <section className="panel-card">
        {preparing && <p>Loading columns…</p>}
        {!preparing && (
          <ClusteringForm
            algorithms={algorithms}
            columns={columns}
            suggestions={suggestions}
            loading={loading}
            onSubmit={cluster}
          />
        )}
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
      </section>
      <ClusteringResults result={result} />
    </main>
  );
}
