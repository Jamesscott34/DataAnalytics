import { BarChart } from './charts/BarChart.jsx';

/**
 * RegressionResults
 *
 * Metrics, actual vs predicted table, and feature importance.
 */
export function RegressionResults({ result }) {
  if (!result) {
    return null;
  }

  const importanceValues = result.feature_importance.map((item) => ({
    value: item.feature,
    count: item.importance,
  }));

  return (
    <section className="regression-results" aria-label="Regression results">
      <div className="eda-summary-grid">
        <article className="eda-stat-card">
          <h3>MAE</h3>
          <p>{result.metrics.mae}</p>
        </article>
        <article className="eda-stat-card">
          <h3>RMSE</h3>
          <p>{result.metrics.rmse}</p>
        </article>
        <article className="eda-stat-card">
          <h3>R²</h3>
          <p>{result.metrics.r2}</p>
        </article>
        <article className="eda-stat-card">
          <h3>Test rows</h3>
          <p>{result.test_rows}</p>
        </article>
      </div>

      <p className="upload-help">
        {result.algorithm} model predicting <strong>{result.target_column}</strong> from{' '}
        {result.feature_columns.join(', ')}.
      </p>

      {importanceValues.length > 0 && (
        <BarChart title="Feature importance" values={importanceValues} />
      )}

      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Actual</th>
              <th scope="col">Predicted</th>
              <th scope="col">Residual</th>
            </tr>
          </thead>
          <tbody>
            {result.actual_vs_predicted.map((row, index) => (
              <tr key={`${row.actual}-${row.predicted}-${index}`}>
                <td>{row.actual}</td>
                <td>{row.predicted}</td>
                <td>{result.residuals[index]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
