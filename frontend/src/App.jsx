import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { HealthStatusPage } from './pages/HealthStatusPage.jsx';
import './App.css';

/**
 * App
 *
 * Root application shell with route definitions.
 */
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/health" replace />} />
        <Route path="/health" element={<HealthStatusPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
