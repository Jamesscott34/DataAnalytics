export function KPICard({ item }) {
  return (
    <article className="eda-stat-card">
      <h3>{item.label}</h3>
      <p>
        {item.value}
        {item.unit === 'percent' ? '%' : ''}
      </p>
    </article>
  );
}
