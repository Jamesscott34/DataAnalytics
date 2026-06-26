import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { fetchScanResult } from '../api/export.js';

/**
 * ScanResultViewPage
 *
 * View a saved Markdown or PDF report from scan_results/ in the browser.
 */
export function ScanResultViewPage() {
  const { filename: encodedFilename } = useParams();
  const filename = encodedFilename ? decodeURIComponent(encodedFilename) : '';
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [markdown, setMarkdown] = useState('');
  const [pdfUrl, setPdfUrl] = useState(null);
  const isPdf = filename.toLowerCase().endsWith('.pdf');

  useEffect(() => {
    if (!filename) {
      setError('No filename provided');
      setLoading(false);
      return undefined;
    }

    let cancelled = false;
    let objectUrl = null;

    (async () => {
      setLoading(true);
      setError(null);
      setMarkdown('');
      setPdfUrl(null);
      try {
        const result = await fetchScanResult(filename);
        if (cancelled) {
          return;
        }
        if (isPdf) {
          objectUrl = URL.createObjectURL(result.blob);
          setPdfUrl(objectUrl);
        } else {
          setMarkdown(result.text ?? '');
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [filename, isPdf]);

  return (
    <main className="page-shell page-shell--wide">
      <header className="page-header">
        <h1>Scan report</h1>
        <p className="page-lead">
          <strong>{filename}</strong>
        </p>
        <div className="inline-links">
          <Link to="/dashboard">Back to dashboard</Link>
          <Link to="/scan">Run another scan</Link>
        </div>
      </header>

      {loading && <p>Loading report…</p>}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      {!loading && !error && isPdf && pdfUrl && (
        <section className="panel-card scan-result-viewer">
          <iframe title={filename} src={pdfUrl} className="scan-result-pdf" />
        </section>
      )}
      {!loading && !error && !isPdf && (
        <section className="panel-card scan-result-viewer">
          <pre className="scan-result-markdown">{markdown}</pre>
        </section>
      )}
    </main>
  );
}
