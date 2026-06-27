import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { DatasetFilePicker } from '../components/DatasetFilePicker.jsx';
import { DatasetFileToolbar } from '../components/DatasetFileToolbar.jsx';
import { SimilarityForm } from '../components/SimilarityForm.jsx';
import { SimilarityResults } from '../components/SimilarityResults.jsx';
import { useSimilarity } from '../hooks/useSimilarity.js';
import { getLastFile, setLastFile } from '../utils/lastFile.js';
import { workspaceLinks } from '../utils/workspaceLinks.js';

export function SimilarityPage() {
  const navigate = useNavigate();
  const { fileId: routeFileId } = useParams();
  const fileId = routeFileId ? Number(routeFileId) : null;
  const hasFileId = Number.isFinite(fileId);
  const lastFile = getLastFile();
  const { columns, result, loading, preparing, error, analyze } = useSimilarity(
    hasFileId ? fileId : null,
  );

  useEffect(() => {
    if (hasFileId && lastFile?.filename && lastFile.fileId === fileId) {
      setLastFile({ file_id: fileId, filename: lastFile.filename });
    }
  }, [fileId, hasFileId, lastFile]);

  if (!hasFileId) {
    return (
      <main className="page-shell page-shell--wide">
        <header className="page-header">
          <h1>Similarity analysis</h1>
          <p className="page-lead">Choose a dataset to compare similar rows or items.</p>
        </header>
        <DatasetFilePicker
          title="Choose a dataset for similarity"
          onSelect={(file) => {
            setLastFile({ file_id: file.file_id, filename: file.filename });
            navigate(`/similarity/${file.file_id}`);
          }}
        />
      </main>
    );
  }

  return (
    <main className="page-shell page-shell--wide">
      <header className="page-header">
        <h1>Similarity analysis</h1>
        <p className="page-lead">
          Use cosine similarity to find rows or columns that behave alike.
        </p>
      </header>
      <DatasetFileToolbar
        fileId={fileId}
        filename={lastFile?.fileId === fileId ? lastFile.filename : null}
        basePath="/similarity"
        relatedLinks={workspaceLinks(fileId)}
      />
      <section className="panel-card">
        {preparing && <p>Loading columns…</p>}
        {!preparing && <SimilarityForm columns={columns} loading={loading} onSubmit={analyze} />}
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
      </section>
      <SimilarityResults result={result} />
    </main>
  );
}
