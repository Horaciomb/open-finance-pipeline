/** Banner con la brecha cambiaria de Bolivia: oficial vs. paralelo/binance. */
export default function FxGapBanner({ fx }) {
  if (!fx || (!fx.oficial && !fx.binance)) {
    return null;
  }

  return (
    <div className="fx-banner">
      <div>
        <span className="fx-label">Oficial</span>
        <span className="fx-value">{fx.oficial ? `Bs ${fx.oficial.value}` : "—"}</span>
      </div>
      <div>
        <span className="fx-label">Paralelo (Binance)</span>
        <span className="fx-value">{fx.binance ? `Bs ${fx.binance.value}` : "—"}</span>
      </div>
      {fx.brecha_pct != null && (
        <div className="fx-gap">
          <span className="fx-label">Brecha</span>
          <span className="fx-value">{fx.brecha_pct}%</span>
        </div>
      )}
    </div>
  );
}
