import { useState } from 'react';
import { deleteUpload, DuplicateUploadError, uploadCsv } from '../api/uploads.js';
import { sha256File } from '../utils/hash.js';
import { setLastFile } from '../utils/lastFile.js';

const LARGE_FILE_THRESHOLD_BYTES = 50 * 1024 * 1024;

/**
 * useBackgroundUpload
 *
 * Upload helper for inline CSV pickers. Hashes large files automatically and
 * surfaces scanner/duplicate state without leaving SQL or EDA pages.
 */
export function useBackgroundUpload() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [duplicate, setDuplicate] = useState(null);
  const [scanResult, setScanResult] = useState(null);
  const [statusText, setStatusText] = useState(null);

  const upload = async (file, clientSha256 = null, duplicateAction = null) => {
    if (!file) {
      setError('Choose a CSV file first.');
      return null;
    }
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setError('Only .csv files are allowed.');
      return null;
    }

    setLoading(true);
    setError(null);
    setDuplicate(null);
    setScanResult(null);

    try {
      let hash = clientSha256;
      if (!hash && file.size > LARGE_FILE_THRESHOLD_BYTES) {
        setStatusText('Calculating file hash…');
        hash = await sha256File(file);
      }
      setStatusText('Uploading and scanning…');

      const options = {};
      if (hash) {
        options.clientSha256 = hash;
      }
      if (duplicateAction) {
        options.duplicateAction = duplicateAction;
      }

      const response = await uploadCsv(file, options);
      setScanResult(response.scan_result ?? null);
      setLastFile({ file_id: response.file_id, filename: response.filename });
      setStatusText(null);
      return response;
    } catch (err) {
      if (err instanceof DuplicateUploadError) {
        setDuplicate(err.payload);
        setScanResult(err.payload.scan_result ?? null);
        setStatusText(null);
        return null;
      }
      setError(err.message);
      setStatusText(null);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const continueWithExisting = async (file, clientSha256 = null) => {
    let hash = clientSha256;
    if (!hash && file.size > LARGE_FILE_THRESHOLD_BYTES) {
      setStatusText('Calculating file hash…');
      hash = await sha256File(file);
    }
    return upload(file, hash, 'use_existing');
  };

  const replaceExisting = async (file, clientSha256 = null) => {
    let hash = clientSha256;
    if (!hash && file.size > LARGE_FILE_THRESHOLD_BYTES) {
      setStatusText('Calculating file hash…');
      hash = await sha256File(file);
    }
    return upload(file, hash, 'replace');
  };

  const deleteExistingDuplicate = async (file, clientSha256 = null) => {
    if (!duplicate?.existing_file?.id) {
      setError('No duplicate file to delete.');
      return null;
    }

    setLoading(true);
    setError(null);
    try {
      await deleteUpload(duplicate.existing_file.id);
      setDuplicate(null);
      return upload(file, clientSha256, null);
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const clearDuplicate = () => {
    setDuplicate(null);
    setScanResult(null);
    setError(null);
    setStatusText(null);
  };

  return {
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
  };
}
