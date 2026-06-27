/**
 * ClusteringForm
 */
export function ClusteringForm({ algorithms, columns, suggestions, loading, onSubmit }) {
  const defaultFeatures =
    suggestions?.feature_columns?.slice(0, 4) ?? columns.slice(0, 3);

  return (
    <form
      className="regression-form"
      onSubmit={(event) => {
        event.preventDefault();
        const formData = new FormData(event.currentTarget);
        onSubmit({
          algorithm: formData.get('algorithm'),
          featureColumns: formData.getAll('feature_columns'),
          nClusters: Number(formData.get('n_clusters')),
          maxK: Number(formData.get('max_k')),
        });
      }}
    >
      <label htmlFor="clustering-algorithm">Algorithm</label>
      <select
        id="clustering-algorithm"
        name="algorithm"
        defaultValue={algorithms[0]?.id ?? 'kmeans'}
        required
      >
        {algorithms.map((algorithm) => (
          <option key={algorithm.id} value={algorithm.id}>
            {algorithm.label}
          </option>
        ))}
      </select>

      <fieldset>
        <legend>Feature columns</legend>
        <ul className="checkbox-list">
          {columns.map((column) => (
            <li key={column}>
              <label>
                <input
                  type="checkbox"
                  name="feature_columns"
                  value={column}
                  defaultChecked={defaultFeatures.includes(column)}
                />
                {column}
              </label>
            </li>
          ))}
        </ul>
      </fieldset>

      <label htmlFor="clustering-k">Number of clusters (k)</label>
      <input id="clustering-k" name="n_clusters" type="number" min="2" max="20" defaultValue="3" />

      <label htmlFor="clustering-max-k">Elbow plot max k</label>
      <input id="clustering-max-k" name="max_k" type="number" min="2" max="15" defaultValue="8" />

      <button type="submit" className="primary-button" disabled={loading || columns.length === 0}>
        {loading ? 'Clustering…' : 'Run clustering'}
      </button>
    </form>
  );
}
