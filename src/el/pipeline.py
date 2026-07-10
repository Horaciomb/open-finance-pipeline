"""Orquestación del EL: extract → load. La transformación (T) la hace dbt.

Lee ``DATABASE_URL`` del entorno, abre una conexión a la instancia Supabase
compartida, extrae precios (Yahoo Finance) u observaciones (FRED) y las carga
crudas en ``openfin_raw``. Dos entry points separados porque corren en crons
distintos: precios a diario, FRED semanal.

Uso:
    python -m src.el.pipeline prices
    python -m src.el.pipeline fred
"""

from __future__ import annotations

import argparse
import logging
import os

import psycopg2

from src.el.extract_fred import extract_fred_series
from src.el.extract_prices import extract_prices
from src.el.load import upsert_fred_observations, upsert_prices

logger = logging.getLogger(__name__)

DEFAULT_TICKERS = ["^GSPC", "BTC-USD", "CL=F", "GC=F"]
DEFAULT_SERIES = ["FEDFUNDS", "UNRATE", "CPIAUCSL", "DGS10"]


def _resolve_database_url(database_url: str | None) -> str:
    database_url = database_url or os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "Falta DATABASE_URL. Expórtala antes de correr el pipeline (ver .env.example)."
        )
    return database_url


def run_daily_prices(
    database_url: str | None = None,
    tickers: list[str] = DEFAULT_TICKERS,
    period: str = "5d",
) -> dict[str, int]:
    """Ejecuta el EL diario de precios: extrae de yfinance y carga en openfin_raw.

    Args:
        database_url: Connection string. Si es ``None`` se lee de ``DATABASE_URL``.
        tickers: Tickers de Yahoo Finance a extraer.
        period: Ventana de yfinance, ej. "5d".

    Returns:
        Conteo cargado: ``{"prices": n}``.
    """
    database_url = _resolve_database_url(database_url)

    logger.info("Extrayendo precios de %d tickers...", len(tickers))
    observations = extract_prices(tickers, period=period)
    logger.info("%d observaciones de precio extraídas.", len(observations))

    conn = psycopg2.connect(database_url, options="-c search_path=openfin_raw")
    try:
        n_prices = upsert_prices(conn, observations)
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("El pipeline de precios falló; se hizo rollback.")
        raise
    finally:
        conn.close()

    result = {"prices": n_prices}
    logger.info("Pipeline de precios completado: %s", result)
    return result


def run_weekly_fred(
    database_url: str | None = None,
    series_ids: list[str] = DEFAULT_SERIES,
    observation_start: str | None = None,
) -> dict[str, int]:
    """Ejecuta el EL semanal de FRED: extrae de la API y carga en openfin_raw.

    Args:
        database_url: Connection string. Si es ``None`` se lee de ``DATABASE_URL``.
        series_ids: Series FRED a extraer.
        observation_start: Fecha mínima (YYYY-MM-DD), opcional.

    Returns:
        Conteo cargado: ``{"fred_observations": n}``.
    """
    database_url = _resolve_database_url(database_url)

    logger.info("Extrayendo %d series FRED...", len(series_ids))
    observations = []
    for series_id in series_ids:
        observations.extend(
            extract_fred_series(series_id, observation_start=observation_start)
        )
    logger.info("%d observaciones FRED extraídas.", len(observations))

    conn = psycopg2.connect(database_url, options="-c search_path=openfin_raw")
    try:
        n_fred = upsert_fred_observations(conn, observations)
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("El pipeline de FRED falló; se hizo rollback.")
        raise
    finally:
        conn.close()

    result = {"fred_observations": n_fred}
    logger.info("Pipeline de FRED completado: %s", result)
    return result


def main() -> None:
    """Punto de entrada CLI: configura logging y despacha al subcomando."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("prices", help="Extrae y carga precios diarios (yfinance).")
    subparsers.add_parser("fred", help="Extrae y carga observaciones FRED semanales.")
    args = parser.parse_args()

    if args.command == "prices":
        run_daily_prices()
    elif args.command == "fred":
        run_weekly_fred()


if __name__ == "__main__":
    main()
