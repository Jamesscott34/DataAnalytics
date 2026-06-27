/**
 * CorrelationHeatmap — numeric correlation matrix for EDA.
 */
export function CorrelationHeatmap({ labels = [], matrix = [] }) {
  if (!labels.length || !matrix.length) {
    return null;
  }

  const size = labels.length;
  const flatValues = matrix.flat();
  const minValue = Math.min(...flatValues, -1);
  const maxValue = Math.max(...flatValues, 1);

  const colorFor = (value) => {
    const normalized = (value - minValue) / (maxValue - minValue || 1);
    const red = Math.round(255 * normalized);
    const blue = Math.round(255 * (1 - normalized));
    return `rgb(${red}, 80, ${blue})`;
  };

  return (
    <figure className="chart-card" aria-label="Correlation heatmap">
      <figcaption>Correlation heatmap</figcaption>
      <div
        className="matrix-heatmap"
        role="grid"
        aria-label="Correlation matrix heatmap"
      >
        <div className="matrix-heatmap-row" role="row">
          <strong role="columnheader" />
          {labels.map((label) => (
            <strong key={label} role="columnheader">
              {label}
            </strong>
          ))}
        </div>
        {matrix.map((row, rowIndex) => (
          <div key={labels[rowIndex]} className="matrix-heatmap-row" role="row">
            <strong role="rowheader">{labels[rowIndex]}</strong>
            {row.map((value, columnIndex) => (
              <span
                key={`${rowIndex}-${columnIndex}`}
                className="matrix-heatmap-cell"
                role="gridcell"
                style={{ backgroundColor: colorFor(value) }}
                title={`${labels[rowIndex]} vs ${labels[columnIndex]}: ${value}`}
              >
                {value.toFixed(2)}
              </span>
            ))}
          </div>
        ))}
      </div>
    </figure>
  );
}
