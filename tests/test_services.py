from contextlib import contextmanager

from src.api import services


def test_get_overview_shares_one_cursor_and_sets_repeatable_read(mocker):
    """Las tres consultas de /overview deben compartir una única transacción
    REPEATABLE READ para no mezclar datos de antes/después de un dbt build
    concurrente que recrea mart_market_overview."""
    cur = mocker.MagicMock()
    cur.fetchall.return_value = []

    @contextmanager
    def fake_get_cursor():
        yield cur

    mocker.patch("src.api.services.get_cursor", side_effect=fake_get_cursor)

    result = services.get_overview()

    assert result == {
        "prices": [],
        "macro": [],
        "fx": {"oficial": None, "binance": None, "brecha_pct": None},
    }
    # 1 SET + 3 SELECTs, todos sobre el mismo cursor/transacción.
    executed = [call.args[0] for call in cur.execute.call_args_list]
    assert "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ" in executed[0]
    assert len(executed) == 4
