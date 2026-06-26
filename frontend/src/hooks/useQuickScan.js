import { useCallback, useState } from 'react';
import { getLatestQuickScan, runQuickScan } from '../api/quickScan.js';

/**
 * useQuickScan
 *
 * Runs or loads a full analysis quick scan for a file.
 *
 * @param {number | null} fileId
 */
export function useQuickScan(fileId) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const scan = useCallback(async () => {
    if (!fileId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await runQuickScan(fileId);
      setReport(response);
      return response;
    } catch (err) {
      setError(err.message);
      setReport(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, [fileId]);

  const loadLatest = useCallback(async () => {
    if (!fileId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await getLatestQuickScan(fileId);
      setReport(response);
      return response;
    } catch {
      setReport(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, [fileId]);

  return {
    report,
    loading,
    error,
    scan,
    loadLatest,
  };
}
