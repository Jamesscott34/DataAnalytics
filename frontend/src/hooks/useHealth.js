import { useEffect, useState } from 'react';
import { fetchHealth } from '../api/monitoring.js';

/**
 * useHealth
 *
 * Loads backend health status for display panels.
 *
 * @returns {{ status: string|null, loading: boolean, error: string|null, reload: () => void }}
 */
export function useHealth() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = () => {
    setLoading(true);
    setError(null);
    fetchHealth()
      .then((data) => setStatus(data.status))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  return { status, loading, error, reload: load };
}
