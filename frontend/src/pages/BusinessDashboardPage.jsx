import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { DatasetFilePicker } from '../components/DatasetFilePicker.jsx';
import { DatasetFileToolbar } from '../components/DatasetFileToolbar.jsx';
import { InsightsPanel } from '../components/InsightsPanel.jsx';
import { KPICard } from '../components/KPICard.jsx';
import { useBusinessAnalytics } from '../hooks/useBusinessAnalytics.js';
import { getLastFile, setLastFile } from '../utils/lastFile.js';
import { workspaceLinks } from '../utils/workspaceLinks.js';

export function BusinessDashboardPage() {
  const navigate = useNavigate();
  const { fileId: routeFileId } = useParams();
  const fileId = routeFileId ? Number(routeFileId) : null;
  const hasFileId = Number.isFinite(fileId);
  const lastFile = getLastFile();
  const { columns, report, loading, preparing, error, analyze } = useBusinessAnalytics(
    hasFileId ? fileId : null,
  );

  useEffect(() => {
    if (hasFileId && lastFile?.filename && lastFile.fileId === fileId) {
      setLastFile({ file_id: fileId, filename: lastFile.filename });
    }
  }, [fileId, hasFileId, lastFile]);

  if (!hasFileId) {
    return (
      <main className="page-shell page-shell--wide">
        <header className="page-header">
          <h1>Business analytics</h1>
          <p className="page-lead">Choose a dataset to calculate revenue and margin KPIs.</p>
        </header>
        <DatasetFilePicker
          title="Choose a dataset for business analytics"
          onSelect={(file) => {
            setLastFile({ file_id: file.file_id, filename: file.filename });
            navigate(`/business/${file.file_id}`);
          }}
        />
      </main>
    );
  }

  return (
    <main className="page-shell page-shell--wide">
      <header className="page-header">
        <h1>Business analytics</h1>
        <p className="page-lead">Map revenue, cost, and date columns to calculate KPIs.</p>
      </header>
      <DatasetFileToolbar
        fileId={fileId}
        filename={lastFile?.fileId === fileId ? lastFile.filename : null}
        basePath="/business"
        relatedLinks={workspaceLinks(fileId)}
      />

      <section className="panel-card">
        {preparing && <p>Loading columns…</p>}
        {!preparing && (
          <form
            className="regression-form"
            onSubmit={(event) => {
              event.preventDefault();
              const formData = new FormData(event.currentTarget);
              analyze({
                dateColumn: formData.get('date_column'),
                revenueColumn: formData.get('revenue_column'),
                costColumn: formData.get('cost_column'),
              });
            }}
          >
            <ColumnSelect label="Date column" name="date_column" columns={columns} />
            <ColumnSelect label="Revenue column" name="revenue_column" columns={columns} />
            <ColumnSelect label="Cost column" name="cost_column" columns={columns} />
            <button className="primary-button" type="submit" disabled={loading}>
              {loading ? 'Analyzing…' : 'Calculate KPIs'}
            </button>
          </form>
        )}
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
      </section>

      {report && (
        <section className="panel-card">
          <p className={report.kpis.length ? 'upload-help' : 'form-error'} role="status">
            {report.suitability_note}
          </p>
          <div className="eda-summary-grid">
            {report.kpis.map((item) => (
              <KPICard key={item.label} item={item} />
            ))}
          </div>
          <InsightsPanel resultId={report.result_id} analysisType="business" />
          {report.revenue_by_month.length > 0 && (
            <>
              <h2>Revenue by month</h2>
              <ul className="file-list">
                {report.revenue_by_month.map((point) => (
                  <li key={point.label}>
                    {point.label}: <strong>{point.value}</strong>
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>
      )}
    </main>
  );
}

function ColumnSelect({ label, name, columns }) {
  return (
    <>
      <label htmlFor={`business-${name}`}>{label}</label>
      <select id={`business-${name}`} name={name} defaultValue="">
        <option value="">Infer automatically</option>
        {columns.map((column) => (
          <option key={column} value={column}>
            {column}
          </option>
        ))}
      </select>
    </>
  );
}
