import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { cancelJob, createJob, getJob, listJobs } from '../api/jobs.js';

const TERMINAL_STATUSES = new Set(['complete', 'failed', 'cancelled']);

export function JobProgressPage() {
  const navigate = useNavigate();
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (jobId) {
      return undefined;
    }
    let active = true;
    listJobs()
      .then((response) => {
        if (active) {
          setJobs(response.items ?? []);
        }
      })
      .catch((err) => {
        if (active) {
          setError(err.message);
        }
      });
    return () => {
      active = false;
    };
  }, [jobId]);

  useEffect(() => {
    if (!jobId) {
      return undefined;
    }
    let active = true;
    let timerId = null;

    const poll = async () => {
      try {
        const response = await getJob(jobId);
        if (!active) {
          return;
        }
        setJob(response);
        setError(null);
        if (!TERMINAL_STATUSES.has(response.status)) {
          timerId = window.setTimeout(poll, 1000);
        }
      } catch (err) {
        if (active) {
          setError(err.message);
        }
      }
    };

    poll();
    return () => {
      active = false;
      if (timerId) {
        window.clearTimeout(timerId);
      }
    };
  }, [jobId]);

  const startDemo = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await createJob({ jobType: 'demo' });
      navigate(`/jobs/${response.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const cancelCurrent = async () => {
    if (!job) {
      return;
    }
    setLoading(true);
    try {
      setJob(await cancelJob(job.id));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page-shell page-shell--wide">
      <header className="page-header">
        <h1>Background jobs</h1>
        <p className="page-lead">Queue long-running analysis work and monitor progress.</p>
      </header>

      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}

      {!jobId && (
        <section className="panel-card">
          <button type="button" className="primary-button" disabled={loading} onClick={startDemo}>
            {loading ? 'Queueing…' : 'Start demo job'}
          </button>
          {jobs.length > 0 && (
            <>
              <h2>Recent jobs</h2>
              <ul className="file-list">
                {jobs.map((item) => (
                  <li key={item.id}>
                    <span>
                      {item.job_type}: {item.status} ({item.progress}%)
                    </span>
                    <Link to={`/jobs/${item.id}`}>View progress</Link>
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>
      )}

      {jobId && job && (
        <section className="panel-card" aria-label="Job progress">
          <div className="panel-card-header">
            <div>
              <h2>{job.job_type}</h2>
              <p className="page-meta">{job.id}</p>
            </div>
            {!TERMINAL_STATUSES.has(job.status) && (
              <button
                type="button"
                className="secondary-button"
                disabled={loading}
                onClick={cancelCurrent}
              >
                Cancel job
              </button>
            )}
          </div>
          <p className="upload-help">Status: {job.status}</p>
          <div className="job-progress-track" aria-label={`Job progress ${job.progress}%`}>
            <div className="job-progress-fill" style={{ width: `${job.progress}%` }} />
          </div>
          {job.result_id && <p className="upload-help">Result ID: {job.result_id}</p>}
          {job.error && (
            <p className="form-error" role="status">
              {job.error}
            </p>
          )}
        </section>
      )}
    </main>
  );
}
