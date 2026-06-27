export function SimilarityResults({ result }) {
  if (!result) {
    return null;
  }

  return (
    <section className="classification-results" aria-label="Similarity results">
      <div className="eda-summary-grid">
        <article className="eda-stat-card">
          <h3>Mode</h3>
          <p>{result.mode}</p>
        </article>
        <article className="eda-stat-card">
          <h3>Rows</h3>
          <p>{result.row_count}</p>
        </article>
        <article className="eda-stat-card">
          <h3>Items</h3>
          <p>{result.item_count}</p>
        </article>
      </div>

      <p className={result.suitable ? 'upload-help' : 'form-error'} role="status">
        {result.suitability_note}
      </p>

      {result.top_pairs.length > 0 && (
        <>
          <h3>Top similar pairs</h3>
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th scope="col">Left</th>
                  <th scope="col">Right</th>
                  <th scope="col">Score</th>
                </tr>
              </thead>
              <tbody>
                {result.top_pairs.map((pair) => (
                  <tr key={`${pair.left}-${pair.right}`}>
                    <td>{pair.left}</td>
                    <td>{pair.right}</td>
                    <td>{pair.score}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {result.similarity_matrix_preview.length > 0 && (
        <>
          <h3>Matrix preview</h3>
          <div className="table-scroll">
            <table className="data-table">
              <tbody>
                {result.similarity_matrix_preview.map((row) => (
                  <tr key={row.label}>
                    <th scope="row">{row.label}</th>
                    {row.values.map((value, index) => (
                      <td key={`${row.label}-${index}`}>{value}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}
