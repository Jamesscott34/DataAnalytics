const NUMERIC_TYPES = new Set(['integer', 'float']);

/**
 * Reasons a column should not be used as a regression feature.
 *
 * @param {{ name: string, inferred_type?: string, missing_percent?: number, unique_count?: number }} column
 * @param {string} targetColumn
 */
export function getRegressionFeatureIssues(column, targetColumn) {
  const issues = [];
  if (!column) {
    return issues;
  }
  if (column.name === targetColumn) {
    issues.push('is the target column');
  }
  if ((column.missing_percent ?? 0) >= 50) {
    issues.push(`${Math.round(column.missing_percent)}% missing`);
  }
  if ((column.unique_count ?? 2) <= 1) {
    issues.push('constant values');
  }
  return issues;
}

/**
 * Pick safe default features and track columns removed with reasons.
 */
export function buildRegressionFeatureSelection({
  columns,
  columnMeta,
  targetColumn,
  suggestions,
}) {
  const candidates = suggestions?.feature_columns?.length
    ? suggestions.feature_columns
    : columns.filter((name) => name !== targetColumn);

  const removed = [];
  const selected = [];

  for (const name of candidates) {
    const meta = columnMeta.find((column) => column.name === name);
    const issues = getRegressionFeatureIssues(meta ?? { name }, targetColumn);
    if (name === targetColumn) {
      const nonTargetIssues = issues.filter((issue) => issue !== 'is the target column');
      removed.push({ name, issues: nonTargetIssues.length ? nonTargetIssues : issues });
      continue;
    }
    if (issues.length) {
      removed.push({ name, issues });
    } else if (!selected.includes(name)) {
      selected.push(name);
    }
  }

  if (selected.length === 0) {
    for (const name of columns) {
      if (name === targetColumn || selected.includes(name)) {
        continue;
      }
      const meta = columnMeta.find((column) => column.name === name);
      const issues = getRegressionFeatureIssues(meta ?? { name }, targetColumn);
      if (issues.length) {
        continue;
      }
      selected.push(name);
      if (selected.length >= 3) {
        break;
      }
    }
  }

  return { selected, removed };
}

/**
 * Remove columns implicated by a server-side regression error.
 */
export function applyRegressionServerError(
  message,
  selectedFeatures,
  targetColumn,
  columnMeta = [],
) {
  const removed = [];
  let features = [...selectedFeatures];

  if (message.includes('Target column cannot also be a feature column')) {
    const overlapColumn = features.includes(targetColumn) ? targetColumn : features[0];
    if (overlapColumn) {
      features = features.filter((name) => name !== overlapColumn);
      removed.push({ name: overlapColumn, reason: 'cannot be both target and feature' });
    }
  }

  const notFoundMatch = message.match(/Feature column not found: ([^:]+)/);
  if (notFoundMatch) {
    const name = notFoundMatch[1].trim();
    if (features.includes(name)) {
      features = features.filter((column) => column !== name);
      removed.push({ name, reason: 'column not found in file' });
    }
  }

  const numericTargetMatch = message.match(/Target column must be numeric: (.+)/);
  if (numericTargetMatch) {
    removed.push({
      name: numericTargetMatch[1].trim(),
      reason: 'not numeric (pick a numeric target instead)',
    });
  }

  if (
    message.includes('Need at least four complete rows') ||
    message.includes('Not enough rows for train/test split')
  ) {
    const ranked = features
      .map((name) => ({
        name,
        missing: columnMeta.find((column) => column.name === name)?.missing_percent ?? 0,
      }))
      .sort((left, right) => right.missing - left.missing);

    for (const { name, missing } of ranked) {
      if (missing <= 0 || features.length <= 1) {
        continue;
      }
      features = features.filter((column) => column !== name);
      removed.push({ name, reason: 'too many missing values reduce usable rows' });
    }
  }

  return {
    features,
    removed,
    userMessage: formatRegressionColumnNotice(removed, message),
  };
}

/**
 * Strip unsafe columns before submit and explain what changed.
 */
export function sanitizeRegressionFeatures(selectedFeatures, targetColumn, columnMeta) {
  const removed = [];
  const selected = [];

  for (const name of selectedFeatures) {
    if (name === targetColumn) {
      removed.push({ name, issues: ['is the target column'] });
      continue;
    }
    const meta = columnMeta.find((column) => column.name === name);
    const issues = getRegressionFeatureIssues(meta ?? { name }, targetColumn);
    if (issues.length) {
      removed.push({ name, issues });
    } else {
      selected.push(name);
    }
  }

  return { selected, removed };
}

export function formatRegressionColumnNotice(removed, fallbackMessage = '') {
  if (!removed.length) {
    return fallbackMessage;
  }

  const lines = removed.map((item) => {
    if (item.issues?.length) {
      return `${item.name} (${item.issues.join(', ')})`;
    }
    return `${item.name} (${item.reason})`;
  });

  return `Unchecked unsuitable columns: ${lines.join('; ')}.${fallbackMessage ? ` ${fallbackMessage}` : ''}`;
}

export function isNumericRegressionTarget(columnMeta, name) {
  const meta = columnMeta?.find((column) => column.name === name);
  return meta ? NUMERIC_TYPES.has(meta.inferred_type) : true;
}

export function pickNumericTargets(columns, columnMeta) {
  if (columnMeta?.length) {
    return columnMeta
      .filter((column) => NUMERIC_TYPES.has(column.inferred_type))
      .map((column) => column.name);
  }
  return columns;
}
