/**
 * MissingValuesChart
 *
 * Bar chart of missing-value percentages per column.
 */
export function MissingValuesChart({ columns = [] }) {
  const withMissing = columns
    .filter((column) => column.missing_percent > 0)
    .sort((a, b) => b.missing_percent - a.missing_percent);

  if (!withMissing.length) {
    return (
      <figure className="chart-card">
        <figcaption>Missing values</figcaption>
        <p className="chart-empty">No missing values detected.</p>
      </figure>
    );
  }

  const maxPercent = Math.max(...withMissing.map((column) => column.missing_percent), 1);

  return (
    <figure className="chart-card" aria-label="Missing values by column">
      <figcaption>Missing values by column</figcaption>
      <div className="bar-chart">
        {withMissing.map((column) => (
          <div key={column.name} className="bar-chart-row">
            <span className="bar-chart-label" title={column.name}>
              {column.name}
            </span>
            <div className="bar-chart-track" aria-hidden="true">
              <div
                className="bar-chart-fill bar-chart-fill--warning"
                style={{ width: `${(column.missing_percent / maxPercent) * 100}%` }}
              />
            </div>
            <span className="bar-chart-count">{column.missing_percent.toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </figure>
  );
}
