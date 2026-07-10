"""Modelos pydantic de respuesta del API (tipan Swagger / OpenAPI)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class HealthOut(BaseModel):
    """Estado del API y de la conexión a la base."""

    status: str = Field(examples=["ok"])
    database: str = Field(examples=["connected"])


class PriceOut(BaseModel):
    """Una observación OHLCV (de fct_daily_prices)."""

    ticker: str = Field(examples=["^GSPC"])
    fecha: date
    open: float
    high: float
    low: float
    close: float
    volume: int


class LatestPriceOut(BaseModel):
    """Último precio de un activo (de mart_market_overview)."""

    ticker: str = Field(examples=["^GSPC"])
    display_name: str = Field(examples=["S&P 500"])
    fecha: date
    close: float
    unit: str = Field(examples=["USD"])


class MacroObservationOut(BaseModel):
    """Una observación de una serie FRED (de fct_macro_indicators)."""

    series_id: str = Field(examples=["FEDFUNDS"])
    fecha: date
    valor: float | None = None


class LatestMacroOut(BaseModel):
    """Último valor de un indicador macro (de mart_market_overview)."""

    series_id: str = Field(examples=["FEDFUNDS"])
    display_name: str = Field(examples=["Tasa de fondos federales"])
    fecha: date
    valor: float
    unit: str = Field(examples=["%"])


class FxRateOut(BaseModel):
    """Última cotización de una casa de cambio boliviana."""

    fecha: date
    value: float


class FxLatestOut(BaseModel):
    """Brecha cambiaria de Bolivia: oficial vs. paralelo/binance."""

    oficial: FxRateOut | None = None
    binance: FxRateOut | None = None
    brecha_pct: float | None = None


class OverviewOut(BaseModel):
    """Snapshot combinado que consume el dashboard (/overview)."""

    prices: list[LatestPriceOut]
    macro: list[LatestMacroOut]
    fx: FxLatestOut
