import math

import pandas as pd

from src.el.extract_prices import extract_prices
from src.models.schemas import PriceObservation


def _fake_history():
    index = pd.to_datetime(["2024-01-02", "2024-01-03"])
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0],
            "High": [102.0, 103.0],
            "Low": [99.0, 100.0],
            "Close": [101.0, 102.0],
            "Volume": [1000, 1100],
        },
        index=index,
    )


def test_extract_prices_returns_validated_observations(mocker):
    mocker.patch(
        "src.el.extract_prices.yf.Ticker",
        return_value=mocker.Mock(history=mocker.Mock(return_value=_fake_history())),
    )

    result = extract_prices(["^GSPC"], period="5d")

    assert len(result) == 2
    assert all(isinstance(o, PriceObservation) for o in result)
    assert result[0].ticker == "^GSPC"
    assert result[0].close == 101.0
    assert result[0].volume == 1000


def test_extract_prices_skips_empty_history(mocker):
    mocker.patch(
        "src.el.extract_prices.yf.Ticker",
        return_value=mocker.Mock(history=mocker.Mock(return_value=pd.DataFrame())),
    )

    result = extract_prices(["FAKE"], period="5d")

    assert result == []


def test_extract_prices_skips_rows_with_nan_without_crashing(mocker):
    """Una fila con NaN (yfinance en tickers ilíquidos) no debe abortar el batch."""
    index = pd.to_datetime(["2024-01-02", "2024-01-03"])
    history = pd.DataFrame(
        {
            "Open": [100.0, math.nan],
            "High": [102.0, 103.0],
            "Low": [99.0, 100.0],
            "Close": [101.0, 102.0],
            "Volume": [1000, math.nan],
        },
        index=index,
    )
    mocker.patch(
        "src.el.extract_prices.yf.Ticker",
        return_value=mocker.Mock(history=mocker.Mock(return_value=history)),
    )

    result = extract_prices(["CL=F"], period="5d")

    assert len(result) == 1
    assert result[0].fecha.isoformat() == "2024-01-02"
