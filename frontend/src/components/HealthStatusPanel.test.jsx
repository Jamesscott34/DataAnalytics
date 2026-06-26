import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { HealthStatusPanel } from './HealthStatusPanel.jsx';
import * as monitoring from '../api/monitoring.js';

describe('HealthStatusPanel', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders loading state initially', () => {
    vi.spyOn(monitoring, 'fetchHealth').mockReturnValue(new Promise(() => {}));
    render(<HealthStatusPanel />);
    expect(screen.getByRole('status')).toHaveTextContent(/checking backend health/i);
  });

  it('displays ok status when health check succeeds', async () => {
    vi.spyOn(monitoring, 'fetchHealth').mockResolvedValue({ status: 'ok' });
    render(<HealthStatusPanel />);
    await waitFor(() => {
      expect(screen.getByLabelText('API status ok')).toBeInTheDocument();
    });
  });

  it('displays error when health check fails', async () => {
    vi.spyOn(monitoring, 'fetchHealth').mockRejectedValue(new Error('Network error'));
    render(<HealthStatusPanel />);
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/network error/i);
    });
  });
});
