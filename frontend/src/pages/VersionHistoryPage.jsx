import { useParams, useSearchParams } from 'react-router-dom';
import { VersionTimeline } from '../components/VersionTimeline.jsx';
import { useFileVersions } from '../hooks/useFileVersions.js';

/**
 * VersionHistoryPage
 *
 * Shows upload version history for a dataset file.
 */
export function VersionHistoryPage() {
  const { fileId: routeFileId } = useParams();
  const [searchParams] = useSearchParams();
  const fileId = Number(routeFileId ?? searchParams.get('file_id'));
  const { history, comparison, loading, error, compareVersions } = useFileVersions(
    Number.isFinite(fileId) ? fileId : null,
  );

  if (!Number.isFinite(fileId)) {
    return (
      <main className="page-shell">
        <h1>Version history</h1>
        <p>Open this page with a file id, for example `/versions/1`.</p>
      </main>
    );
  }

  return (
    <main className="page-shell">
      <h1>Version history</h1>
      {loading && <p>Loading versions…</p>}
      {error && <p role="alert">{error}</p>}
      <VersionTimeline
        history={history}
        onCompare={(versionA, versionB) => compareVersions(versionA, versionB)}
      />
      {comparison && (
        <section className="version-compare" aria-live="polite">
          <h2>Comparison</h2>
          <p>Content identical: {comparison.content_identical ? 'yes' : 'no'}</p>
          {comparison.differences.length > 0 ? (
            <ul>
              {comparison.differences.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : (
            <p>No metadata differences between the selected versions.</p>
          )}
        </section>
      )}
    </main>
  );
}
