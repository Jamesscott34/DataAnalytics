export function ConfusionMatrixChart({ labels = [], matrix = [] }) {
  if (!labels.length || !matrix.length) {
    return null;
  }

  const maxValue = Math.max(...matrix.flat(), 1);

  return (
    <figure className="chart-card" aria-label="Confusion matrix heatmap">
      <figcaption>Confusion matrix heatmap</figcaption>
      <div
        className="matrix-heatmap"
        style={{
          gridTemplateColumns: `repeat(${labels.length + 1}, minmax(3rem, 1fr))`,
        }}
      >
        <span />
        {labels.map((label) => (
          <strong key={`predicted-${label}`}>{label}</strong>
        ))}
        {matrix.map((row, rowIndex) => (
          <FragmentRow
            key={labels[rowIndex]}
            label={labels[rowIndex]}
            row={row}
            maxValue={maxValue}
            rowIndex={rowIndex}
          />
        ))}
      </div>
    </figure>
  );
}

function FragmentRow({ label, row, maxValue, rowIndex }) {
  return (
    <>
      <strong>{label}</strong>
      {row.map((value, columnIndex) => (
        <span
          key={`${rowIndex}-${columnIndex}`}
          className="matrix-heatmap-cell"
          style={{ opacity: 0.25 + (value / maxValue) * 0.75 }}
        >
          {value}
        </span>
      ))}
    </>
  );
}
