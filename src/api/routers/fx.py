"""Endpoint de la brecha cambiaria de Bolivia. Lee de mart_market_overview
(dbt ya resolvió el cruce cross-schema con fx.exchange_rates); no se consulta
el esquema fx directamente desde el API."""

from __future__ import annotations

from fastapi import APIRouter

from src.api import services
from src.api.schemas import FxLatestOut

router = APIRouter(prefix="/fx", tags=["fx"])


@router.get("/latest", response_model=FxLatestOut)
def get_latest_fx() -> dict:
    """Última brecha cambiaria (oficial vs. paralelo) de Bolivia."""
    return services.get_latest_fx()
