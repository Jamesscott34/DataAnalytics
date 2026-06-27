/**
 * PCAForm
 */
export function PCAForm({ columns, loading, onSubmit }) {
  return (
    <form
      className="regression-form"
      onSubmit={(event) => {
        event.preventDefault();
        const formData = new FormData(event.currentTarget);
        onSubmit({
          featureColumns: formData.getAll('feature_columns'),
          nComponents: Number(formData.get('n_components')),
        });
      }}
    >
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
                  defaultChecked={columns.indexOf(column) < 4}
                />
                {column}
              </label>
            </li>
          ))}
        </ul>
      </fieldset>

      <label htmlFor="pca-components">Components</label>
      <input id="pca-components" name="n_components" type="number" min="1" max="10" defaultValue="2" />

      <button type="submit" className="primary-button" disabled={loading || columns.length === 0}>
        {loading ? 'Running PCA…' : 'Run PCA'}
      </button>
    </form>
  );
}
