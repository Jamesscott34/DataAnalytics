import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { BarChart } from './BarChart.jsx';
import { HistogramChart } from './HistogramChart.jsx';
import { MissingValuesChart } from './MissingValuesChart.jsx';
import { EDADashboard } from '../EDADashboard.jsx';

describe('BarChart', () => {
  it('renders categorical value bars', () => {
    render(
      <BarChart
        title="region"
        values={[
          { value: 'North', count: 3 },
          { value: 'South', count: 1 },
        ]}
      />,
    );
    expect(screen.getByLabelText('Bar chart for region')).toBeInTheDocument();
    expect(screen.getByText('North')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });
});

describe('HistogramChart', () => {
  it('renders histogram bins', () => {
    render(
      <HistogramChart
        title="amount"
        bins={[
          { start: 0, end: 10, count: 2 },
          { start: 10, end: 20, count: 5 },
        ]}
      />,
    );
    expect(screen.getByLabelText('Histogram for amount')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
  });
});

describe('MissingValuesChart', () => {
  it('shows empty state when no missing values', () => {
    render(
      <MissingValuesChart
        columns={[{ name: 'id', missing_percent: 0, missing_count: 0 }]}
      />,
    );
    expect(screen.getByText(/no missing values detected/i)).toBeInTheDocument();
  });
});

describe('EDADashboard', () => {
  it('renders summary cards and column table', () => {
    render(
      <EDADashboard
        eda={{
          summary: {
            row_count: 10,
            column_count: 2,
            missing_cells: 1,
            missing_percent: 5,
            duplicate_row_count: 0,
            file_hash: 'a'.repeat(64),
          },
          columns: [
            {
              name: 'value',
              inferred_type: 'integer',
              missing_count: 0,
              missing_percent: 0,
              unique_count: 8,
              sample_values: ['1', '2'],
              numeric_stats: { min: 1, max: 10, mean: 5, median: 5, std: 2, q25: 3, q75: 7 },
            },
          ],
          quality_warnings: ['Column notes has high missing rate'],
          chart_data: {
            value: {
              type: 'histogram',
              bins: [{ start: 1, end: 5, count: 4 }],
            },
          },
          cached: false,
          analyzed_at: '2024-01-01T00:00:00Z',
        }}
        suggestions={{
          target_columns: ['value'],
          feature_columns: [],
          date_columns: [],
          suggested_analyses: ['regression'],
        }}
      />,
    );

    expect(screen.getByText('Rows')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getByRole('rowheader', { name: 'value' })).toBeInTheDocument();
    expect(screen.getByText(/high missing rate/i)).toBeInTheDocument();
    expect(screen.getByText('regression')).toBeInTheDocument();
  });
});
