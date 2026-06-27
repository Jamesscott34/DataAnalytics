import { useEffect, useMemo, useRef, useState } from 'react';
import {
  applyRegressionServerError,
  buildRegressionFeatureSelection,
  formatRegressionColumnNotice,
  isNumericRegressionTarget,
  pickNumericTargets,
  sanitizeRegressionFeatures,
} from '../utils/regressionColumnRules.js';

/**
 * RegressionForm
 *
 * Configure algorithm, numeric target column, and feature columns.
 */
export function RegressionForm({
  algorithms,
  columns,
  columnMeta = [],
  suggestions,
  loading,
  serverError,
  onClearServerError,
  onSubmit,
}) {
  const numericTargets = useMemo(
    () => pickNumericTargets(columns, columnMeta),
    [columns, columnMeta],
  );
  const defaultTarget = numericTargets[numericTargets.length - 1] ?? columns[0] ?? '';
  const [targetColumn, setTargetColumn] = useState(defaultTarget);
  const [selectedFeatures, setSelectedFeatures] = useState([]);
  const [formError, setFormError] = useState(null);
  const [columnNotice, setColumnNotice] = useState(null);
  const lastHandledError = useRef(null);
  const selectionKey = useRef('');

  useEffect(() => {
    if (numericTargets.length === 0) {
      return;
    }
    if (!numericTargets.includes(targetColumn)) {
      setTargetColumn(numericTargets[numericTargets.length - 1]);
    }
  }, [numericTargets, targetColumn]);

  useEffect(() => {
    if (!columns.length) {
      setSelectedFeatures([]);
      setColumnNotice(null);
      selectionKey.current = '';
      return;
    }

    const nextKey = `${columns.join('|')}:${targetColumn}`;
    if (selectionKey.current === nextKey) {
      return;
    }
    selectionKey.current = nextKey;

    const { selected, removed } = buildRegressionFeatureSelection({
      columns,
      columnMeta,
      targetColumn,
      suggestions,
    });
    setSelectedFeatures(selected);
    setColumnNotice(
      removed.length ? formatRegressionColumnNotice(removed) : null,
    );
  }, [columns, columnMeta, suggestions, targetColumn]);

  useEffect(() => {
    if (!serverError || serverError === lastHandledError.current) {
      return;
    }
    lastHandledError.current = serverError;

    setSelectedFeatures((current) => {
      const { features, removed, userMessage } = applyRegressionServerError(
        serverError,
        current,
        targetColumn,
        columnMeta,
      );

      if (removed.length) {
        setColumnNotice(userMessage);
      }
      setFormError(serverError);
      onClearServerError?.();
      return features;
    });
  }, [serverError, targetColumn, columnMeta, onClearServerError]);

  const toggleFeature = (column, checked) => {
    setFormError(null);
    if (checked) {
      setSelectedFeatures((current) => (current.includes(column) ? current : [...current, column]));
      return;
    }
    setSelectedFeatures((current) => current.filter((name) => name !== column));
  };

  const handleTargetChange = (nextTarget) => {
    setTargetColumn(nextTarget);
    setFormError(null);
    setSelectedFeatures((current) => {
      const filtered = current.filter((name) => name !== nextTarget);
      const { removed } = sanitizeRegressionFeatures(filtered, nextTarget, columnMeta);
      if (removed.length) {
        setColumnNotice(formatRegressionColumnNotice(removed));
      }
      return filtered;
    });
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    setFormError(null);
    lastHandledError.current = null;

    const formData = new FormData(event.currentTarget);
    const algorithm = formData.get('algorithm');
    const testSize = Number(formData.get('test_size'));

    if (!isNumericRegressionTarget(columnMeta, targetColumn)) {
      setFormError('Regression target must be a numeric column (integer or float).');
      return;
    }

    const { selected, removed } = sanitizeRegressionFeatures(
      selectedFeatures,
      targetColumn,
      columnMeta,
    );

    if (removed.length) {
      setSelectedFeatures(selected);
      setColumnNotice(formatRegressionColumnNotice(removed));
    }

    if (selected.length === 0) {
      setFormError('Select at least one feature column other than the target.');
      return;
    }

    onSubmit({
      algorithm,
      targetColumn,
      featureColumns: selected,
      testSize: Number.isFinite(testSize) ? testSize : 0.2,
    });
  };

  return (
    <form className="regression-form" onSubmit={handleSubmit}>
      {numericTargets.length === 0 && (
        <p className="form-error" role="alert">
          This dataset has no numeric columns suitable for regression. Pick a different file
          or use classification instead.
        </p>
      )}

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

      <label htmlFor="regression-target">Target column (numeric)</label>
      <select
        id="regression-target"
        name="target_column"
        value={targetColumn}
        onChange={(event) => handleTargetChange(event.target.value)}
        required
      >
        {numericTargets.length > 0 ? (
          numericTargets.map((column) => (
            <option key={column} value={column}>
              {column}
            </option>
          ))
        ) : (
          columns.map((column) => (
            <option key={column} value={column}>
              {column}
            </option>
          ))
        )}
      </select>
      <p className="upload-help">
        Predict a numeric value such as price or revenue. Categorical columns like region or
        carrier belong in classification, not regression.
      </p>

      <fieldset>
        <legend>Feature columns</legend>
        {columns.length === 0 ? (
          <p>No columns loaded yet.</p>
        ) : (
          <ul className="checkbox-list">
            {columns.map((column) => {
              const meta = columnMeta.find((item) => item.name === column);
              const issues = meta
                ? [
                    ...(column === targetColumn ? ['target column'] : []),
                    ...(meta.missing_percent >= 50
                      ? [`${Math.round(meta.missing_percent)}% missing`]
                      : []),
                    ...(meta.unique_count <= 1 ? ['constant'] : []),
                  ]
                : [];

              return (
                <li key={column}>
                  <label>
                    <input
                      type="checkbox"
                      name="feature_columns"
                      value={column}
                      checked={selectedFeatures.includes(column)}
                      disabled={column === targetColumn}
                      onChange={(event) => toggleFeature(column, event.target.checked)}
                    />
                    {column}
                    {column === targetColumn ? ' (target)' : ''}
                    {issues.length > 0 && column !== targetColumn ? (
                      <span className="upload-help"> · {issues.join(', ')}</span>
                    ) : null}
                  </label>
                </li>
              );
            })}
          </ul>
        )}
      </fieldset>

      {columnNotice && (
        <p className="upload-help" role="status">
          {columnNotice}
        </p>
      )}

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

      {formError && (
        <p className="form-error" role="alert">
          {formError}
        </p>
      )}

      <button
        type="submit"
        className="primary-button"
        disabled={loading || columns.length === 0 || numericTargets.length === 0}
      >
        {loading ? 'Training…' : 'Train regression model'}
      </button>
    </form>
  );
}
