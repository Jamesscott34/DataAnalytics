import { Link, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth.js';
import { getLastFile } from '../utils/lastFile.js';

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/groups', label: 'Dataset groups' },
  { to: '/upload', label: 'Upload CSV' },
  { to: '/assets', label: 'Sample datasets' },
  { to: '/health', label: 'API health' },
];

/**
 * AppShell
 *
 * Shared layout with sidebar navigation for authenticated pages.
 */
export function AppShell() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const lastFile = getLastFile();

  return (
    <div className="app-shell">
      <aside className="app-sidebar" aria-label="Main navigation">
        <div className="app-brand">
          <p className="app-brand-title">Analytics Lab</p>
          <p className="app-brand-subtitle">Secure CSV workspace</p>
        </div>

        <nav className="app-nav">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={
                location.pathname === item.to
                  ? 'app-nav-link is-active'
                  : 'app-nav-link'
              }
            >
              {item.label}
            </Link>
          ))}
        </nav>

        {lastFile && (
          <section className="app-last-file" aria-label="Last used file">
            <h2>Last file</h2>
            <p className="app-last-file-name">{lastFile.filename}</p>
            <div className="app-last-file-actions">
              <Link to={`/scan/${lastFile.fileId}`}>Full scan</Link>
              <Link to={`/sql/${lastFile.fileId}`}>SQL</Link>
              <Link to={`/eda/${lastFile.fileId}`}>EDA</Link>
              <Link to={`/regression/${lastFile.fileId}`}>Regression</Link>
              <Link to={`/classification/${lastFile.fileId}`}>Classification</Link>
              <Link to={`/clustering/${lastFile.fileId}`}>Clustering</Link>
              <Link to={`/pca/${lastFile.fileId}`}>PCA</Link>
              <Link to={`/timeseries/${lastFile.fileId}`}>Time series</Link>
              <Link to={`/similarity/${lastFile.fileId}`}>Similarity</Link>
              <Link to={`/business/${lastFile.fileId}`}>Business</Link>
              <Link to={`/versions/${lastFile.fileId}`}>Versions</Link>
            </div>
          </section>
        )}

        <footer className="app-sidebar-footer">
          <p className="app-user">
            {user?.email}
            <span className="app-user-role">{user?.role}</span>
          </p>
          <button type="button" className="secondary-button" onClick={() => logout()}>
            Sign out
          </button>
        </footer>
      </aside>

      <div className="app-main">
        <Outlet />
      </div>
    </div>
  );
}
