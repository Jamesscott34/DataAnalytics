import { BarChart } from './charts/BarChart.jsx';

/**
 * ClusteringResults
 */
export function ClusteringResults({ result }) {
  if (!result) {
    return null;
  }

  const elbowValues = result.elbow.map((point) => ({
    value: `k=${point.k}`,
    count: point.inertia,
  }));

  return (
    <section className="classification-results" aria-label="Clustering results">
      <div className="eda-summary-grid">
        <article className="eda-stat-card">
          <h3>Rows</h3>
          <p>{result.row_count}</p>
        </article>
        <article className="eda-stat-card">
          <h3>Clusters</h3>
          <p>{result.n_clusters}</p>
        </article>
        <article className="eda-stat-card">
          <h3>Silhouette</h3>
          <p>{result.silhouette ?? 'n/a'}</p>
        </article>
      </div>

      <p className="upload-help">
        {result.algorithm} on {result.feature_columns.join(', ')}.
      </p>

      <BarChart title="Elbow plot (inertia vs k)" values={elbowValues} />

      <h3>Cluster sizes</h3>
      <ul className="file-list">
        {Object.entries(result.cluster_sizes).map(([cluster, size]) => (
          <li key={cluster}>
            Cluster {cluster}: <strong>{size}</strong> rows
          </li>
        ))}
      </ul>
    </section>
  );
}
