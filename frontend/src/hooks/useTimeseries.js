import { useCallback, useEffect, useState } from 'react';
import { getEda, getEdaSuggestions, runEda } from '../api/eda.js';
import { getModelRegistry, runTimeseries } from '../api/models.js';

/**
 * useTimeseries
 *
 * Loads algorithms, column hints, and runs time series forecasts.
 *
 * @param {number | null} fileId
 */
export function useTimeseries(fileId) {
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
      setAlgorithms(registry.timeseries ?? []);

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

  const forecast = async ({
    algorithm,
    dateColumn,
    valueColumn,
    forecastPeriods = 5,
    window = 3,
    arLags = 3,
    arimaP = 1,
    arimaD = 1,
    arimaQ = 1,
    seasonalPeriod = null,
  }) => {
    if (!fileId) {
      return null;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await runTimeseries(fileId, {
        algorithm,
        dateColumn,
        valueColumn,
        forecastPeriods,
        window,
        arLags,
        arimaP,
        arimaD,
        arimaQ,
        seasonalPeriod,
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
    forecast,
    reloadContext: loadContext,
  };
}
