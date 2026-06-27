import { BarChart } from './charts/BarChart.jsx';

/**
 * PCAResults
 */
export function PCAResults({ result }) {
  if (!result) {
    return null;
  }

  const varianceValues = result.components.map((component) => ({
    value: component.name,
    count: Math.round(component.explained_variance_ratio * 1000) / 10,
  }));

  return (
    <section className="classification-results" aria-label="PCA results">
      <div className="eda-summary-grid">
        <article className="eda-stat-card">
          <h3>Rows</h3>
          <p>{result.row_count}</p>
        </article>
        <article className="eda-stat-card">
          <h3>Components</h3>
          <p>{result.n_components}</p>
        </article>
        <article className="eda-stat-card">
          <h3>Total variance</h3>
          <p>{Math.round(result.total_explained_variance * 1000) / 10}%</p>
        </article>
      </div>

      <BarChart title="Explained variance (%)" values={varianceValues} />

      <h3>Top loadings</h3>
      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Component</th>
              <th scope="col">Feature</th>
              <th scope="col">Weight</th>
            </tr>
          </thead>
          <tbody>
            {result.components.flatMap((component) =>
              component.loadings.slice(0, 3).map((loading) => (
                <tr key={`${component.name}-${loading.feature}`}>
                  <th scope="row">{component.name}</th>
                  <td>{loading.feature}</td>
                  <td>{loading.weight}</td>
                </tr>
              )),
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
