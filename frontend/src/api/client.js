const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function getJson(path) {
  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) {
    throw new Error(`${path} respondió ${res.status}`);
  }
  return res.json();
}

/** Snapshot combinado: últimos precios, últimos indicadores macro y brecha FX. */
export function fetchOverview() {
  return getJson("/overview");
}

/** Serie histórica OHLCV de un ticker, para el gráfico de líneas. */
export function fetchPriceSeries(ticker) {
  return getJson(`/prices/${encodeURIComponent(ticker)}`);
}
