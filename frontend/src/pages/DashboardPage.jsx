import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth.jsx';

/**
 * DashboardPage
 *
 * Authenticated landing page after login.
 */
export function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <main>
      <header className="dashboard-header">
        <h1>Dashboard</h1>
        <p>
          Signed in as {user?.email} ({user?.role})
        </p>
        <button type="button" onClick={() => logout()} aria-label="Sign out">
          Sign out
        </button>
      </header>
      <nav aria-label="Secondary">
        <Link to="/upload">Upload CSV</Link> <Link to="/health">API health</Link>
      </nav>
    </main>
  );
}
