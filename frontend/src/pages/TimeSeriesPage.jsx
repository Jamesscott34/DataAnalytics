import { useNavigate, useParams } from 'react-router-dom';
import { useEffect } from 'react';
import { DatasetFilePicker } from '../components/DatasetFilePicker.jsx';
import { DatasetFileToolbar } from '../components/DatasetFileToolbar.jsx';
import { TimeSeriesForm } from '../components/TimeSeriesForm.jsx';
import { TimeSeriesResults } from '../components/TimeSeriesResults.jsx';
import { useTimeseries } from '../hooks/useTimeseries.js';
import { getLastFile, setLastFile } from '../utils/lastFile.js';
import { workspaceLinks } from '../utils/workspaceLinks.js';

export function TimeSeriesPage() {
  const navigate = useNavigate();
  const { fileId: routeFileId } = useParams();
  const fileId = routeFileId ? Number(routeFileId) : null;
  const hasFileId = Number.isFinite(fileId);
  const lastFile = getLastFile();
  const { algorithms, columns, suggestions, result, loading, preparing, error, forecast } =
    useTimeseries(hasFileId ? fileId : null);

  useEffect(() => {
    if (hasFileId && lastFile?.filename && lastFile.fileId === fileId) {
      setLastFile({ file_id: fileId, filename: lastFile.filename });
    }
  }, [fileId, hasFileId, lastFile]);

  if (!hasFileId) {
    return (
      <main className="page-shell page-shell--wide">
        <header className="page-header">
          <h1>Time series</h1>
          <p className="page-lead">Choose a dataset for moving average, AR, or ARIMA forecasting.</p>
        </header>
        <DatasetFilePicker
          title="Choose a dataset for time series forecasting"
          onSelect={(file) => {
            setLastFile({ file_id: file.file_id, filename: file.filename });
            navigate(`/timeseries/${file.file_id}`);
          }}
        />
      </main>
    );
  }

  return (
    <main className="page-shell page-shell--wide">
      <header className="page-header">
        <h1>Time series</h1>
        <p className="page-lead">Forecast numeric trends from dated observations.</p>
      </header>
      <DatasetFileToolbar
        fileId={fileId}
        filename={lastFile?.fileId === fileId ? lastFile.filename : null}
        basePath="/timeseries"
        relatedLinks={workspaceLinks(fileId)}
      />
      <section className="panel-card">
        {preparing && <p>Loading columns…</p>}
        {!preparing && (
          <TimeSeriesForm
            algorithms={algorithms}
            columns={columns}
            suggestions={suggestions}
            loading={loading}
            onSubmit={forecast}
          />
        )}
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
      </section>
      <TimeSeriesResults result={result} />
    </main>
  );
}
