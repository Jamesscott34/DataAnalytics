/**
 * ClassificationResults
 *
 * Metrics, confusion matrix, per-class report, and predictions.
 */
export function ClassificationResults({ result }) {
  if (!result) {
    return null;
  }

  const { labels, matrix, included, message, class_count: classCount } =
    result.confusion_matrix;
  const showMatrix = included !== false && labels.length > 0;

  return (
    <section className="classification-results" aria-label="Classification results">
      <div className="eda-summary-grid">
        <article className="eda-stat-card">
          <h3>Accuracy</h3>
          <p>{result.metrics.accuracy}</p>
        </article>
        <article className="eda-stat-card">
          <h3>Precision</h3>
          <p>{result.metrics.precision}</p>
        </article>
        <article className="eda-stat-card">
          <h3>Recall</h3>
          <p>{result.metrics.recall}</p>
        </article>
        <article className="eda-stat-card">
          <h3>F1</h3>
          <p>{result.metrics.f1}</p>
        </article>
      </div>

      <p className="upload-help">
        {result.algorithm} model predicting <strong>{result.target_column}</strong> from{' '}
        {result.feature_columns.join(', ')}.
      </p>

      <h3>Confusion matrix</h3>
      {showMatrix ? (
        <div className="table-scroll">
          <table className="data-table confusion-matrix-table">
            <thead>
              <tr>
                <th scope="col">Actual \ Predicted</th>
                {labels.map((label) => (
                  <th key={label} scope="col">
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {matrix.map((row, rowIndex) => (
                <tr key={labels[rowIndex]}>
                  <th scope="row">{labels[rowIndex]}</th>
                  {row.map((value, columnIndex) => (
                    <td key={`${rowIndex}-${columnIndex}`}>{value}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="upload-help">
          {message ||
            `Confusion matrix omitted (${classCount ?? labels.length} classes; too many to display usefully).`}
        </p>
      )}

      {result.classification_report.length > 0 && (
        <>
          <h3>Per-class report</h3>
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th scope="col">Class</th>
                  <th scope="col">Precision</th>
                  <th scope="col">Recall</th>
                  <th scope="col">F1</th>
                  <th scope="col">Support</th>
                </tr>
              </thead>
              <tbody>
                {result.classification_report.map((row) => (
                  <tr key={row.label}>
                    <th scope="row">{row.label}</th>
                    <td>{row.precision}</td>
                    <td>{row.recall}</td>
                    <td>{row.f1}</td>
                    <td>{row.support}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      <h3>Predictions</h3>
      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Actual</th>
              <th scope="col">Predicted</th>
              <th scope="col">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {result.predictions.map((row, index) => (
              <tr key={`${row.actual}-${row.predicted}-${index}`}>
                <td>{row.actual}</td>
                <td>{row.predicted}</td>
                <td>{row.confidence ?? 'n/a'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
