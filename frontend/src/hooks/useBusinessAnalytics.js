import { useCallback, useEffect, useState } from 'react';
import { analyzeBusiness } from '../api/business.js';
import { getEda, runEda } from '../api/eda.js';

export function useBusinessAnalytics(fileId) {
  const [columns, setColumns] = useState([]);
  const [report, setReport] = useState(null);
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
        edaResponse = await runEda(fileId, { forceRefresh: false });
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

  const analyze = async (mapping) => {
    if (!fileId) {
      return null;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await analyzeBusiness(fileId, mapping);
      setReport(response);
      return response;
    } catch (err) {
      setError(err.message);
      setReport(null);
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { columns, report, loading, preparing, error, analyze };
}
