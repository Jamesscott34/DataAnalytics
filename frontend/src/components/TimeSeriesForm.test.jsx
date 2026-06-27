import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { TimeSeriesForm } from './TimeSeriesForm.jsx';

describe('TimeSeriesForm', () => {
  it('submits valid defaults for hidden algorithm fields', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(
      <TimeSeriesForm
        algorithms={[{ id: 'moving_average', label: 'Moving average' }]}
        columns={['date', 'sales']}
        suggestions={{
          date_columns: ['date'],
          target_columns: ['sales'],
        }}
        loading={false}
        onSubmit={onSubmit}
      />,
    );

    await user.click(screen.getByRole('button', { name: /run forecast/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      algorithm: 'moving_average',
      dateColumn: 'date',
      valueColumn: 'sales',
      forecastPeriods: 5,
      window: 3,
      arLags: 3,
      arimaP: 1,
      arimaD: 1,
      arimaQ: 1,
      seasonalPeriod: null,
    });
  });
});
