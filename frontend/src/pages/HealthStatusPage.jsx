import { HealthStatusPanel } from '../components/HealthStatusPanel.jsx';

/**
 * HealthStatusPage
 *
 * Public page showing backend connectivity for development and smoke tests.
 */
export function HealthStatusPage() {
  return (
    <main>
      <header>
        <h1>Predictive Security Analytics Lab</h1>
        <p>Backend connectivity check</p>
      </header>
      <HealthStatusPanel />
    </main>
  );
}
