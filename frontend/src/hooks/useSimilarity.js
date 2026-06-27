import { useCallback, useEffect, useState } from 'react';
import { getEda, runEda } from '../api/eda.js';
import { runSimilarity } from '../api/models.js';

export function useSimilarity(fileId) {
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
      setColumns(edaResponse?.columns?.map((column) => column.name) ?? []);
    } catch (err) {
      setError(err.message);
    } finally {
      setPreparing(false);
    }
  }, [fileId]);

  useEffect(() => {
    loadContext();
  }, [loadContext]);

  const analyze = async ({
    mode,
    idColumn,
    featureColumns,
    topN = 10,
  }) => {
    if (!fileId) {
      return null;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await runSimilarity(fileId, {
        mode,
        idColumn,
        featureColumns,
        topN,
      });
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
