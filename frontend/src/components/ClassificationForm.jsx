/**
 * ClassificationForm
 *
 * Configure algorithm, target column, and feature columns.
 */
export function ClassificationForm({
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
      <label htmlFor="classification-algorithm">Algorithm</label>
      <select
        id="classification-algorithm"
        name="algorithm"
        defaultValue={algorithms[0]?.id ?? 'logistic'}
        required
      >
        {algorithms.map((algorithm) => (
          <option key={algorithm.id} value={algorithm.id}>
            {algorithm.label}
          </option>
        ))}
      </select>

      <label htmlFor="classification-target">Target column</label>
      <select
        id="classification-target"
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

      <label htmlFor="classification-test-size">Test split</label>
      <input
        id="classification-test-size"
        name="test_size"
        type="number"
        min="0.1"
        max="0.5"
        step="0.05"
        defaultValue="0.2"
      />

      <button type="submit" className="primary-button" disabled={loading || columns.length === 0}>
        {loading ? 'Training…' : 'Train classification model'}
      </button>
    </form>
  );
}
