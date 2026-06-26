/**
 * BarChart
 *
 * Simple horizontal bar chart for categorical column frequencies.
 */
export function BarChart({ title, values = [] }) {
  if (!values.length) {
    return null;
  }

  const maxCount = Math.max(...values.map((item) => item.count), 1);

  return (
    <figure className="chart-card" aria-label={`Bar chart for ${title}`}>
      <figcaption>{title}</figcaption>
      <div className="bar-chart">
        {values.map((item) => (
          <div key={item.value} className="bar-chart-row">
            <span className="bar-chart-label" title={item.value}>
              {item.value}
            </span>
            <div className="bar-chart-track" aria-hidden="true">
              <div
                className="bar-chart-fill"
                style={{ width: `${(item.count / maxCount) * 100}%` }}
              />
            </div>
            <span className="bar-chart-count">{item.count}</span>
          </div>
        ))}
      </div>
    </figure>
  );
}
