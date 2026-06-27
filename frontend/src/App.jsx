import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/AppShell.jsx';
import { AssetIntegrityGate } from './components/AssetIntegrityGate.jsx';
import { ProtectedRoute } from './components/ProtectedRoute.jsx';
import { AuthProvider } from './context/AuthProvider.jsx';
import { AssetsPage } from './pages/AssetsPage.jsx';
import { DashboardPage } from './pages/DashboardPage.jsx';
import { HealthStatusPage } from './pages/HealthStatusPage.jsx';
import { LoginPage } from './pages/LoginPage.jsx';
import { ClassificationPage } from './pages/ClassificationPage.jsx';
import { ClusteringPage } from './pages/ClusteringPage.jsx';
import { EDAPage } from './pages/EDAPage.jsx';
import { GroupsPage } from './pages/GroupsPage.jsx';
import { PCAPage } from './pages/PCAPage.jsx';
import { QuickScanPage } from './pages/QuickScanPage.jsx';
import { ScanResultViewPage } from './pages/ScanResultViewPage.jsx';
import { RegressionPage } from './pages/RegressionPage.jsx';
import { SQLAnalysisPage } from './pages/SQLAnalysisPage.jsx';
import { SQLGroupPage } from './pages/SQLGroupPage.jsx';
import { VersionHistoryPage } from './pages/VersionHistoryPage.jsx';
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
        <AssetIntegrityGate />
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/health" element={<HealthStatusPage />} />
          <Route
            element={
              <ProtectedRoute>
                <AppShell />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route
              path="/upload"
              element={
                <ProtectedRoute roles={['admin', 'analyst']}>
                  <UploadPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/groups"
              element={
                <ProtectedRoute roles={['admin', 'analyst']}>
                  <GroupsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/sql/groups/:groupId"
              element={
                <ProtectedRoute roles={['admin', 'analyst']}>
                  <SQLGroupPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/eda"
              element={
                <ProtectedRoute roles={['admin', 'analyst']}>
                  <EDAPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/eda/:fileId"
              element={
                <ProtectedRoute roles={['admin', 'analyst']}>
                  <EDAPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/scan"
              element={
                <ProtectedRoute roles={['admin', 'analyst']}>
                  <QuickScanPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/scan/:fileId"
              element={
                <ProtectedRoute roles={['admin', 'analyst']}>
                  <QuickScanPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/scan-results/view/:filename"
              element={
                <ProtectedRoute roles={['admin', 'analyst']}>
                  <ScanResultViewPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/classification"
              element={
                <ProtectedRoute roles={['admin', 'analyst']}>
                  <ClassificationPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/classification/:fileId"
              element={
                <ProtectedRoute roles={['admin', 'analyst']}>
                  <ClassificationPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/clustering"
              element={
                <ProtectedRoute roles={['admin', 'analyst']}>
                  <ClusteringPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/clustering/:fileId"
              element={
                <ProtectedRoute roles={['admin', 'analyst']}>
                  <ClusteringPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/pca"
              element={
                <ProtectedRoute roles={['admin', 'analyst']}>
                  <PCAPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/pca/:fileId"
              element={
                <ProtectedRoute roles={['admin', 'analyst']}>
                  <PCAPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/regression"
              element={
                <ProtectedRoute roles={['admin', 'analyst']}>
                  <RegressionPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/regression/:fileId"
              element={
                <ProtectedRoute roles={['admin', 'analyst']}>
                  <RegressionPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/sql"
              element={
                <ProtectedRoute roles={['admin', 'analyst']}>
                  <SQLAnalysisPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/sql/:fileId"
              element={
                <ProtectedRoute roles={['admin', 'analyst']}>
                  <SQLAnalysisPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/versions/:fileId"
              element={
                <ProtectedRoute roles={['admin', 'analyst']}>
                  <VersionHistoryPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/assets"
              element={
                <ProtectedRoute roles={['admin', 'analyst']}>
                  <AssetsPage />
                </ProtectedRoute>
              }
            />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
