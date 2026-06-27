import { BarChart } from './BarChart.jsx';

export function TrendBarChart({ points = [], title = 'Trend' }) {
  const values = points.map((point) => ({
    value: point.label,
    count: point.value,
  }));

  if (!values.length) {
    return null;
  }

  return <BarChart title={title} values={values} />;
}
