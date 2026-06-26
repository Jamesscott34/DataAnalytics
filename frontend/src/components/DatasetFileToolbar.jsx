import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { listUploads } from '../api/uploads.js';
import { useBackgroundUpload } from '../hooks/useBackgroundUpload.js';
import { setLastFile } from '../utils/lastFile.js';
import { DuplicateResolutionPanel } from './DuplicateResolutionPanel.jsx';
import { ScannerResultPanel } from './ScannerResultPanel.jsx';

/**
 * DatasetFileToolbar
 *
 * Shows the active dataset and inline upload / file-switch actions.
 */
export function DatasetFileToolbar({
  fileId,
  filename,
  basePath,
  companionPath,
  relatedLinks = [],
}) {
  const navigate = useNavigate();
  const inputRef = useRef(null);
  const [resolvedName, setResolvedName] = useState(filename ?? '');
  const [pendingFile, setPendingFile] = useState(null);
  const {
    upload,
    continueWithExisting,
    replaceExisting,
    deleteExistingDuplicate,
    clearDuplicate,
    loading,
    error,
    duplicate,
    scanResult,
    statusText,
  } = useBackgroundUpload();

  useEffect(() => {
    if (filename) {
      setResolvedName(filename);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const response = await listUploads();
        const match = (response.items ?? []).find((file) => file.id === fileId);
        if (!cancelled && match) {
          setResolvedName(match.original_filename);
        }
      } catch {
        if (!cancelled) {
          setResolvedName(`File #${fileId}`);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [fileId, filename]);

  const handleUploadPick = async (event) => {
    const file = event.target.files?.[0] ?? null;
    event.target.value = '';
    if (!file) {
      return;
    }
    setPendingFile(file);
    const response = await upload(file);
    if (response?.file_id) {
      setLastFile({ file_id: response.file_id, filename: response.filename });
      navigate(`${basePath}/${response.file_id}`);
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
      setLastFile({ file_id: response.file_id, filename: response.filename });
      navigate(`${basePath}/${response.file_id}`);
      setPendingFile(null);
      clearDuplicate();
    }
  };

  const workspaceLinks =
    relatedLinks.length > 0
      ? relatedLinks
      : companionPath
        ? [{ to: `${companionPath}/${fileId}`, label: 'Switch workspace' }]
        : [];

  return (
    <section className="panel-card dataset-file-toolbar" aria-label="Dataset selection">
      <div className="dataset-file-toolbar-main">
        <div>
          <p className="dataset-file-toolbar-label">Current dataset</p>
          <p className="dataset-file-toolbar-name">{resolvedName || `File #${fileId}`}</p>
        </div>
        <div className="inline-links">
          <Link to={basePath}>Change file</Link>
          {workspaceLinks.map((link) => (
            <Link key={link.to} to={link.to}>
              {link.label}
            </Link>
          ))}
          <label className="text-button dataset-file-upload-link">
            {loading ? statusText || 'Uploading…' : 'Upload CSV'}
            <input
              ref={inputRef}
              type="file"
              accept=".csv,text/csv"
              className="sr-only"
              onChange={handleUploadPick}
              disabled={loading}
              aria-label="Upload CSV file"
            />
          </label>
        </div>
      </div>
      {loading && statusText && (
        <p className="status-text" role="status">
          {statusText}
        </p>
      )}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      <ScannerResultPanel result={scanResult} />
      <DuplicateResolutionPanel
        duplicate={duplicate}
        loading={loading}
        onUseExisting={() => resolveDuplicate('use_existing')}
        onReplace={() => resolveDuplicate('replace')}
        onDeleteExisting={() => resolveDuplicate('delete')}
        onCancel={() => {
          clearDuplicate();
          setPendingFile(null);
        }}
      />
    </section>
  );
}
