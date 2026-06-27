export function SimilarityForm({ columns, loading, onSubmit }) {
  const defaultFeatures = columns.slice(0, 4);

  return (
    <form
      className="regression-form"
      onSubmit={(event) => {
        event.preventDefault();
        const formData = new FormData(event.currentTarget);
        onSubmit({
          mode: formData.get('mode'),
          idColumn: formData.get('id_column'),
          featureColumns: formData.getAll('feature_columns'),
          topN: Number(formData.get('top_n')),
        });
      }}
    >
      <label htmlFor="similarity-mode">Similarity mode</label>
      <select id="similarity-mode" name="mode" defaultValue="row">
        <option value="row">Rows</option>
        <option value="item">Items / columns</option>
      </select>

      <label htmlFor="similarity-id-column">Optional label column</label>
      <select id="similarity-id-column" name="id_column" defaultValue="">
        <option value="">Use row numbers</option>
        {columns.map((column) => (
          <option key={column} value={column}>
            {column}
          </option>
        ))}
      </select>

      <fieldset>
        <legend>Numeric feature columns</legend>
        {columns.length === 0 ? (
          <p>No columns loaded yet.</p>
        ) : (
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
        )}
      </fieldset>

      <label htmlFor="similarity-top-n">Top pairs</label>
      <input id="similarity-top-n" name="top_n" type="number" min="1" max="50" defaultValue="10" />

      <button type="submit" className="primary-button" disabled={loading || columns.length === 0}>
        {loading ? 'Analyzing…' : 'Run similarity'}
      </button>
    </form>
  );
}
