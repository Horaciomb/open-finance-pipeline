"""Endpoints de indicadores macro (FRED). Sólo delegan a services."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.api import services
from src.api.schemas import LatestMacroOut, MacroObservationOut

router = APIRouter(prefix="/macro", tags=["macro"])


@router.get("/latest", response_model=list[LatestMacroOut])
def get_latest_macro() -> list[dict]:
    """Último valor de cada indicador macro trackeado."""
    return services.get_latest_macro()


@router.get("/{series_id}", response_model=list[MacroObservationOut])
def get_macro_series(series_id: str) -> list[dict]:
    """Serie histórica de un indicador FRED."""
    rows = services.get_macro_series(series_id)
    if not rows:
        raise HTTPException(status_code=404, detail=f"Sin datos para la serie '{series_id}'.")
    return rows
