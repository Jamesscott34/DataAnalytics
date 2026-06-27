import { useCallback, useEffect, useState } from 'react';
import { getEda, getEdaSuggestions, runEda } from '../api/eda.js';
import { getModelRegistry, trainClassification } from '../api/models.js';

/**
 * useClassification
 *
 * Loads algorithms, column hints from EDA, and trains classifiers.
 *
 * @param {number | null} fileId
 */
export function useClassification(fileId) {
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
      setAlgorithms(registry.classification ?? []);

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
        const suggestionResponse = await getEdaSuggestions(fileId);
        setSuggestions(suggestionResponse);
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

  const train = async ({
    algorithm,
    targetColumn,
    featureColumns,
    testSize = 0.2,
    randomState = 42,
  }) => {
    if (!fileId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await trainClassification(fileId, {
        algorithm,
        targetColumn,
        featureColumns,
        testSize,
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
    train,
    reloadContext: loadContext,
  };
}
