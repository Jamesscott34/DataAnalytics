import { ForecastChart } from './charts/ForecastChart.jsx';

/**
 * TimeSeriesResults
 */
export function TimeSeriesResults({ result }) {
  if (!result) {
    return null;
  }

  return (
    <section className="classification-results" aria-label="Time series results">
      <div className="eda-summary-grid">
        <article className="eda-stat-card">
          <h3>Rows</h3>
          <p>{result.row_count}</p>
        </article>
        <article className="eda-stat-card">
          <h3>Train / test</h3>
          <p>
            {result.train_rows} / {result.test_rows}
          </p>
        </article>
        <article className="eda-stat-card">
          <h3>MAE</h3>
          <p>{result.metrics.mae.toFixed(3)}</p>
        </article>
        <article className="eda-stat-card">
          <h3>RMSE</h3>
          <p>{result.metrics.rmse.toFixed(3)}</p>
        </article>
        <article className="eda-stat-card">
          <h3>MAPE</h3>
          <p>{result.metrics.mape != null ? `${result.metrics.mape.toFixed(1)}%` : 'n/a'}</p>
        </article>
      </div>

      <p className="upload-help">
        {result.algorithm} on {result.date_column} and {result.value_column}.
      </p>

      <ForecastChart
        title="Actual vs forecast"
        history={result.history}
        forecast={result.forecast}
      />

      <h3>Forecast table</h3>
      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Period</th>
              <th scope="col">Actual</th>
              <th scope="col">Forecast</th>
            </tr>
          </thead>
          <tbody>
            {[...result.history, ...result.forecast].map((point) => (
              <tr key={point.label}>
                <th scope="row">{point.label}</th>
                <td>{point.actual != null ? point.actual.toFixed(2) : 'n/a'}</td>
                <td>{point.forecast != null ? point.forecast.toFixed(2) : 'n/a'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
