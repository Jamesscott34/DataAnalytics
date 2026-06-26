import { useState } from 'react';
import { Link } from 'react-router-dom';
import { getScanResultViewPath, saveMarkdownReport, savePdfReport } from '../api/export.js';

/**
 * ExportReportButtons
 *
 * Save quick-scan report as Markdown or PDF to scan_results/.
 */
export function ExportReportButtons({ report, exporting, onExportStart, onExportEnd, onSaved }) {
  const [lastSaved, setLastSaved] = useState(null);
  const [message, setMessage] = useState(null);

  if (!report?.report_id) {
    return null;
  }

  const handleExport = async (format) => {
    onExportStart?.();
    setMessage(null);
    try {
      const response =
        format === 'md'
          ? await saveMarkdownReport(report.report_id)
          : await savePdfReport(report.report_id);
      setLastSaved(response.saved);
      setMessage(`Saved as ${response.saved.filename}`);
      onSaved?.(response.saved);
    } catch (err) {
      setMessage(err.message);
    } finally {
      onExportEnd?.();
    }
  };

  return (
    <div className="export-report-actions">
      <div className="inline-links">
        <button
          type="button"
          className="primary-button"
          disabled={exporting}
          onClick={() => handleExport('md')}
        >
          {exporting ? 'Saving…' : 'Save Markdown (.md)'}
        </button>
        <button
          type="button"
          className="secondary-button"
          disabled={exporting}
          onClick={() => handleExport('pdf')}
        >
          Save PDF
        </button>
      </div>
      {message && <p className="upload-help">{message}</p>}
      {lastSaved && (
        <p className="upload-help">
          <Link to={getScanResultViewPath(lastSaved.filename)}>View {lastSaved.filename}</Link>
        </p>
      )}
    </div>
  );
}
