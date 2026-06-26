import { EDADashboard } from './EDADashboard.jsx';
import { ClassificationResults } from './ClassificationResults.jsx';
import { RegressionResults } from './RegressionResults.jsx';

/**
 * QuickScanResults
 *
 * Summary of a full analysis quick scan with step statuses.
 */
export function QuickScanResults({ report }) {
  if (!report) {
    return null;
  }

  return (
    <div className="quick-scan-results">
      <section className="panel-card">
        <h2>Scan summary</h2>
        <p className="upload-help">
          Generated {new Date(report.generated_at).toLocaleString()} for{' '}
          <strong>{report.filename}</strong>
        </p>
        <ul className="quick-scan-steps">
          {report.steps.map((step) => (
            <li key={step.step} className={`quick-scan-step quick-scan-step--${step.status}`}>
              <strong>{formatStepName(step.step)}</strong>
              <span>{step.status}</span>
              {step.message && <p>{step.message}</p>}
            </li>
          ))}
        </ul>
      </section>

      {report.security_scan && (
        <section className="panel-card">
          <h2>Security scan</h2>
          <p>
            Status: <strong>{report.security_scan.status}</strong> · Risk:{' '}
            {report.security_scan.risk_score}/100
          </p>
          <p>{report.security_scan.recommended_action}</p>
        </section>
      )}

      {report.eda && (
        <section className="panel-card">
          <h2>Exploratory analysis</h2>
          <EDADashboard eda={report.eda} suggestions={report.suggestions} />
        </section>
      )}

      {report.sql_import && (
        <section className="panel-card">
          <h2>SQL import</h2>
          <p>
            Table <code>{report.sql_import.table_name}</code> ·{' '}
            {report.sql_import.imported_rows} rows · {report.sql_import.columns.length}{' '}
            columns
          </p>
        </section>
      )}

      {report.regression && (
        <section className="panel-card">
          <h2>Regression</h2>
          <RegressionResults result={report.regression} />
        </section>
      )}

      {report.classification && (
        <section className="panel-card">
          <h2>Classification</h2>
          <ClassificationResults result={report.classification} />
        </section>
      )}
    </div>
  );
}

function formatStepName(step) {
  return step
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}
