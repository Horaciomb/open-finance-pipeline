"""Carga cruda a PostgreSQL (capa L del EL).

Inserta precios y observaciones FRED en el esquema ``openfin_raw`` con UPSERT
idempotente sobre las constraints UNIQUE. NO transforma datos de negocio (eso
es dbt). La conexión se recibe por parámetro (inyección de dependencias) para
que los tests usen un mock sin tocar una base real.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from psycopg2.extras import execute_values

from src.models.schemas import FredObservation, PriceObservation

if TYPE_CHECKING:
    from psycopg2.extensions import connection as PgConnection

logger = logging.getLogger(__name__)

# UPSERT de precios: idempotente sobre (ticker, fecha).
_UPSERT_PRICES = """
    INSERT INTO openfin_raw.prices
        (ticker, fecha, open, high, low, close, volume)
    VALUES %s
    ON CONFLICT (ticker, fecha) DO UPDATE SET
        open        = EXCLUDED.open,
        high        = EXCLUDED.high,
        low         = EXCLUDED.low,
        close       = EXCLUDED.close,
        volume      = EXCLUDED.volume,
        ingested_at = now()
"""

# UPSERT de observaciones FRED: idempotente sobre (series_id, fecha).
_UPSERT_FRED_OBSERVATIONS = """
    INSERT INTO openfin_raw.fred_observations
        (series_id, fecha, valor)
    VALUES %s
    ON CONFLICT (series_id, fecha) DO UPDATE SET
        valor       = EXCLUDED.valor,
        ingested_at = now()
"""


def upsert_prices(conn: PgConnection, rows: list[PriceObservation]) -> int:
    """Inserta/actualiza precios OHLCV de forma idempotente.

    Reejecutar con los mismos datos no duplica filas: el ``ON CONFLICT``
    actualiza la fila existente.

    Args:
        conn: Conexión psycopg2 abierta (inyectada; en tests, un mock).
        rows: Observaciones de precio a cargar.

    Returns:
        El número de filas procesadas.
    """
    if not rows:
        logger.info("Sin precios para cargar.")
        return 0

    values = [(r.ticker, r.fecha, r.open, r.high, r.low, r.close, r.volume) for r in rows]
    with conn.cursor() as cur:
        execute_values(cur, _UPSERT_PRICES, values)
    logger.info("Upsert de %d precios en openfin_raw.prices.", len(values))
    return len(values)


def upsert_fred_observations(conn: PgConnection, rows: list[FredObservation]) -> int:
    """Inserta/actualiza observaciones FRED de forma idempotente.

    Se cargan todas las observaciones, incluidas las de ``valor`` nulo (el
    descarte de nulos es trabajo de dbt en staging, no de Bronze).

    Args:
        conn: Conexión psycopg2 abierta (inyectada; en tests, un mock).
        rows: Observaciones FRED a cargar.

    Returns:
        El número de filas procesadas.
    """
    if not rows:
        logger.info("Sin observaciones FRED para cargar.")
        return 0

    values = [(r.series_id, r.fecha, r.valor) for r in rows]
    with conn.cursor() as cur:
        execute_values(cur, _UPSERT_FRED_OBSERVATIONS, values)
    logger.info("Upsert de %d observaciones en openfin_raw.fred_observations.", len(values))
    return len(values)
