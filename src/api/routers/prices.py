"""Endpoints de precios de mercado. Sólo delegan a services."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException

from src.api import services
from src.api.schemas import LatestPriceOut, PriceOut

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("/latest", response_model=list[LatestPriceOut])
def get_latest_prices() -> list[dict]:
    """Último precio de cada activo trackeado."""
    return services.get_latest_prices()


@router.get("/{ticker}", response_model=list[PriceOut])
def get_price_series(
    ticker: str, desde: date | None = None, hasta: date | None = None
) -> list[dict]:
    """Serie histórica OHLCV de un ticker."""
    rows = services.get_price_series(ticker, desde=desde, hasta=hasta)
    if not rows:
        raise HTTPException(status_code=404, detail=f"Sin datos para el ticker '{ticker}'.")
    return rows
