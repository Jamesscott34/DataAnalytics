/**
 * RegressionForm
 *
 * Configure algorithm, target column, and feature columns.
 */
export function RegressionForm({
  algorithms,
  columns,
  suggestions,
  loading,
  onSubmit,
}) {
  const defaultTarget = suggestions?.target_columns?.[0] ?? columns[0] ?? '';
  const defaultFeatures =
    suggestions?.feature_columns?.filter((name) => name !== defaultTarget) ??
    columns.filter((name) => name !== defaultTarget).slice(0, 3);

  return (
    <form
      className="regression-form"
      onSubmit={(event) => {
        event.preventDefault();
        const formData = new FormData(event.currentTarget);
        const algorithm = formData.get('algorithm');
        const targetColumn = formData.get('target_column');
        const featureColumns = formData.getAll('feature_columns');
        const testSize = Number(formData.get('test_size'));
        onSubmit({
          algorithm,
          targetColumn,
          featureColumns,
          testSize: Number.isFinite(testSize) ? testSize : 0.2,
        });
      }}
    >
      <label htmlFor="regression-algorithm">Algorithm</label>
      <select
        id="regression-algorithm"
        name="algorithm"
        defaultValue={algorithms[0]?.id ?? 'linear'}
        required
      >
        {algorithms.map((algorithm) => (
          <option key={algorithm.id} value={algorithm.id}>
            {algorithm.label}
          </option>
        ))}
      </select>

      <label htmlFor="regression-target">Target column</label>
      <select
        id="regression-target"
        name="target_column"
        defaultValue={defaultTarget}
        required
      >
        {columns.map((column) => (
          <option key={column} value={column}>
            {column}
          </option>
        ))}
      </select>

      <fieldset>
        <legend>Feature columns</legend>
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

      <label htmlFor="regression-test-size">Test split</label>
      <input
        id="regression-test-size"
        name="test_size"
        type="number"
        min="0.1"
        max="0.5"
        step="0.05"
        defaultValue="0.2"
      />

      <button type="submit" className="primary-button" disabled={loading || columns.length === 0}>
        {loading ? 'Training…' : 'Train regression model'}
      </button>
    </form>
  );
}
