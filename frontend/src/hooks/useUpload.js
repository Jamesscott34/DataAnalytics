import { useState } from 'react';
import { uploadCsv } from '../api/uploads.js';

/**
 * useUpload
 *
 * Handles CSV upload state and validation before calling the API.
 *
 * @returns {{ upload: Function, loading: boolean, error: string|null, result: Object|null }}
 */
export function useUpload() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const upload = async (file) => {
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
    try {
      const response = await uploadCsv(file);
      setResult(response);
      return response;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { upload, loading, error, result };
}
