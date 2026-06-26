import { Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { DuplicateUploadError } from '../api/uploads.js';
import { listAssets, selectAsset } from '../api/assets.js';
import { setLastFile } from '../utils/lastFile.js';
import { DuplicateResolutionPanel } from './DuplicateResolutionPanel.jsx';
import { AddToGroupPanel } from './AddToGroupPanel.jsx';
import { ScannerResultPanel } from './ScannerResultPanel.jsx';

/**
 * AssetsFileList
 *
 * Lists temp_assets CSV files and lets analysts import one without uploading.
 */
export function AssetsFileList() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedFilename, setSelectedFilename] = useState(null);
  const [result, setResult] = useState(null);
  const [duplicate, setDuplicate] = useState(null);
  const [importing, setImporting] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    listAssets()
      .then((response) => {
        if (active) {
          setFiles(response.files);
        }
      })
      .catch((err) => {
        if (active) {
          setError(err.message);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const importAsset = async (filename, duplicateAction = null) => {
    setImporting(true);
    setError(null);
    setDuplicate(null);
    setSelectedFilename(filename);
    try {
      const response = await selectAsset(filename, { duplicateAction });
      setResult(response);
      setLastFile({ file_id: response.file_id, filename: response.filename });
    } catch (err) {
      if (err instanceof DuplicateUploadError) {
        setDuplicate(err.payload);
        setResult(null);
      } else {
        setError(err.message);
      }
    } finally {
      setImporting(false);
    }
  };

  const clearDuplicate = () => {
    setDuplicate(null);
    setResult(null);
    setSelectedFilename(null);
  };

  if (loading) {
    return <p>Loading temp assets…</p>;
  }

  return (
    <section className="assets-panel" aria-labelledby="assets-heading">
      <h2 id="assets-heading">Temp assets</h2>
      <p className="upload-help">
        Choose a CSV from the project temp_assets folder. Files go through the same
        security scan and duplicate checks as manual uploads.
      </p>
      {error && <p role="alert">{error}</p>}
      {files.length === 0 ? (
        <p>No CSV files found in temp_assets.</p>
      ) : (
        <ul className="assets-list">
          {files.map((file) => (
            <li key={file.name}>
              <div>
                <strong>{file.name}</strong>
                <span>{formatBytes(file.size_bytes)}</span>
              </div>
              <button
                type="button"
                onClick={() => importAsset(file.name)}
                disabled={importing}
              >
                {importing && selectedFilename === file.name
                  ? 'Importing…'
                  : 'Use file'}
              </button>
            </li>
          ))}
        </ul>
      )}

      <ScannerResultPanel
        result={result?.scan_result ?? duplicate?.scan_result ?? null}
      />
      <DuplicateResolutionPanel
        duplicate={duplicate}
        loading={importing}
        onUseExisting={() => importAsset(selectedFilename, 'use_existing')}
        onReplace={() => importAsset(selectedFilename, 'replace')}
        onDeleteExisting={() => importAsset(selectedFilename, 'replace')}
        onCancel={clearDuplicate}
      />

      {result && (
        <div className="upload-result" role="status" aria-live="polite">
          <p>Selected: {result.filename}</p>
          <p>Rows: {result.row_count}</p>
          <p>Columns: {result.column_count}</p>
          <p>SHA-256: {result.file_hash}</p>
          <div className="inline-links">
            <Link to={`/sql/${result.file_id}`}>Run SQL analysis</Link>
            <Link to={`/eda/${result.file_id}`}>Run EDA</Link>
            <Link to={`/versions/${result.file_id}`}>View version history</Link>
          </div>
          <AddToGroupPanel fileId={result.file_id} filename={result.filename} />
        </div>
      )}
    </section>
  );
}

function formatBytes(bytes) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
