import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { DatasetFilePicker } from '../components/DatasetFilePicker.jsx';
import { DatasetFileToolbar } from '../components/DatasetFileToolbar.jsx';
import { ExportReportButtons } from '../components/ExportReportButtons.jsx';
import { QuickScanResults } from '../components/QuickScanResults.jsx';
import { useQuickScan } from '../hooks/useQuickScan.js';
import { getLastFile, setLastFile } from '../utils/lastFile.js';
import { workspaceLinks } from '../utils/workspaceLinks.js';

/**
 * QuickScanPage
 *
 * Run all available analyses on a file and export a combined report.
 */
export function QuickScanPage() {
  const navigate = useNavigate();
  const { fileId: routeFileId } = useParams();
  const fileId = routeFileId ? Number(routeFileId) : null;
  const hasFileId = Number.isFinite(fileId);
  const lastFile = getLastFile();
  const { report, loading, error, scan, loadLatest } = useQuickScan(
    hasFileId ? fileId : null,
  );
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    if (hasFileId && lastFile?.filename && lastFile.fileId === fileId) {
      setLastFile({ file_id: fileId, filename: lastFile.filename });
    }
  }, [fileId, hasFileId, lastFile]);

  useEffect(() => {
    if (hasFileId) {
      loadLatest();
    }
  }, [hasFileId, loadLatest]);

  if (!hasFileId) {
    return (
      <main className="page-shell page-shell--wide">
        <header className="page-header">
          <h1>Full analysis scan</h1>
          <p className="page-lead">
            Choose a CSV to run security review, EDA, SQL import, regression, and
            classification in one pass — then export everything to Markdown or PDF.
          </p>
        </header>
        <DatasetFilePicker
          title="Choose a dataset for full scan"
          description="Pick from your uploads or add a new CSV without leaving this page."
          onSelect={(file) => {
            setLastFile({ file_id: file.file_id, filename: file.filename });
            navigate(`/scan/${file.file_id}`);
          }}
        />
      </main>
    );
  }

  const activeFilename = lastFile?.fileId === fileId ? lastFile.filename : null;

  return (
    <main className="page-shell page-shell--wide">
      <header className="page-header">
        <h1>Full analysis scan</h1>
        <p className="page-lead">
          Runs every available analysis on this file. When finished, download a combined
          Markdown or PDF report with all results.
        </p>
      </header>

      <DatasetFileToolbar
        fileId={fileId}
        filename={activeFilename}
        basePath="/scan"
        relatedLinks={workspaceLinks(fileId)}
      />

      <section className="panel-card">
        <div className="panel-card-header">
          <h2>Run quick scan</h2>
          <button
            type="button"
            className="primary-button"
            onClick={scan}
            disabled={loading}
          >
            {loading ? 'Running all analyses…' : report ? 'Re-run full scan' : 'Run full scan'}
          </button>
        </div>
        <p className="upload-help">
          This runs security scan review, EDA, SQL import, regression (when numeric columns
          exist), and classification (when categorical targets exist). Steps that cannot run
          are marked as skipped.
        </p>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        {report && (
          <ExportReportButtons
            report={report}
            exporting={exporting}
            onExportStart={() => setExporting(true)}
            onExportEnd={() => setExporting(false)}
          />
        )}
      </section>

      <QuickScanResults report={report} />
    </main>
  );
}
