import { useCallback, useState } from 'react';
import { getEdaSuggestions, runEda } from '../api/eda.js';

/**
 * useEDA
 *
 * Runs exploratory data analysis for an uploaded file.
 *
 * @param {number | null} fileId
 */
export function useEDA(fileId) {
  const [eda, setEda] = useState(null);
  const [suggestions, setSuggestions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyze = useCallback(
    async (forceRefresh = false) => {
      if (!fileId) {
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const response = await runEda(fileId, { forceRefresh });
        setEda(response);
        const suggestionResponse = await getEdaSuggestions(fileId);
        setSuggestions(suggestionResponse);
      } catch (err) {
        setError(err.message);
        setEda(null);
        setSuggestions(null);
      } finally {
        setLoading(false);
      }
    },
    [fileId],
  );

  return {
    eda,
    suggestions,
    loading,
    error,
    analyze,
  };
}
