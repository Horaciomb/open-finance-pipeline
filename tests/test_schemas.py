import math

import pytest
from pydantic import ValidationError

from src.models.schemas import PriceObservation


def test_price_observation_rejects_nan_ohlc():
    with pytest.raises(ValidationError):
        PriceObservation(
            ticker="CL=F",
            fecha="2024-01-02",
            open=math.nan,
            high=1.0,
            low=1.0,
            close=1.0,
            volume=100,
        )
