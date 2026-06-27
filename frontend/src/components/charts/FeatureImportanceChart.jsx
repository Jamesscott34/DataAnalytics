import { BarChart } from './BarChart.jsx';

export function FeatureImportanceChart({ data, title = 'Feature importance' }) {
  const values = data.map((item) => ({
    value: item.feature,
    count: item.importance,
  }));

  if (values.length === 0) {
    return (
      <p className="upload-help">
        Feature importance is not available for this result.
      </p>
    );
  }

  return <BarChart title={title} values={values} />;
}
