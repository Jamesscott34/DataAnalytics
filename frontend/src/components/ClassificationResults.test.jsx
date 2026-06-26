import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ClassificationResults } from './ClassificationResults.jsx';

describe('ClassificationResults', () => {
  it('renders metrics, confusion matrix, and predictions', () => {
    render(
      <ClassificationResults
        result={{
          algorithm: 'logistic',
          target_column: 'label',
          feature_columns: ['x1', 'x2'],
          metrics: { accuracy: 0.9, precision: 0.88, recall: 0.9, f1: 0.89 },
          confusion_matrix: {
            labels: ['A', 'B'],
            matrix: [
              [3, 1],
              [0, 4],
            ],
          },
          classification_report: [
            { label: 'A', precision: 1, recall: 0.75, f1: 0.86, support: 4 },
            { label: 'B', precision: 0.8, recall: 1, f1: 0.89, support: 4 },
          ],
          predictions: [
            { actual: 'A', predicted: 'A', confidence: 0.91 },
            { actual: 'B', predicted: 'B', confidence: 0.87 },
          ],
        }}
      />,
    );

    expect(screen.getByText('Accuracy')).toBeInTheDocument();
    expect(screen.getByText('Confusion matrix')).toBeInTheDocument();
    expect(screen.getByText('0.91')).toBeInTheDocument();
  });
});
