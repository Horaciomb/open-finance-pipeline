"""Extracción de precios diarios OHLCV desde Yahoo Finance (yfinance)."""

import logging

import yfinance as yf

from src.el.retry import retry_with_backoff
from src.models.schemas import PriceObservation

logger = logging.getLogger(__name__)


@retry_with_backoff(max_attempts=3, base_delay=1.0)
def _fetch_history(ticker: str, period: str):
    return yf.Ticker(ticker).history(period=period)


def extract_prices(tickers: list[str], period: str = "5d") -> list[PriceObservation]:
    """Extrae observaciones OHLCV diarias para una lista de tickers de Yahoo Finance.

    Args:
        tickers: símbolos de Yahoo Finance, ej. ["^GSPC", "BTC-USD", "CL=F"].
        period: ventana de yfinance, ej. "5d", "1y", "5y".

    Returns:
        Lista de PriceObservation, una por (ticker, fecha).
    """
    observations: list[PriceObservation] = []
    for ticker in tickers:
        history = _fetch_history(ticker, period)
        if history.empty:
            logger.warning("yfinance devolvió historial vacío para %s", ticker)
            continue
        for idx, row in history.iterrows():
            observations.append(
                PriceObservation(
                    ticker=ticker,
                    fecha=idx.date(),
                    open=row["Open"],
                    high=row["High"],
                    low=row["Low"],
                    close=row["Close"],
                    volume=int(row["Volume"]),
                )
            )
    return observations
