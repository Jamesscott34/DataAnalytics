import { BarChart } from './BarChart.jsx';

export function TopPairsChart({ pairs = [], title = 'Top scores' }) {
  const values = pairs.map((pair) => ({
    value: `${pair.left} / ${pair.right}`,
    count: pair.score,
  }));

  if (!values.length) {
    return null;
  }

  return <BarChart title={title} values={values} />;
}
