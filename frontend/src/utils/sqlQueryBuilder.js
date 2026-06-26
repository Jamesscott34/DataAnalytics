/**
 * Build SQL literals and queries from table metadata and selected rows.
 */

/**
 * @param {unknown} value
 * @returns {string}
 */
export function sqlLiteral(value) {
  if (value === null || value === undefined || value === '') {
    return "''";
  }
  const text = String(value).trim();
  const asNumber = Number(text);
  if (text !== '' && !Number.isNaN(asNumber) && String(asNumber) === text) {
    return String(asNumber);
  }
  return `'${text.replace(/'/g, "''")}'`;
}

/**
 * @param {string[]} columns
 * @param {Array<unknown>} row
 * @returns {string}
 */
export function buildRowCondition(columns, row) {
  const parts = columns.map((column, index) => {
    const value = row[index];
    if (value === null || value === undefined || String(value).trim() === '') {
      return `("${column}" IS NULL OR "${column}" = '')`;
    }
    return `"${column}" = ${sqlLiteral(value)}`;
  });
  return `(${parts.join(' AND ')})`;
}

/**
 * @param {string} tableName
 * @param {string[]} columns
 * @param {Array<Array<unknown>>} rows
 * @param {Iterable<number>} selectedIndexes
 * @returns {string}
 */
export function buildSelectedRowsQuery(tableName, columns, rows, selectedIndexes) {
  const indexes = [...selectedIndexes].sort((a, b) => a - b);
  if (indexes.length === 0) {
    return `SELECT * FROM "${tableName}"`;
  }
  const conditions = indexes.map((index) => buildRowCondition(columns, rows[index]));
  return `SELECT * FROM "${tableName}" WHERE ${conditions.join(' OR ')}`;
}

/**
 * @param {string} tableName
 * @param {string[]} columns
 * @returns {Array<{ id: string, label: string, sql: string, description: string }>}
 */
export function buildSqlCommandList(tableName, columns = []) {
  const commands = [
    {
      id: 'view_all',
      label: 'SELECT * — all rows',
      description: 'Return every imported row.',
      sql: `SELECT * FROM "${tableName}"`,
    },
    {
      id: 'count_rows',
      label: 'COUNT(*) — row total',
      description: 'Count how many rows are in the table.',
      sql: `SELECT COUNT(*) AS row_count FROM "${tableName}"`,
    },
    {
      id: 'distinct_all',
      label: 'SELECT DISTINCT *',
      description: 'Return unique row combinations.',
      sql: `SELECT DISTINCT * FROM "${tableName}"`,
    },
    {
      id: 'limit_10',
      label: 'SELECT * LIMIT 10',
      description: 'Preview the first ten rows.',
      sql: `SELECT * FROM "${tableName}" LIMIT 10`,
    },
    {
      id: 'table_info',
      label: 'PRAGMA table_info',
      description: 'Show column names and types.',
      sql: `PRAGMA table_info('${tableName}')`,
    },
  ];

  for (const column of columns) {
    commands.push({
      id: `select_${column}`,
      label: `SELECT "${column}"`,
      description: `Return values from the ${column} column only.`,
      sql: `SELECT "${column}" FROM "${tableName}"`,
    });
    commands.push({
      id: `group_${column}`,
      label: `GROUP BY "${column}"`,
      description: `Count rows grouped by ${column}.`,
      sql: `SELECT "${column}", COUNT(*) AS row_count FROM "${tableName}" GROUP BY "${column}" ORDER BY row_count DESC`,
    });
    commands.push({
      id: `order_${column}`,
      label: `ORDER BY "${column}"`,
      description: `Sort all rows by ${column}.`,
      sql: `SELECT * FROM "${tableName}" ORDER BY "${column}" ASC`,
    });
  }

  return commands;
}

/**
 * @param {string} tableName
 * @param {string} column
 * @returns {string}
 */
export function buildSelectColumnQuery(tableName, column) {
  return `SELECT "${column}" FROM "${tableName}"`;
}
