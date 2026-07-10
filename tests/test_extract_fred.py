import requests

from src.el.extract_fred import extract_fred_series
from src.models.schemas import FredObservation


class _FakeResponse:
    def __init__(self, observations):
        self._observations = observations

    def raise_for_status(self):
        pass

    def json(self):
        return {"observations": self._observations}


def test_extract_fred_series_casts_missing_value_to_none(mocker):
    mocker.patch(
        "src.el.extract_fred.requests.get",
        return_value=_FakeResponse(
            [
                {"date": "2024-01-02", "value": "3.95"},
                {"date": "2024-01-01", "value": "."},
            ]
        ),
    )

    result = extract_fred_series("DGS10", api_key="fake-key")

    assert len(result) == 2
    assert all(isinstance(o, FredObservation) for o in result)
    assert result[0].valor == 3.95
    assert result[1].valor is None


def test_extract_fred_series_retries_on_failure(mocker):
    mocker.patch("src.el.retry.time.sleep", return_value=None)
    call_count = {"n": 0}

    def flaky_get(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] < 2:
            raise requests.ConnectionError("boom")
        return _FakeResponse([{"date": "2024-01-02", "value": "1.0"}])

    mocker.patch("src.el.extract_fred.requests.get", side_effect=flaky_get)

    result = extract_fred_series("FEDFUNDS", api_key="fake-key")

    assert len(result) == 1
    assert call_count["n"] == 2
