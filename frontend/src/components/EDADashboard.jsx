import { ColumnChart } from './charts/ColumnChart.jsx';
import { CorrelationHeatmap } from './charts/CorrelationHeatmap.jsx';
import { LineChart } from './charts/LineChart.jsx';
import { MissingValuesChart } from './charts/MissingValuesChart.jsx';
import { ScatterChart } from './charts/ScatterChart.jsx';

/**
 * EDADashboard
 *
 * Summary cards, column table, quality warnings, and charts.
 */
export function EDADashboard({ eda, suggestions }) {
  if (!eda) {
    return null;
  }

  const {
    summary,
    columns,
    quality_warnings: warnings,
    chart_data: chartData,
    dataset_charts: datasetCharts,
  } = eda;
  const chartColumns = Object.keys(chartData ?? {});

  return (
    <div className="eda-dashboard">
      <section className="eda-summary-grid" aria-label="Dataset summary">
        <article className="eda-stat-card">
          <h3>Rows</h3>
          <p>{summary.row_count}</p>
        </article>
        <article className="eda-stat-card">
          <h3>Columns</h3>
          <p>{summary.column_count}</p>
        </article>
        <article className="eda-stat-card">
          <h3>Missing cells</h3>
          <p>
            {summary.missing_cells} ({summary.missing_percent.toFixed(1)}%)
          </p>
        </article>
        <article className="eda-stat-card">
          <h3>Duplicate rows</h3>
          <p>{summary.duplicate_row_count}</p>
        </article>
      </section>

      {eda.cached && (
        <p className="eda-cache-note" role="status">
          Showing cached analysis from {new Date(eda.analyzed_at).toLocaleString()}.
        </p>
      )}

      {eda.sampled && (
        <p className="eda-cache-note" role="status">
          Large dataset: analysis used a row sample for performance.
        </p>
      )}

      {warnings?.length > 0 && (
        <section className="panel-card eda-warnings">
          <h2>Quality warnings</h2>
          <ul>
            {warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </section>
      )}

      {suggestions && (
        <section className="panel-card eda-suggestions">
          <h2>Suggested analyses</h2>
          <div className="eda-suggestion-tags">
            {suggestions.suggested_analyses.map((item) => (
              <span key={item} className="eda-tag">
                {item}
              </span>
            ))}
          </div>
          {suggestions.target_columns.length > 0 && (
            <p>
              <strong>Target columns:</strong> {suggestions.target_columns.join(', ')}
            </p>
          )}
          {suggestions.feature_columns.length > 0 && (
            <p>
              <strong>Feature columns:</strong> {suggestions.feature_columns.join(', ')}
            </p>
          )}
        </section>
      )}

      <section className="panel-card">
        <h2>Column overview</h2>
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">Column</th>
                <th scope="col">Type</th>
                <th scope="col">Missing</th>
                <th scope="col">Unique</th>
                <th scope="col">Stats</th>
              </tr>
            </thead>
            <tbody>
              {columns.map((column) => (
                <tr key={column.name}>
                  <th scope="row">{column.name}</th>
                  <td>{column.inferred_type}</td>
                  <td>
                    {column.missing_count} ({column.missing_percent.toFixed(1)}%)
                  </td>
                  <td>{column.unique_count}</td>
                  <td>{formatColumnStats(column)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel-card">
        <h2>Charts</h2>
        <div className="chart-grid">
          <MissingValuesChart columns={columns} />
          {datasetCharts?.correlation && (
            <CorrelationHeatmap
              labels={datasetCharts.correlation.labels}
              matrix={datasetCharts.correlation.matrix}
            />
          )}
          {datasetCharts?.scatter?.map((chart) => (
            <ScatterChart
              key={`${chart.x_column}-${chart.y_column}`}
              title={`${chart.x_column} vs ${chart.y_column}`}
              xColumn={chart.x_column}
              yColumn={chart.y_column}
              points={chart.points}
            />
          ))}
          {datasetCharts?.line?.map((chart) => (
            <LineChart
              key={`${chart.x_column}-${chart.y_column}`}
              title={`${chart.y_column} over ${chart.x_column}`}
              xColumn={chart.x_column}
              yColumn={chart.y_column}
              points={chart.points}
            />
          ))}
          {chartColumns.map((columnName) => (
            <ColumnChart
              key={columnName}
              columnName={columnName}
              chart={chartData[columnName]}
            />
          ))}
        </div>
      </section>
    </div>
  );
}

function formatColumnStats(column) {
  if (column.numeric_stats) {
    const stats = column.numeric_stats;
    return `mean ${stats.mean ?? 'n/a'}, min ${stats.min ?? 'n/a'}, max ${stats.max ?? 'n/a'}`;
  }
  if (column.categorical_stats) {
    const top = column.categorical_stats.top_values[0];
    return top ? `top: ${top.value} (${top.count})` : 'n/a';
  }
  return column.sample_values.slice(0, 2).join(', ') || 'n/a';
}
