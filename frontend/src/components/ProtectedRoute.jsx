import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth.js';

/**
 * ProtectedRoute
 *
 * Redirects unauthenticated users to the login page.
 *
 * @param {Object} props
 * @param {import('react').ReactNode} props.children
 * @param {string[]} [props.roles] - Optional allowed roles.
 */
export function ProtectedRoute({ children, roles }) {
  const { isAuthenticated, loading, user } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <p role="status" aria-live="polite">
        Loading session…
      </p>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (roles && user && !roles.includes(user.role)) {
    return <p role="alert">You do not have permission to view this page.</p>;
  }

  return children;
}
