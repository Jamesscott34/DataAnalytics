/**
 * DuplicateResolutionPanel
 *
 * Shown after a successful security scan when the file hash already exists.
 *
 * @param {Object} props
 * @param {Object} props.duplicate - Duplicate upload payload from the API.
 * @param {boolean} props.loading - Whether an action is in progress.
 * @param {Function} props.onUseExisting - Continue with the stored file.
 * @param {Function} props.onReplace - Replace the stored file with this upload.
 * @param {Function} props.onDeleteExisting - Delete the stored file, then upload.
 * @param {Function} props.onCancel - Dismiss the duplicate prompt.
 */
export function DuplicateResolutionPanel({
  duplicate,
  loading,
  onUseExisting,
  onReplace,
  onDeleteExisting,
  onCancel,
}) {
  if (!duplicate) {
    return null;
  }

  const existing = duplicate.existing_file;

  return (
    <section className="duplicate-panel" aria-labelledby="duplicate-heading">
      <h3 id="duplicate-heading">Duplicate file detected</h3>
      <p>
        Security scan passed, but this file matches an upload already stored in the
        system.
      </p>
      <dl>
        <div>
          <dt>Existing filename</dt>
          <dd>{existing.original_filename}</dd>
        </div>
        <div>
          <dt>SHA-256</dt>
          <dd>
            <code>{existing.file_hash}</code>
          </dd>
        </div>
        <div>
          <dt>Rows</dt>
          <dd>{existing.row_count ?? 'unknown'}</dd>
        </div>
        <div>
          <dt>Columns</dt>
          <dd>{existing.column_count ?? 'unknown'}</dd>
        </div>
      </dl>
      <div className="duplicate-actions">
        <button type="button" onClick={onUseExisting} disabled={loading}>
          Use existing file
        </button>
        <button type="button" onClick={onReplace} disabled={loading}>
          Replace with this upload
        </button>
        <button type="button" onClick={onDeleteExisting} disabled={loading}>
          Delete existing, then upload
        </button>
        <button
          type="button"
          className="secondary-button"
          onClick={onCancel}
          disabled={loading}
        >
          Cancel
        </button>
      </div>
    </section>
  );
}
