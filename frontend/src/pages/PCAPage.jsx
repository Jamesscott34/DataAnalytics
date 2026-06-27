import { useNavigate, useParams } from 'react-router-dom';
import { useEffect } from 'react';
import { DatasetFilePicker } from '../components/DatasetFilePicker.jsx';
import { DatasetFileToolbar } from '../components/DatasetFileToolbar.jsx';
import { PCAForm } from '../components/PCAForm.jsx';
import { PCAResults } from '../components/PCAResults.jsx';
import { usePCA } from '../hooks/usePCA.js';
import { getLastFile, setLastFile } from '../utils/lastFile.js';
import { workspaceLinks } from '../utils/workspaceLinks.js';

export function PCAPage() {
  const navigate = useNavigate();
  const { fileId: routeFileId } = useParams();
  const fileId = routeFileId ? Number(routeFileId) : null;
  const hasFileId = Number.isFinite(fileId);
  const lastFile = getLastFile();
  const { columns, result, loading, preparing, error, analyze } = usePCA(hasFileId ? fileId : null);

  useEffect(() => {
    if (hasFileId && lastFile?.filename && lastFile.fileId === fileId) {
      setLastFile({ file_id: fileId, filename: lastFile.filename });
    }
  }, [fileId, hasFileId, lastFile]);

  if (!hasFileId) {
    return (
      <main className="page-shell page-shell--wide">
        <header className="page-header">
          <h1>PCA</h1>
          <p className="page-lead">Choose a dataset for principal component analysis.</p>
        </header>
        <DatasetFilePicker
          title="Choose a dataset for PCA"
          onSelect={(file) => {
            setLastFile({ file_id: file.file_id, filename: file.filename });
            navigate(`/pca/${file.file_id}`);
          }}
        />
      </main>
    );
  }

  return (
    <main className="page-shell page-shell--wide">
      <header className="page-header">
        <h1>Principal component analysis</h1>
        <p className="page-lead">Reduce dimensionality and review explained variance.</p>
      </header>
      <DatasetFileToolbar
        fileId={fileId}
        filename={lastFile?.fileId === fileId ? lastFile.filename : null}
        basePath="/pca"
        relatedLinks={workspaceLinks(fileId)}
      />
      <section className="panel-card">
        {preparing && <p>Loading columns…</p>}
        {!preparing && <PCAForm columns={columns} loading={loading} onSubmit={analyze} />}
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
      </section>
      <PCAResults result={result} />
    </main>
  );
}
