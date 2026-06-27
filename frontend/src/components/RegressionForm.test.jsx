import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { RegressionForm } from './RegressionForm.jsx';

describe('RegressionForm', () => {
  it('defaults to a numeric target and excludes it from features on submit', async () => {
    const onSubmit = vi.fn();
    render(
      <RegressionForm
        algorithms={[{ id: 'linear', label: 'Linear regression' }]}
        columns={['origin', 'price', 'tax']}
        columnMeta={[
          { name: 'origin', inferred_type: 'categorical', missing_percent: 0, unique_count: 3 },
          { name: 'price', inferred_type: 'float', missing_percent: 0, unique_count: 100 },
          { name: 'tax', inferred_type: 'float', missing_percent: 0, unique_count: 50 },
        ]}
        suggestions={{
          target_columns: ['origin'],
          feature_columns: ['price', 'tax'],
        }}
        loading={false}
        onSubmit={onSubmit}
      />,
    );

    expect(screen.getByLabelText('Target column (numeric)')).toHaveValue('tax');

    fireEvent.click(screen.getByRole('button', { name: /train regression model/i }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          targetColumn: 'tax',
          featureColumns: expect.not.arrayContaining(['tax']),
        }),
      );
    });
  });

  it('blocks submit when no feature columns are selected', async () => {
    const onSubmit = vi.fn();
    render(
      <RegressionForm
        algorithms={[{ id: 'linear', label: 'Linear regression' }]}
        columns={['price', 'tax']}
        columnMeta={[
          { name: 'price', inferred_type: 'float', missing_percent: 0, unique_count: 100 },
          { name: 'tax', inferred_type: 'float', missing_percent: 0, unique_count: 50 },
        ]}
        loading={false}
        onSubmit={onSubmit}
      />,
    );

    fireEvent.click(screen.getByRole('checkbox', { name: /^price/i }));
    fireEvent.click(screen.getByRole('button', { name: /train regression model/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(
      screen.getByText(/select at least one feature column other than the target/i),
    ).toBeInTheDocument();
  });

  it('unchecks columns and informs the user when the server rejects them', async () => {
    const onClearServerError = vi.fn();
    const { rerender } = render(
      <RegressionForm
        algorithms={[{ id: 'linear', label: 'Linear regression' }]}
        columns={['price', 'tax']}
        columnMeta={[
          { name: 'price', inferred_type: 'float', missing_percent: 0, unique_count: 100 },
          { name: 'tax', inferred_type: 'float', missing_percent: 0, unique_count: 50 },
        ]}
        loading={false}
        onSubmit={vi.fn()}
        onClearServerError={onClearServerError}
      />,
    );

    expect(screen.getByRole('checkbox', { name: /^price/i })).toBeChecked();

    rerender(
      <RegressionForm
        algorithms={[{ id: 'linear', label: 'Linear regression' }]}
        columns={['price', 'tax']}
        columnMeta={[
          { name: 'price', inferred_type: 'float', missing_percent: 0, unique_count: 100 },
          { name: 'tax', inferred_type: 'float', missing_percent: 0, unique_count: 50 },
        ]}
        loading={false}
        onSubmit={vi.fn()}
        serverError="Target column cannot also be a feature column"
        onClearServerError={onClearServerError}
      />,
    );

    await waitFor(() => {
      expect(screen.getByRole('checkbox', { name: /^price/i })).not.toBeChecked();
      expect(screen.getByText(/unchecked unsuitable columns: price/i)).toBeInTheDocument();
    });
    expect(onClearServerError).toHaveBeenCalled();
  });

  it('shows notice when high-missing columns are auto-unchecked on load', () => {
    render(
      <RegressionForm
        algorithms={[{ id: 'linear', label: 'Linear regression' }]}
        columns={['origin', 'price', 'tax']}
        columnMeta={[
          { name: 'origin', inferred_type: 'categorical', missing_percent: 0, unique_count: 3 },
          { name: 'price', inferred_type: 'float', missing_percent: 0, unique_count: 100 },
          { name: 'tax', inferred_type: 'float', missing_percent: 55, unique_count: 50 },
        ]}
        suggestions={{ feature_columns: ['origin', 'tax'] }}
        loading={false}
        onSubmit={vi.fn()}
      />,
    );

    expect(screen.getByRole('checkbox', { name: /tax/i })).not.toBeChecked();
    expect(screen.getByText(/unchecked unsuitable columns: tax \(55% missing\)/i)).toBeInTheDocument();
  });
});
