/**
 * VersionTimeline
 *
 * Displays version history for an uploaded dataset.
 *
 * @param {Object} props
 * @param {Object|null} props.history - Version history payload.
 * @param {Function} props.onCompare - Compare handler for two versions.
 */
export function VersionTimeline({ history, onCompare }) {
  if (!history) {
    return null;
  }

  const versions = history.versions ?? [];

  return (
    <section className="version-panel" aria-labelledby="version-timeline-heading">
      <h2 id="version-timeline-heading">Version timeline</h2>
      <p>
        File hash: <code>{history.file_hash}</code>
      </p>
      {versions.length === 0 ? (
        <p>No versions recorded yet.</p>
      ) : (
        <ol className="version-list">
          {versions.map((version) => (
            <li key={version.id}>
              <strong>v{version.version_number}</strong>: {version.upload_event}
              <div>{new Date(version.created_at).toLocaleString()}</div>
              {version.notes && <div>{version.notes}</div>}
            </li>
          ))}
        </ol>
      )}
      {versions.length >= 2 && (
        <button type="button" onClick={() => onCompare(1, versions.length)}>
          Compare first and latest version
        </button>
      )}
    </section>
  );
}
