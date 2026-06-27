import { Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { listUploads } from '../api/uploads.js';
import { listGroups } from '../api/groups.js';
import { getLastFile } from '../utils/lastFile.js';
import { DashboardEdaPanel } from '../components/DashboardEdaPanel.jsx';
import { ScanResultsPanel } from '../components/ScanResultsPanel.jsx';

/**
 * DashboardPage
 *
 * Authenticated home with recent files and quick actions.
 */
export function DashboardPage() {
  const [recentFiles, setRecentFiles] = useState([]);
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const lastFile = getLastFile();
  const focusFile =
    lastFile ??
    (recentFiles[0]
      ? { fileId: recentFiles[0].id, filename: recentFiles[0].original_filename }
      : null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [uploadResponse, groupResponse] = await Promise.all([
          listUploads(),
          listGroups(),
        ]);
        if (!cancelled) {
          setRecentFiles(uploadResponse.items ?? []);
          setGroups(groupResponse.items ?? []);
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
    };
  }, []);

  return (
    <main className="page-shell page-shell--wide">
      <header className="page-header">
        <h1>Dashboard</h1>
        <p className="page-lead">
          Upload a CSV, run exploratory analysis, train regression models, query with SQL,
          and track version history from one place.
        </p>
      </header>

      <section className="card-grid" aria-label="Quick actions">
        <article className="action-card action-card--highlight">
          <h2>Full analysis scan</h2>
          <p>
            Run EDA, SQL, regression, and classification in one go, then export a
            combined Markdown or PDF report.
          </p>
          <Link className="primary-link" to="/scan">
            Run full scan
          </Link>
        </article>
        <article className="action-card">
          <h2>Upload data</h2>
          <p>Import a new CSV through the secure scanner pipeline.</p>
          <Link className="primary-link" to="/upload">
            Go to upload
          </Link>
        </article>
        <article className="action-card">
          <h2>Sample datasets</h2>
          <p>Start quickly with curated files from temp_assets.</p>
          <Link className="primary-link" to="/assets">
            Browse samples
          </Link>
        </article>
        <article className="action-card">
          <h2>Dataset groups</h2>
          <p>Group customers, products, and prices CSVs for multi-table SQL.</p>
          <Link className="primary-link" to="/groups">
            Manage groups
          </Link>
        </article>
        <article className="action-card">
          <h2>SQL analysis</h2>
          <p>Import headers, run library queries, or write custom SQL.</p>
          <Link className="primary-link" to="/sql">
            Open SQL
          </Link>
        </article>
        <article className="action-card">
          <h2>Exploratory analysis</h2>
          <p>Column types, missing values, distributions, and quality warnings.</p>
          <Link className="primary-link" to="/eda">
            Open EDA
          </Link>
        </article>
        <article className="action-card">
          <h2>Regression models</h2>
          <p>
            Train linear, polynomial, decision tree, or random forest models with MAE,
            RMSE, and R² metrics.
          </p>
          <Link className="primary-link" to="/regression">
            Open regression
          </Link>
        </article>
        <article className="action-card">
          <h2>Classification models</h2>
          <p>
            Train logistic, SVM, k-NN, naive Bayes, or tree models with accuracy, F1,
            and confusion matrix.
          </p>
          <Link className="primary-link" to="/classification">
            Open classification
          </Link>
        </article>
        <article className="action-card">
          <h2>Clustering</h2>
          <p>K-means and hierarchical clustering with elbow diagnostics.</p>
          <Link className="primary-link" to="/clustering">
            Open clustering
          </Link>
        </article>
        <article className="action-card">
          <h2>PCA</h2>
          <p>Principal component analysis with explained variance charts.</p>
          <Link className="primary-link" to="/pca">
            Open PCA
          </Link>
        </article>
        <article className="action-card">
          <h2>Time series</h2>
          <p>Moving average, AR, and ARIMA forecasting with hold-out metrics.</p>
          <Link className="primary-link" to="/timeseries">
            Open time series
          </Link>
        </article>
        <article className="action-card">
          <h2>Similarity</h2>
          <p>Find similar rows or item columns using cosine similarity.</p>
          <Link className="primary-link" to="/similarity">
            Open similarity
          </Link>
        </article>
        {lastFile && (
          <article className="action-card action-card--highlight">
            <h2>Continue with last file</h2>
            <p>
              <strong>{lastFile.filename}</strong>
            </p>
            <div className="inline-links">
              <Link to={`/scan/${lastFile.fileId}`}>Full scan</Link>
              <Link to={`/sql/${lastFile.fileId}`}>SQL analysis</Link>
              <Link to={`/eda/${lastFile.fileId}`}>EDA</Link>
              <Link to={`/regression/${lastFile.fileId}`}>Regression</Link>
              <Link to={`/classification/${lastFile.fileId}`}>Classification</Link>
              <Link to={`/clustering/${lastFile.fileId}`}>Clustering</Link>
              <Link to={`/pca/${lastFile.fileId}`}>PCA</Link>
              <Link to={`/timeseries/${lastFile.fileId}`}>Time series</Link>
              <Link to={`/similarity/${lastFile.fileId}`}>Similarity</Link>
              <Link to={`/versions/${lastFile.fileId}`}>Version history</Link>
            </div>
          </article>
        )}
      </section>

      <DashboardEdaPanel fileId={focusFile?.fileId} filename={focusFile?.filename} />

      <ScanResultsPanel />

      <section className="panel-card">
        <div className="panel-card-header">
          <h2>Dataset groups</h2>
          <Link to="/groups">Manage groups</Link>
        </div>
        {loading && <p>Loading groups…</p>}
        {!loading && groups.length === 0 && (
          <p>
            No groups yet. Combine related CSVs (customers, products, prices) for
            multi-table SQL.{' '}
            <Link to="/groups">Create a group</Link>
          </p>
        )}
        {!loading && groups.length > 0 && (
          <ul className="file-list">
            {groups.map((group) => (
              <li key={group.id}>
                <div>
                  <strong>{group.name}</strong>
                  <span>
                    {group.members.length} file{group.members.length === 1 ? '' : 's'}
                    {group.members.length > 0 &&
                      ` · ${group.members.map((member) => member.original_filename).join(', ')}`}
                  </span>
                </div>
                <div className="inline-links">
                  <Link to={`/sql/groups/${group.id}`}>Group SQL</Link>
                  <Link to="/groups">Edit</Link>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="panel-card">
        <div className="panel-card-header">
          <h2>Recent uploads</h2>
          <Link to="/upload">Upload another</Link>
        </div>
        {loading && <p>Loading recent files…</p>}
        {error && <p role="alert">{error}</p>}
        {!loading && !error && recentFiles.length === 0 && (
          <p>No uploads yet. Upload a CSV or select a sample dataset to get started.</p>
        )}
        {!loading && recentFiles.length > 0 && (
          <ul className="file-list">
            {recentFiles.map((file) => (
              <li key={file.id}>
                <div>
                  <strong>{file.original_filename}</strong>
                  <span>
                    {file.row_count ?? 0} rows · {file.column_count ?? 0} columns
                  </span>
                </div>
                <div className="inline-links">
                  <Link to={`/scan/${file.id}`}>Full scan</Link>
                  <Link to={`/sql/${file.id}`}>SQL</Link>
                  <Link to={`/eda/${file.id}`}>EDA</Link>
                  <Link to={`/regression/${file.id}`}>Regression</Link>
                  <Link to={`/classification/${file.id}`}>Classification</Link>
                  <Link to={`/clustering/${file.id}`}>Clustering</Link>
                  <Link to={`/pca/${file.id}`}>PCA</Link>
                  <Link to={`/timeseries/${file.id}`}>Time series</Link>
                  <Link to={`/similarity/${file.id}`}>Similarity</Link>
                  <Link to={`/versions/${file.id}`}>Versions</Link>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
