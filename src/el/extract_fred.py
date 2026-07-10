"""Extracción de series macroeconómicas desde la API de FRED."""

import logging
import os

import requests

from src.el.retry import retry_with_backoff
from src.models.schemas import FredObservation

logger = logging.getLogger(__name__)

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


@retry_with_backoff(max_attempts=3, base_delay=1.0)
def _fetch_observations(series_id: str, api_key: str, observation_start: str | None) -> dict:
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
    }
    if observation_start:
        params["observation_start"] = observation_start
    resp = requests.get(FRED_BASE_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def extract_fred_series(
    series_id: str,
    api_key: str | None = None,
    observation_start: str | None = None,
) -> list[FredObservation]:
    """Extrae observaciones históricas de una serie FRED.

    Args:
        series_id: id de la serie, ej. "FEDFUNDS", "UNRATE", "CPIAUCSL", "DGS10".
        api_key: API key de FRED; si no se pasa, se lee de la variable FRED_API_KEY.
        observation_start: fecha mínima (YYYY-MM-DD), opcional.

    Returns:
        Lista de FredObservation. valor es None cuando FRED devuelve "." (dato faltante).
    """
    key = api_key or os.environ["FRED_API_KEY"]
    data = _fetch_observations(series_id, key, observation_start)
    return [
        FredObservation(series_id=series_id, fecha=obs["date"], valor=obs["value"])
        for obs in data["observations"]
    ]
