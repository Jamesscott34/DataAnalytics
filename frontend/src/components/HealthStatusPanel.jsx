import { useHealth } from '../hooks/useHealth.js';

/**
 * HealthStatusPanel
 *
 * Displays backend API liveness status with loading and error states.
 *
 * @param {Object} [props]
 * @param {string} [props.title] - Heading shown above the status indicator.
 */
export function HealthStatusPanel({ title = 'API Health' }) {
  const { status, loading, error, reload } = useHealth();

  return (
    <section aria-labelledby="health-status-heading" className="health-panel">
      <h2 id="health-status-heading">{title}</h2>

      {loading && (
        <p role="status" aria-live="polite">
          Checking backend health…
        </p>
      )}

      {!loading && error && (
        <div role="alert">
          <p>Unable to reach the API: {error}</p>
          <button type="button" onClick={reload} aria-label="Retry health check">
            Retry
          </button>
        </div>
      )}

      {!loading && !error && (
        <p>
          Status:{' '}
          <span
            className={`health-badge health-badge--${status}`}
            aria-label={`API status ${status}`}
          >
            {status}
          </span>
        </p>
      )}
    </section>
  );
}
