/**
 * ForecastChart
 *
 * SVG line chart comparing actual history and forecast values.
 */
export function ForecastChart({ title = 'Forecast', history = [], forecast = [] }) {
  const points = [
    ...history.map((point) => ({
      label: point.label,
      actual: point.actual,
      forecast: point.forecast,
      kind: 'history',
    })),
    ...forecast.map((point) => ({
      label: point.label,
      actual: point.actual,
      forecast: point.forecast,
      kind: 'forecast',
    })),
  ];

  if (!points.length) {
    return null;
  }

  const width = 640;
  const height = 240;
  const padding = { top: 16, right: 16, bottom: 40, left: 48 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

  const values = points.flatMap((point) =>
    [point.actual, point.forecast].filter((value) => value != null),
  );
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const valueRange = maxValue - minValue || 1;

  const xForIndex = (index) =>
    padding.left + (index / Math.max(points.length - 1, 1)) * plotWidth;
  const yForValue = (value) =>
    padding.top + plotHeight - ((value - minValue) / valueRange) * plotHeight;

  const actualPath = points
    .filter((point) => point.actual != null)
    .map((point, index) => {
      const pointIndex = points.indexOf(point);
      const command = index === 0 ? 'M' : 'L';
      return `${command}${xForIndex(pointIndex)},${yForValue(point.actual)}`;
    })
    .join(' ');

  const forecastPath = points
    .filter((point) => point.forecast != null)
    .map((point, index) => {
      const pointIndex = points.indexOf(point);
      const command = index === 0 ? 'M' : 'L';
      return `${command}${xForIndex(pointIndex)},${yForValue(point.forecast)}`;
    })
    .join(' ');

  const firstForecastIndex = points.findIndex((point) => point.kind === 'forecast');

  return (
    <figure
      className="chart-card forecast-chart"
      aria-label={`Line chart for ${title}`}
    >
      <figcaption>{title}</figcaption>
      <svg
        className="forecast-chart-svg"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`${title} actual vs forecast`}
      >
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
        {firstForecastIndex >= 0 && (
          <line
            x1={xForIndex(firstForecastIndex)}
            y1={padding.top}
            x2={xForIndex(firstForecastIndex)}
            y2={padding.top + plotHeight}
            className="forecast-divider"
          />
        )}
        {actualPath && (
          <path d={actualPath} className="forecast-line forecast-line--actual" />
        )}
        {forecastPath && (
          <path d={forecastPath} className="forecast-line forecast-line--forecast" />
        )}
        <text x={padding.left} y={height - 8} className="forecast-label">
          {points[0]?.label}
        </text>
        <text
          x={width - padding.right}
          y={height - 8}
          textAnchor="end"
          className="forecast-label"
        >
          {points[points.length - 1]?.label}
        </text>
        <text x={8} y={padding.top + 8} className="forecast-label">
          {maxValue.toFixed(1)}
        </text>
        <text x={8} y={padding.top + plotHeight} className="forecast-label">
          {minValue.toFixed(1)}
        </text>
      </svg>
      <div className="forecast-legend" aria-hidden="true">
        <span className="forecast-legend-item forecast-legend-item--actual">
          Actual
        </span>
        <span className="forecast-legend-item forecast-legend-item--forecast">
          Forecast
        </span>
      </div>
    </figure>
  );
}
