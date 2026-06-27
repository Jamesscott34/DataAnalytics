import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { BusinessDashboardPage } from './BusinessDashboardPage.jsx';

const analyze = vi.fn();

vi.mock('../hooks/useBusinessAnalytics.js', () => ({
  useBusinessAnalytics: () => ({
    columns: ['job_date', 'customer_region', 'revenue', 'cost', 'pest_type'],
    report: null,
    loading: false,
    preparing: false,
    error: null,
    analyze,
  }),
}));

describe('BusinessDashboardPage', () => {
  beforeEach(() => {
    analyze.mockReset();
  });

  it('renders the business form and applies pest control preset', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={['/business/7']}>
        <Routes>
          <Route path="/business/:fileId" element={<BusinessDashboardPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: /business analytics/i })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /apply pest control preset/i }));
    await user.click(screen.getByRole('button', { name: /calculate kpis/i }));

    expect(analyze).toHaveBeenCalledWith({
      dateColumn: 'job_date',
      revenueColumn: 'revenue',
      costColumn: 'cost',
    });
  });
});
