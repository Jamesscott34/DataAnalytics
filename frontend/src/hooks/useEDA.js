import { useCallback, useRef, useState } from 'react';
import { getEda, getEdaSuggestions, runEda } from '../api/eda.js';
import { getJob } from '../api/jobs.js';

const POLL_INTERVAL_MS = 1500;

function sleep(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

/**
 * useEDA
 *
 * Runs exploratory data analysis for an uploaded file.
 * Large files are processed via background jobs with progress polling.
 *
 * @param {number | null} fileId
 */
export function useEDA(fileId) {
  const [eda, setEda] = useState(null);
  const [suggestions, setSuggestions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [jobProgress, setJobProgress] = useState(null);
  const cancelRef = useRef(false);

  const analyze = useCallback(
    async (forceRefresh = false, forceBackground = false) => {
      if (!fileId) {
        return;
      }
      cancelRef.current = false;
      setLoading(true);
      setError(null);
      setJobProgress(null);
      try {
        const response = await runEda(fileId, { forceRefresh, forceBackground });
        if (response?.async_job && response.job_id) {
          setJobProgress({ jobId: response.job_id, progress: 0, status: 'queued' });
          let job = await getJob(response.job_id);
          while (
            !cancelRef.current &&
            !['complete', 'failed', 'cancelled'].includes(job.status)
          ) {
            setJobProgress({
              jobId: job.id,
              progress: job.progress,
              status: job.status,
            });
            await sleep(POLL_INTERVAL_MS);
            job = await getJob(response.job_id);
          }
          if (cancelRef.current) {
            return;
          }
          setJobProgress({
            jobId: job.id,
            progress: job.progress,
            status: job.status,
          });
          if (job.status !== 'complete') {
            throw new Error(job.error ?? 'Background EDA failed');
          }
        } else {
          setEda(response);
        }
        const suggestionResponse = await getEdaSuggestions(fileId);
        setSuggestions(suggestionResponse);
        if (response?.async_job) {
          const edaResponse = await getEda(fileId);
          if (!edaResponse) {
            throw new Error('EDA completed but cached results are not available yet');
          }
          setEda(edaResponse);
        }
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

  const cancel = useCallback(() => {
    cancelRef.current = true;
  }, []);

  return {
    eda,
    suggestions,
    loading,
    error,
    jobProgress,
    analyze,
    cancel,
  };
}
