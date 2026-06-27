import { describe, expect, it } from 'vitest';
import {
  applyRegressionServerError,
  buildRegressionFeatureSelection,
  sanitizeRegressionFeatures,
} from './regressionColumnRules.js';

describe('regressionColumnRules', () => {
  it('skips high-missing and target columns from initial selection', () => {
    const { selected, removed } = buildRegressionFeatureSelection({
      columns: ['origin', 'price', 'tax'],
      columnMeta: [
        { name: 'origin', inferred_type: 'categorical', missing_percent: 0, unique_count: 3 },
        { name: 'price', inferred_type: 'float', missing_percent: 0, unique_count: 100 },
        { name: 'tax', inferred_type: 'float', missing_percent: 60, unique_count: 50 },
      ],
      targetColumn: 'price',
      suggestions: {
        feature_columns: ['origin', 'tax', 'price'],
      },
    });

    expect(selected).toEqual(['origin']);
    expect(removed).toEqual([
      { name: 'tax', issues: ['60% missing'] },
      { name: 'price', issues: ['is the target column'] },
    ]);
  });

  it('unchecks target overlap after server error', () => {
    const result = applyRegressionServerError(
      'Target column cannot also be a feature column',
      ['price', 'tax'],
      'price',
      [],
    );

    expect(result.features).toEqual(['tax']);
    expect(result.userMessage).toMatch(/Unchecked unsuitable columns: price/);
  });

  it('removes high-missing features when row count is too low', () => {
    const result = applyRegressionServerError(
      'Need at least four complete rows for regression',
      ['origin', 'tax', 'carrier'],
      'price',
      [
        { name: 'origin', missing_percent: 0 },
        { name: 'tax', missing_percent: 40 },
        { name: 'carrier', missing_percent: 10 },
      ],
    );

    expect(result.features).not.toContain('tax');
    expect(result.userMessage).toMatch(/Unchecked unsuitable columns/);
  });

  it('sanitizes selected features before submit', () => {
    const { selected, removed } = sanitizeRegressionFeatures(
      ['origin', 'price'],
      'price',
      [
        { name: 'origin', missing_percent: 0, unique_count: 3 },
        { name: 'price', missing_percent: 0, unique_count: 100 },
      ],
    );

    expect(selected).toEqual(['origin']);
    expect(removed[0].name).toBe('price');
  });
});
