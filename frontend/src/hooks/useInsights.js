import { useState } from 'react';
import { generateInsight } from '../api/insights.js';

export function useInsights() {
  const [insight, setInsight] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const generate = async ({ resultId, analysisType, jobId }) => {
    setLoading(true);
    setError(null);
    try {
      const response = await generateInsight({ resultId, analysisType, jobId });
      setInsight(response);
      return response;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { insight, loading, error, generate };
}
