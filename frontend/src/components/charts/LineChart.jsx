/**
 * LineChart — time series or ordered numeric line chart for EDA.
 */
export function LineChart({ title, xColumn, yColumn, points = [] }) {
  if (!points.length) {
    return null;
  }

  const width = 640;
  const height = 240;
  const padding = { top: 16, right: 16, bottom: 40, left: 48 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const yValues = points.map((point) => point.y);
  const minY = Math.min(...yValues);
  const maxY = Math.max(...yValues);
  const yRange = maxY - minY || 1;
  const xForIndex = (index) =>
    padding.left + (index / Math.max(points.length - 1, 1)) * plotWidth;
  const yFor = (value) =>
    padding.top + plotHeight - ((value - minY) / yRange) * plotHeight;
  const path = points
    .map(
      (point, index) =>
        `${index === 0 ? 'M' : 'L'}${xForIndex(index)},${yFor(point.y)}`,
    )
    .join(' ');

  return (
    <figure
      className="chart-card forecast-chart"
      aria-label={`Line chart for ${title}`}
    >
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
        <path d={path} className="forecast-line forecast-line--actual" />
        <text x={padding.left} y={height - 8} className="forecast-label">
          {points[0]?.x}
        </text>
        <text
          x={width - padding.right}
          y={height - 8}
          textAnchor="end"
          className="forecast-label"
        >
          {points[points.length - 1]?.x}
        </text>
        <text x={8} y={padding.top + 8} className="forecast-label">
          {yColumn || xColumn}
        </text>
      </svg>
    </figure>
  );
}
