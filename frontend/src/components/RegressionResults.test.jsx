import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { RegressionResults } from './RegressionResults.jsx';

describe('RegressionResults', () => {
  it('renders metrics and actual vs predicted rows', () => {
    render(
      <RegressionResults
        result={{
          algorithm: 'linear',
          target_column: 'revenue',
          feature_columns: ['units'],
          train_rows: 6,
          test_rows: 2,
          metrics: { mae: 1.5, rmse: 2.1, r2: 0.91 },
          actual_vs_predicted: [
            { actual: 10, predicted: 9.5 },
            { actual: 12, predicted: 12.2 },
          ],
          residuals: [0.5, -0.2],
          feature_importance: [{ feature: 'units', importance: 0.88 }],
        }}
      />,
    );

    expect(screen.getByText('MAE')).toBeInTheDocument();
    expect(screen.getByText('1.5')).toBeInTheDocument();
    expect(screen.getByText('0.91')).toBeInTheDocument();
    expect(screen.getByText('9.5')).toBeInTheDocument();
    expect(screen.getByLabelText('Bar chart for Feature importance')).toBeInTheDocument();
  });
});
