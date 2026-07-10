"""Capa de servicios: SQL parametrizado contra los marts dbt (esquema openfin).

Toda la lógica de acceso a datos vive aquí; los routers sólo delegan. Las
consultas usan parámetros (nunca interpolación de strings) para evitar inyección.
"""

from __future__ import annotations

from datetime import date

from src.api.database import get_cursor


def get_price_series(
    ticker: str, desde: date | None = None, hasta: date | None = None
) -> list[dict]:
    """Serie histórica OHLCV de un ticker.

    Args:
        ticker: Símbolo de Yahoo Finance (ej. '^GSPC').
        desde: Fecha mínima (inclusive), opcional.
        hasta: Fecha máxima (inclusive), opcional.

    Returns:
        Observaciones ordenadas por fecha.
    """
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT ticker, fecha, open, high, low, close, volume
            FROM fct_daily_prices
            WHERE ticker = %(ticker)s
              AND (%(desde)s::date IS NULL OR fecha >= %(desde)s)
              AND (%(hasta)s::date IS NULL OR fecha <= %(hasta)s)
            ORDER BY fecha
            """,
            {"ticker": ticker, "desde": desde, "hasta": hasta},
        )
        return cur.fetchall()


def get_latest_prices() -> list[dict]:
    """Último precio de cada activo trackeado (de mart_market_overview).

    Returns:
        Un registro por activo, ordenado por ticker.
    """
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT metric_key AS ticker, metric_label AS display_name,
                   fecha, value AS close, unit
            FROM mart_market_overview
            WHERE metric_type = 'price'
            ORDER BY metric_key
            """
        )
        return cur.fetchall()


def get_macro_series(series_id: str) -> list[dict]:
    """Serie histórica de un indicador FRED.

    Args:
        series_id: Código de la serie (ej. 'FEDFUNDS').

    Returns:
        Observaciones ordenadas por fecha.
    """
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT series_id, fecha, valor
            FROM fct_macro_indicators
            WHERE series_id = %(series_id)s
            ORDER BY fecha
            """,
            {"series_id": series_id},
        )
        return cur.fetchall()


def get_latest_macro() -> list[dict]:
    """Último valor de cada indicador macro (de mart_market_overview).

    Returns:
        Un registro por indicador, ordenado por series_id.
    """
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT metric_key AS series_id, metric_label AS display_name,
                   fecha, value AS valor, unit
            FROM mart_market_overview
            WHERE metric_type = 'macro'
            ORDER BY metric_key
            """
        )
        return cur.fetchall()


def get_latest_fx() -> dict:
    """Última brecha cambiaria de Bolivia (de mart_market_overview).

    Returns:
        Dict con ``oficial``, ``binance`` (cada uno ``{fecha, value}`` o
        ``None`` si aún no hay dato) y ``brecha_pct``.
    """
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT metric_key, fecha, value, secondary_value
            FROM mart_market_overview
            WHERE metric_type = 'fx'
            """
        )
        rows = {r["metric_key"]: r for r in cur.fetchall()}

    oficial = rows.get("oficial")
    binance = rows.get("binance")
    return {
        "oficial": {"fecha": oficial["fecha"], "value": oficial["value"]} if oficial else None,
        "binance": {"fecha": binance["fecha"], "value": binance["value"]} if binance else None,
        "brecha_pct": binance["secondary_value"] if binance else None,
    }


def get_overview() -> dict:
    """Snapshot combinado para el dashboard: precios, macro y brecha FX.

    Returns:
        Dict con las claves ``prices``, ``macro`` y ``fx``.
    """
    return {
        "prices": get_latest_prices(),
        "macro": get_latest_macro(),
        "fx": get_latest_fx(),
    }
