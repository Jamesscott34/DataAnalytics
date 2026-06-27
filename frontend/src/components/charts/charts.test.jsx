import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { BarChart } from './BarChart.jsx';
import { ForecastChart } from './ForecastChart.jsx';
import { HistogramChart } from './HistogramChart.jsx';
import { MissingValuesChart } from './MissingValuesChart.jsx';
import { ConfusionMatrixChart } from './ConfusionMatrixChart.jsx';
import { ResidualChart } from './ResidualChart.jsx';
import { TopPairsChart } from './TopPairsChart.jsx';
import { CorrelationHeatmap } from './CorrelationHeatmap.jsx';
import { LineChart } from './LineChart.jsx';
import { ScatterChart } from './ScatterChart.jsx';
import { TrendBarChart } from './TrendBarChart.jsx';
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

describe('ForecastChart', () => {
  it('renders actual and forecast lines', () => {
    render(
      <ForecastChart
        title="Sales forecast"
        history={[
          { label: '2024-01', actual: 100, forecast: 98 },
          { label: '2024-02', actual: 110, forecast: 108 },
        ]}
        forecast={[
          { label: '2024-03', actual: null, forecast: 115 },
          { label: '2024-04', actual: null, forecast: 120 },
        ]}
      />,
    );
    expect(screen.getByLabelText('Line chart for Sales forecast')).toBeInTheDocument();
    expect(screen.getByText('Actual')).toBeInTheDocument();
    expect(screen.getByText('Forecast')).toBeInTheDocument();
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

describe('Result charts', () => {
  it('renders residual magnitudes', () => {
    render(<ResidualChart residuals={[0.2, -1.4]} />);
    expect(
      screen.getByLabelText('Bar chart for Residual magnitude'),
    ).toBeInTheDocument();
  });

  it('renders confusion matrix heatmap', () => {
    render(
      <ConfusionMatrixChart
        labels={['A', 'B']}
        matrix={[
          [2, 1],
          [0, 3],
        ]}
      />,
    );
    expect(screen.getByLabelText('Confusion matrix heatmap')).toBeInTheDocument();
  });

  it('renders top pair scores', () => {
    render(<TopPairsChart pairs={[{ left: 'A', right: 'B', score: 0.94 }]} />);
    expect(screen.getByLabelText('Bar chart for Top scores')).toBeInTheDocument();
  });

  it('renders trend bars', () => {
    render(<TrendBarChart points={[{ label: 'Jan', value: 120 }]} />);
    expect(screen.getByLabelText('Bar chart for Trend')).toBeInTheDocument();
  });

  it('renders scatter plot', () => {
    render(
      <ScatterChart
        title="revenue vs cost"
        xColumn="revenue"
        yColumn="cost"
        points={[
          { x: 1, y: 2 },
          { x: 3, y: 4 },
        ]}
      />,
    );
    expect(
      screen.getByLabelText('Scatter plot for revenue vs cost'),
    ).toBeInTheDocument();
  });

  it('renders EDA line chart', () => {
    render(
      <LineChart
        title="Revenue trend"
        xColumn="date"
        yColumn="revenue"
        points={[
          { x: '2024-01-01', y: 100 },
          { x: '2024-02-01', y: 120 },
        ]}
      />,
    );
    expect(screen.getByLabelText('Line chart for Revenue trend')).toBeInTheDocument();
  });

  it('renders correlation heatmap', () => {
    render(
      <CorrelationHeatmap
        labels={['a', 'b']}
        matrix={[
          [1, 0.5],
          [0.5, 1],
        ]}
      />,
    );
    expect(screen.getByLabelText('Correlation heatmap')).toBeInTheDocument();
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
              numeric_stats: {
                min: 1,
                max: 10,
                mean: 5,
                median: 5,
                std: 2,
                q25: 3,
                q75: 7,
              },
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
