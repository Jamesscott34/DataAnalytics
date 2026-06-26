import { BarChart } from './BarChart.jsx';
import { HistogramChart } from './HistogramChart.jsx';

/**
 * ColumnChart
 *
 * Renders the appropriate chart for backend chart_data entries.
 */
export function ColumnChart({ columnName, chart }) {
  if (!chart) {
    return null;
  }

  if (chart.type === 'histogram') {
    return <HistogramChart title={columnName} bins={chart.bins ?? []} />;
  }

  if (chart.type === 'bar') {
    return <BarChart title={columnName} values={chart.values ?? []} />;
  }

  return null;
}
