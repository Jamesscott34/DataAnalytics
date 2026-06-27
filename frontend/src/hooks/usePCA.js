import { useCallback, useEffect, useState } from 'react';
import { getEda, runEda } from '../api/eda.js';
import { runPca } from '../api/models.js';

/**
 * usePCA
 *
 * Loads columns and runs principal component analysis.
 *
 * @param {number | null} fileId
 */
export function usePCA(fileId) {
  const [columns, setColumns] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [preparing, setPreparing] = useState(false);
  const [error, setError] = useState(null);

  const loadContext = useCallback(async () => {
    if (!fileId) {
      return;
    }
    setPreparing(true);
    setError(null);
    try {
      let edaResponse = await getEda(fileId);
      if (!edaResponse) {
        try {
          edaResponse = await runEda(fileId, { forceRefresh: false });
        } catch {
          edaResponse = null;
        }
      }
      if (edaResponse?.columns) {
        setColumns(
          edaResponse.columns
            .filter((column) => ['integer', 'float', 'categorical'].includes(column.inferred_type))
            .map((column) => column.name),
        );
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setPreparing(false);
    }
  }, [fileId]);

  useEffect(() => {
    loadContext();
  }, [loadContext]);

  const analyze = async ({ featureColumns, nComponents = 2, randomState = 42 }) => {
    if (!fileId) {
      return null;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await runPca(fileId, { featureColumns, nComponents, randomState });
      setResult(response);
      return response;
    } catch (err) {
      setError(err.message);
      setResult(null);
      return null;
    } finally {
      setLoading(false);
    }
  };

  return {
    columns,
    result,
    loading,
    preparing,
    error,
    analyze,
    reloadContext: loadContext,
  };
}
