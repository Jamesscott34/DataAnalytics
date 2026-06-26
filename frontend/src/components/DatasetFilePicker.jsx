import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { listUploads } from '../api/uploads.js';
import { useBackgroundUpload } from '../hooks/useBackgroundUpload.js';
import { getLastFile } from '../utils/lastFile.js';
import { DuplicateResolutionPanel } from './DuplicateResolutionPanel.jsx';
import { ScannerResultPanel } from './ScannerResultPanel.jsx';

const LARGE_FILE_THRESHOLD_BYTES = 50 * 1024 * 1024;

/**
 * DatasetFilePicker
 *
 * Choose an existing upload or add a new CSV inline. Security scanning still
 * runs on the server during upload.
 */
export function DatasetFilePicker({
  title,
  description,
  selectedFileId = null,
  onSelect,
}) {
  const inputRef = useRef(null);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [pendingFile, setPendingFile] = useState(null);
  const {
    upload,
    continueWithExisting,
    replaceExisting,
    deleteExistingDuplicate,
    clearDuplicate,
    loading: uploading,
    error: uploadError,
    duplicate,
    scanResult,
    statusText,
  } = useBackgroundUpload();

  const loadFiles = async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const response = await listUploads();
      setFiles(response.items ?? []);
    } catch (err) {
      setLoadError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFiles();
  }, []);

  const handleUploadPick = async (event) => {
    const file = event.target.files?.[0] ?? null;
    event.target.value = '';
    if (!file) {
      return;
    }
    setPendingFile(file);
    const response = await upload(file);
    if (response?.file_id) {
      await loadFiles();
      onSelect({ file_id: response.file_id, filename: response.filename });
      setPendingFile(null);
      return;
    }
    if (!duplicate) {
      setPendingFile(null);
    }
  };

  const resolveDuplicate = async (action) => {
    if (!pendingFile) {
      return;
    }
    let response = null;
    if (action === 'use_existing') {
      response = await continueWithExisting(pendingFile);
    } else if (action === 'replace') {
      response = await replaceExisting(pendingFile);
    } else if (action === 'delete') {
      response = await deleteExistingDuplicate(pendingFile);
    }
    if (response?.file_id) {
      await loadFiles();
      onSelect({ file_id: response.file_id, filename: response.filename });
      setPendingFile(null);
      clearDuplicate();
    }
  };

  const lastFile = getLastFile();

  return (
    <section className="panel-card dataset-file-picker" aria-labelledby="dataset-picker-heading">
      <header className="dataset-file-picker-header">
        <div>
          <h2 id="dataset-picker-heading">{title}</h2>
          {description && <p className="upload-help">{description}</p>}
        </div>
        <label className="primary-button dataset-file-upload-button">
          {uploading ? statusText || 'Uploading…' : 'Upload CSV'}
          <input
            ref={inputRef}
            type="file"
            accept=".csv,text/csv"
            className="sr-only"
            onChange={handleUploadPick}
            disabled={uploading}
            aria-label="Upload CSV file"
          />
        </label>
      </header>

      <p className="dataset-file-picker-note">
        New files are scanned for unsafe content in the background while you continue.
      </p>

      {loadError && (
        <p className="form-error" role="alert">
          {loadError}
        </p>
      )}
      {uploadError && (
        <p className="form-error" role="alert">
          {uploadError}
        </p>
      )}
      {uploading && statusText && (
        <p className="status-text" role="status">
          {statusText}
        </p>
      )}

      <ScannerResultPanel result={scanResult} />
      <DuplicateResolutionPanel
        duplicate={duplicate}
        loading={uploading}
        onUseExisting={() => resolveDuplicate('use_existing')}
        onReplace={() => resolveDuplicate('replace')}
        onDeleteExisting={() => resolveDuplicate('delete')}
        onCancel={() => {
          clearDuplicate();
          setPendingFile(null);
        }}
      />

      {loading && <p>Loading your files…</p>}

      {!loading && files.length === 0 && (
        <p>No uploads yet. Upload a CSV above or browse sample datasets.</p>
      )}

      {!loading && files.length > 0 && (
        <ul className="dataset-file-list">
          {files.map((file) => {
            const isSelected = selectedFileId === file.id;
            const isLast = lastFile?.fileId === file.id;
            return (
              <li key={file.id} className={isSelected ? 'is-selected' : ''}>
                <button
                  type="button"
                  className="dataset-file-option"
                  onClick={() =>
                    onSelect({
                      file_id: file.id,
                      filename: file.original_filename,
                    })
                  }
                >
                  <span className="dataset-file-option-name">{file.original_filename}</span>
                  <span className="dataset-file-option-meta">
                    {file.row_count ?? 0} rows · {file.column_count ?? 0} columns
                    {isLast ? ' · last used' : ''}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      )}

      <p className="dataset-file-picker-footer">
        <Link to="/assets">Browse sample datasets</Link>
        {' · '}
        <Link to="/dashboard">Back to dashboard</Link>
      </p>
    </section>
  );
}

export { LARGE_FILE_THRESHOLD_BYTES };
