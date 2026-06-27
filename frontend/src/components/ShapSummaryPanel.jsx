export function ShapSummaryPanel({ explainability, confidenceSummary }) {
  return (
    <section className="panel-card panel-card--nested" aria-label="Explainability summary">
      <h3>Explainability</h3>
      {explainability?.notes && <p className="upload-help">{explainability.notes}</p>}
      <p className="upload-help">
        SHAP values are not computed in this local build. Use feature importance and
        confidence scores as fallback explanations.
      </p>
      {confidenceSummary && (
        <p className="upload-help">
          Confidence: average {confidenceSummary.average}, min {confidenceSummary.minimum},
          max {confidenceSummary.maximum}.
        </p>
      )}
    </section>
  );
}
