"""Modelos pydantic para validar datos extraídos antes de cargarlos a Bronze."""

from datetime import date

from pydantic import BaseModel, field_validator


class PriceObservation(BaseModel):
    """Una observación diaria OHLCV para un ticker de Yahoo Finance."""

    ticker: str
    fecha: date
    open: float
    high: float
    low: float
    close: float
    volume: int


class FredObservation(BaseModel):
    """Una observación de una serie FRED.

    valor es None cuando la API de FRED devuelve el literal "." (dato faltante).
    """

    series_id: str
    fecha: date
    valor: float | None

    @field_validator("valor", mode="before")
    @classmethod
    def parse_missing_value(cls, v: object) -> float | None:
        if v == ".":
            return None
        return v
