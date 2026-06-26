import { Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { useUpload } from '../hooks/useUpload.js';
import { sha256File } from '../utils/hash.js';
import { setLastFile } from '../utils/lastFile.js';
import { DuplicateResolutionPanel } from './DuplicateResolutionPanel.jsx';
import { AddToGroupPanel } from './AddToGroupPanel.jsx';
import { ScannerResultPanel } from './ScannerResultPanel.jsx';

const LARGE_FILE_THRESHOLD_BYTES = 50 * 1024 * 1024;

/**
 * UploadForm
 *
 * Lets analysts upload a CSV file and displays returned metadata.
 */
export function UploadForm() {
  const [file, setFile] = useState(null);
  const [clientHash, setClientHash] = useState(null);
  const [hashing, setHashing] = useState(false);
  const [largeFileConfirmed, setLargeFileConfirmed] = useState(false);
  const {
    upload,
    continueWithExisting,
    replaceExisting,
    deleteExistingDuplicate,
    clearDuplicate,
    loading,
    error,
    result,
    duplicate,
  } = useUpload();

  useEffect(() => {
    if (result?.file_id) {
      setLastFile({ file_id: result.file_id, filename: result.filename });
    }
  }, [result]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (isLargeFile(file) && !largeFileConfirmed) {
      return;
    }
    await upload(file, clientHash);
  };

  const handleFileChange = async (event) => {
    const selectedFile = event.target.files?.[0] ?? null;
    setFile(selectedFile);
    setClientHash(null);
    setLargeFileConfirmed(false);
    clearDuplicate();

    if (isLargeFile(selectedFile)) {
      setHashing(true);
      try {
        setClientHash(await sha256File(selectedFile));
      } finally {
        setHashing(false);
      }
    }
  };

  const requiresConfirmation = isLargeFile(file);
  const uploadDisabled =
    loading ||
    hashing ||
    duplicate !== null ||
    (requiresConfirmation && (!clientHash || !largeFileConfirmed));

  const scanResult = result?.scan_result ?? duplicate?.scan_result ?? null;

  return (
    <section className="upload-panel" aria-labelledby="upload-heading">
      <h2 id="upload-heading">Upload CSV</h2>
      <p className="upload-help">
        Files are checked for unsafe names, binary content, CSV injection, and
        suspicious payloads. After the security scan passes, duplicate files are flagged
        so you can use, replace, or delete the existing copy.
      </p>
      <form onSubmit={handleSubmit}>
        <label htmlFor="csv-file">CSV file</label>
        <input
          id="csv-file"
          type="file"
          accept=".csv,text/csv"
          onChange={handleFileChange}
          aria-label="CSV file"
        />
        {requiresConfirmation && (
          <div className="large-file-check">
            <p>
              This file is larger than 50 MB. The browser calculated this SHA-256 hash
              so you can verify it matches the backend result after upload.
            </p>
            <code>{hashing ? 'Calculating hash…' : clientHash}</code>
            <label htmlFor="large-file-confirm">
              <input
                id="large-file-confirm"
                type="checkbox"
                checked={largeFileConfirmed}
                onChange={(event) => setLargeFileConfirmed(event.target.checked)}
              />{' '}
              I confirm this hash is expected and want to upload this large CSV.
            </label>
          </div>
        )}
        {error && <p role="alert">{error}</p>}
        <button type="submit" disabled={uploadDisabled} aria-busy={loading || hashing}>
          {hashing ? 'Hashing…' : loading ? 'Uploading…' : 'Upload'}
        </button>
      </form>

      <ScannerResultPanel result={scanResult} />
      <DuplicateResolutionPanel
        duplicate={duplicate}
        loading={loading}
        onUseExisting={() => continueWithExisting(file, clientHash)}
        onReplace={() => replaceExisting(file, clientHash)}
        onDeleteExisting={() => deleteExistingDuplicate(file, clientHash)}
        onCancel={clearDuplicate}
      />

      {result && (
        <div className="upload-result" role="status" aria-live="polite">
          <p>Uploaded: {result.filename}</p>
          <p>Rows: {result.row_count}</p>
          <p>Columns: {result.column_count}</p>
          <p>Duplicate: {result.is_duplicate ? 'yes' : 'no'}</p>
          <p>Version: {result.version_number}</p>
          <p>SHA-256: {result.file_hash}</p>
          {result.client_hash_match && <p>Browser/backend hash match: yes</p>}
          <p>
            <Link to={`/versions/${result.file_id}`}>View version history</Link>
          </p>
          <p>
            <Link to={`/sql/${result.file_id}`}>Run SQL analysis</Link>
          </p>
          <p>
            <Link to={`/eda/${result.file_id}`}>Run EDA</Link>
          </p>
          <AddToGroupPanel fileId={result.file_id} filename={result.filename} />
        </div>
      )}
    </section>
  );
}

function isLargeFile(file) {
  return Boolean(file && file.size > LARGE_FILE_THRESHOLD_BYTES);
}
