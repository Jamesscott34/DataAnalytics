import { useCallback, useEffect, useState } from 'react';
import { getEda, getEdaSuggestions, runEda } from '../api/eda.js';
import { getModelRegistry, runClustering } from '../api/models.js';

/**
 * useClustering
 *
 * Loads algorithms, column hints, and runs clustering.
 *
 * @param {number | null} fileId
 */
export function useClustering(fileId) {
  const [algorithms, setAlgorithms] = useState([]);
  const [columns, setColumns] = useState([]);
  const [suggestions, setSuggestions] = useState(null);
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
      const registry = await getModelRegistry();
      setAlgorithms(registry.clustering ?? []);

      let edaResponse = await getEda(fileId);
      if (!edaResponse) {
        try {
          edaResponse = await runEda(fileId, { forceRefresh: false });
        } catch {
          edaResponse = null;
        }
      }

      if (edaResponse?.columns) {
        setColumns(edaResponse.columns.map((column) => column.name));
      }

      try {
        setSuggestions(await getEdaSuggestions(fileId));
      } catch {
        setSuggestions(null);
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

  const cluster = async ({
    algorithm,
    featureColumns,
    nClusters = 3,
    maxK = 8,
    randomState = 42,
  }) => {
    if (!fileId) {
      return null;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await runClustering(fileId, {
        algorithm,
        featureColumns,
        nClusters,
        maxK,
        randomState,
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
    algorithms,
    columns,
    suggestions,
    result,
    loading,
    preparing,
    error,
    cluster,
    reloadContext: loadContext,
  };
}
