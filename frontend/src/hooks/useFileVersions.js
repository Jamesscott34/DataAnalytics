import { useEffect, useState } from 'react';
import { compareFileVersions, getFileVersions } from '../api/uploads.js';

/**
 * useFileVersions
 *
 * Loads and compares version history for an uploaded file.
 *
 * @param {number|null} fileId
 * @returns {Object}
 */
export function useFileVersions(fileId) {
  const [history, setHistory] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!fileId) {
      setHistory(null);
      return;
    }

    let active = true;
    setLoading(true);
    setError(null);
    getFileVersions(fileId)
      .then((response) => {
        if (active) {
          setHistory(response);
        }
      })
      .catch((err) => {
        if (active) {
          setError(err.message);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [fileId]);

  const compareVersions = async (versionA, versionB) => {
    if (!fileId) {
      return;
    }
    setError(null);
    const response = await compareFileVersions(fileId, versionA, versionB);
    setComparison(response);
    return response;
  };

  return { history, comparison, loading, error, compareVersions };
}
