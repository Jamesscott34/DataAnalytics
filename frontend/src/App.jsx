import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { ProtectedRoute } from './components/ProtectedRoute.jsx';
import { AuthProvider } from './hooks/useAuth.jsx';
import { DashboardPage } from './pages/DashboardPage.jsx';
import { HealthStatusPage } from './pages/HealthStatusPage.jsx';
import { LoginPage } from './pages/LoginPage.jsx';
import { UploadPage } from './pages/UploadPage.jsx';
import './App.css';

/**
 * App
 *
 * Root application shell with route definitions.
 */
function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/health" element={<HealthStatusPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/upload"
            element={
              <ProtectedRoute roles={['admin', 'analyst']}>
                <UploadPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
