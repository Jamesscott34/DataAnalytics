/**
 * ScatterChart — pairwise numeric scatter plot for EDA.
 */
export function ScatterChart({ title, xColumn, yColumn, points = [] }) {
  if (!points.length) {
    return null;
  }

  const width = 420;
  const height = 260;
  const padding = { top: 16, right: 16, bottom: 40, left: 48 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const xValues = points.map((point) => point.x);
  const yValues = points.map((point) => point.y);
  const minX = Math.min(...xValues);
  const maxX = Math.max(...xValues);
  const minY = Math.min(...yValues);
  const maxY = Math.max(...yValues);
  const xRange = maxX - minX || 1;
  const yRange = maxY - minY || 1;
  const xFor = (value) => padding.left + ((value - minX) / xRange) * plotWidth;
  const yFor = (value) =>
    padding.top + plotHeight - ((value - minY) / yRange) * plotHeight;

  return (
    <figure className="chart-card" aria-label={`Scatter plot for ${title}`}>
      <figcaption>{title}</figcaption>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={title}>
        <line
          x1={padding.left}
          y1={padding.top + plotHeight}
          x2={width - padding.right}
          y2={padding.top + plotHeight}
          className="forecast-axis"
        />
        <line
          x1={padding.left}
          y1={padding.top}
          x2={padding.left}
          y2={padding.top + plotHeight}
          className="forecast-axis"
        />
        {points.map((point, index) => (
          <circle
            key={`${point.x}-${point.y}-${index}`}
            cx={xFor(point.x)}
            cy={yFor(point.y)}
            r={3}
            className="scatter-point"
          />
        ))}
        <text x={padding.left} y={height - 8} className="forecast-label">
          {xColumn}
        </text>
        <text
          x={width - padding.right}
          y={padding.top + 12}
          textAnchor="end"
          className="forecast-label"
        >
          {yColumn}
        </text>
      </svg>
    </figure>
  );
}
