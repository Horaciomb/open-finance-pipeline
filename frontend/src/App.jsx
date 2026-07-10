import { useEffect, useState } from "react";
import { fetchOverview, fetchPriceSeries } from "./api/client";
import FxGapBanner from "./components/FxGapBanner";
import MacroCard from "./components/MacroCard";
import PriceChart from "./components/PriceChart";
import "./App.css";

// Cuántos activos mostrar en el gráfico de líneas (CLAUDE.md: "1-2 activos").
const CHART_TICKER_COUNT = 2;

function App() {
  const [overview, setOverview] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchOverview()
      .then(async (data) => {
        setOverview(data);
        const tickers = data.prices.slice(0, CHART_TICKER_COUNT);
        const series = await Promise.all(
          tickers.map((p) => fetchPriceSeries(p.ticker))
        );
        setChartData(
          tickers.map((p, i) => ({
            ticker: p.ticker,
            displayName: p.display_name,
            series: series[i],
          }))
        );
      })
      .catch((err) => setError(err.message));
  }, []);

  if (error) {
    return <p className="status">Error al cargar el dashboard: {error}</p>;
  }

  if (!overview) {
    return <p className="status">Cargando...</p>;
  }

  return (
    <div className="dashboard">
      <header>
        <h1>Open Finance Pipeline</h1>
        <p className="subtitle">Mercados, indicadores macro y brecha cambiaria de Bolivia</p>
      </header>

      <FxGapBanner fx={overview.fx} />

      <section className="charts">
        {chartData.map((c) => (
          <PriceChart
            key={c.ticker}
            ticker={c.ticker}
            displayName={c.displayName}
            series={c.series}
          />
        ))}
      </section>

      <section className="macro-grid">
        {overview.macro.map((m) => (
          <MacroCard key={m.series_id} metric={m} />
        ))}
      </section>
    </div>
  );
}

export default App;
