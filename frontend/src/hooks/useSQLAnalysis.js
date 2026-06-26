import { useCallback, useEffect, useState } from 'react';
import { getSqlPresets, importSqlRows, runSqlPreset, runSqlQuery } from '../api/sql.js';

/**
 * useSQLAnalysis
 *
 * Loads SQL presets and runs import/query actions for a file.
 *
 * @param {number | null} fileId
 */
export function useSQLAnalysis(fileId) {
  const [importInfo, setImportInfo] = useState(null);
  const [presets, setPresets] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadPresets = useCallback(async () => {
    if (!fileId) {
      return;
    }
    const response = await getSqlPresets(fileId);
    setPresets(response.presets ?? []);
  }, [fileId]);

  useEffect(() => {
    if (!importInfo) {
      setPresets([]);
      return;
    }
    loadPresets().catch((err) => setError(err.message));
  }, [importInfo, loadPresets]);

  const importRows = async () => {
    if (!fileId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await importSqlRows(fileId);
      setImportInfo(response);
      setResult(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const executeQuery = async (query) => {
    if (!fileId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await runSqlQuery(fileId, query);
      setResult(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const executePreset = async (presetId) => {
    if (!fileId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await runSqlPreset(fileId, presetId);
      setResult(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return {
    importInfo,
    presets,
    result,
    loading,
    error,
    importRows,
    executeQuery,
    executePreset,
    setResult,
  };
}
