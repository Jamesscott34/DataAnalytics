import { describe, expect, it } from 'vitest';
import {
  buildSelectedRowsQuery,
  buildSqlCommandList,
  sqlLiteral,
} from './sqlQueryBuilder.js';

describe('sqlQueryBuilder', () => {
  it('escapes string literals', () => {
    expect(sqlLiteral("O'Brien")).toBe("'O''Brien'");
    expect(sqlLiteral(12)).toBe('12');
  });

  it('builds OR filter for selected rows', () => {
    const sql = buildSelectedRowsQuery(
      'csv_import_1',
      ['name', 'value'],
      [
        ['alpha', '1'],
        ['beta', '2'],
      ],
      new Set([0, 1]),
    );
    expect(sql).toContain('WHERE');
    expect(sql).toContain('"name" = \'alpha\'');
    expect(sql).toContain(' OR ');
  });

  it('includes column-specific commands', () => {
    const commands = buildSqlCommandList('csv_import_1', ['region']);
    expect(commands.some((command) => command.sql.includes('GROUP BY "region"'))).toBe(true);
  });
});
