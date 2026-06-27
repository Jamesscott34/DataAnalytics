import { BarChart } from './BarChart.jsx';

export function ResidualChart({ residuals = [] }) {
  const values = residuals.map((residual, index) => ({
    value: `Row ${index + 1}`,
    count: Math.abs(residual),
  }));

  if (!values.length) {
    return null;
  }

  return <BarChart title="Residual magnitude" values={values} />;
}
