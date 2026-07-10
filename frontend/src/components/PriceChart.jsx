import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

/** Gráfico de líneas del histórico de cierre de un ticker. */
export default function PriceChart({ ticker, displayName, series }) {
  const data = series.map((row) => ({ fecha: row.fecha, close: row.close }));

  return (
    <div className="card">
      <h3>{displayName ?? ticker}</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="fecha" tick={{ fontSize: 12 }} />
          <YAxis domain={["auto", "auto"]} tick={{ fontSize: 12 }} />
          <Tooltip />
          <Line type="monotone" dataKey="close" stroke="#4f7cff" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
