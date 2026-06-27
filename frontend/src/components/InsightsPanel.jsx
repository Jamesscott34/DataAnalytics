import { useInsights } from '../hooks/useInsights.js';

export function InsightsPanel({ resultId, analysisType }) {
  const { insight, loading, error, generate } = useInsights();

  if (!resultId) {
    return null;
  }

  return (
    <section className="panel-card panel-card--nested" aria-label="AI insights">
      <div className="panel-card-header">
        <h3>AI insights</h3>
        <button
          type="button"
          className="secondary-button"
          disabled={loading}
          onClick={() => generate({ resultId, analysisType })}
        >
          {loading ? 'Generating…' : 'Generate summary'}
        </button>
      </div>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      {insight ? (
        <p className="upload-help">
          {insight.summary} <strong>Source:</strong> {insight.source}.
        </p>
      ) : (
        <p className="upload-help">
          Generate a stored plain-English summary for this analysis result.
        </p>
      )}
    </section>
  );
}
