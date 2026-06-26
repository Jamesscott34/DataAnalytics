/**
 * HistogramChart
 *
 * Simple column histogram for numeric columns.
 */
export function HistogramChart({ title, bins = [] }) {
  if (!bins.length) {
    return null;
  }

  const maxCount = Math.max(...bins.map((bin) => bin.count), 1);

  return (
    <figure className="chart-card" aria-label={`Histogram for ${title}`}>
      <figcaption>{title}</figcaption>
      <div className="histogram-chart" role="img">
        {bins.map((bin) => (
          <div
            key={`${bin.start}-${bin.end}`}
            className="histogram-bar"
            style={{ height: `${(bin.count / maxCount) * 100}%` }}
            title={`${bin.start} – ${bin.end}: ${bin.count}`}
          >
            <span className="histogram-count">{bin.count}</span>
          </div>
        ))}
      </div>
      <div className="histogram-axis" aria-hidden="true">
        <span>{bins[0]?.start}</span>
        <span>{bins[bins.length - 1]?.end}</span>
      </div>
    </figure>
  );
}
