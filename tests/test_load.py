from datetime import date

from src.el.load import upsert_fred_observations, upsert_prices
from src.models.schemas import FredObservation, PriceObservation


def test_upsert_prices_calls_execute_values_with_rows(mocker):
    execute_values_mock = mocker.patch("src.el.load.execute_values")
    conn = mocker.MagicMock()

    rows = [
        PriceObservation(
            ticker="^GSPC", fecha=date(2024, 1, 2), open=1, high=2, low=0.5, close=1.5, volume=100
        )
    ]

    n = upsert_prices(conn, rows)

    assert n == 1
    execute_values_mock.assert_called_once()
    values = execute_values_mock.call_args.args[2]
    assert values == [("^GSPC", date(2024, 1, 2), 1, 2, 0.5, 1.5, 100)]


def test_upsert_prices_skips_empty_list(mocker):
    execute_values_mock = mocker.patch("src.el.load.execute_values")
    conn = mocker.MagicMock()

    n = upsert_prices(conn, [])

    assert n == 0
    execute_values_mock.assert_not_called()


def test_upsert_fred_observations_calls_execute_values_with_rows(mocker):
    execute_values_mock = mocker.patch("src.el.load.execute_values")
    conn = mocker.MagicMock()

    rows = [
        FredObservation(series_id="DGS10", fecha=date(2024, 1, 2), valor=3.95),
        FredObservation(series_id="DGS10", fecha=date(2024, 1, 1), valor=None),
    ]

    n = upsert_fred_observations(conn, rows)

    assert n == 2
    values = execute_values_mock.call_args.args[2]
    assert values == [
        ("DGS10", date(2024, 1, 2), 3.95),
        ("DGS10", date(2024, 1, 1), None),
    ]


def test_upsert_fred_observations_skips_empty_list(mocker):
    execute_values_mock = mocker.patch("src.el.load.execute_values")
    conn = mocker.MagicMock()

    n = upsert_fred_observations(conn, [])

    assert n == 0
    execute_values_mock.assert_not_called()
