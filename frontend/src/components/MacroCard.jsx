/** Tarjeta con el último valor de un indicador macro. */
export default function MacroCard({ metric }) {
  return (
    <div className="card">
      <h4>{metric.display_name}</h4>
      <p className="metric-value">
        {metric.valor}
        <span className="metric-unit">{metric.unit}</span>
      </p>
      <p className="metric-date">{metric.fecha}</p>
    </div>
  );
}
