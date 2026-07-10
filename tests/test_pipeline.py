from src.el import pipeline


def test_default_tickers_and_series_are_immutable_tuples():
    """DEFAULT_TICKERS/DEFAULT_SERIES no deben ser listas (mutable-default footgun)."""
    assert isinstance(pipeline.DEFAULT_TICKERS, tuple)
    assert isinstance(pipeline.DEFAULT_SERIES, tuple)


def test_run_daily_prices_commits_via_shared_connection(mocker):
    mocker.patch("src.el.pipeline.extract_prices", return_value=["obs"])
    upsert_mock = mocker.patch("src.el.pipeline.upsert_prices", return_value=1)
    conn_mock = mocker.MagicMock()
    mocker.patch("src.el.pipeline.psycopg2.connect", return_value=conn_mock)

    result = pipeline.run_daily_prices(database_url="postgresql://fake", tickers=["^GSPC"])

    assert result == {"prices": 1}
    upsert_mock.assert_called_once_with(conn_mock, ["obs"])
    conn_mock.commit.assert_called_once()
    conn_mock.close.assert_called_once()
    conn_mock.rollback.assert_not_called()


def test_run_daily_prices_rolls_back_on_upsert_failure(mocker):
    mocker.patch("src.el.pipeline.extract_prices", return_value=["obs"])
    mocker.patch("src.el.pipeline.upsert_prices", side_effect=RuntimeError("boom"))
    conn_mock = mocker.MagicMock()
    mocker.patch("src.el.pipeline.psycopg2.connect", return_value=conn_mock)

    try:
        pipeline.run_daily_prices(database_url="postgresql://fake", tickers=["^GSPC"])
    except RuntimeError:
        pass

    conn_mock.rollback.assert_called_once()
    conn_mock.close.assert_called_once()
    conn_mock.commit.assert_not_called()


def test_run_weekly_fred_commits_via_shared_connection(mocker):
    mocker.patch("src.el.pipeline.extract_fred_series", return_value=["obs"])
    upsert_mock = mocker.patch("src.el.pipeline.upsert_fred_observations", return_value=1)
    conn_mock = mocker.MagicMock()
    mocker.patch("src.el.pipeline.psycopg2.connect", return_value=conn_mock)

    result = pipeline.run_weekly_fred(database_url="postgresql://fake", series_ids=["FEDFUNDS"])

    assert result == {"fred_observations": 1}
    upsert_mock.assert_called_once_with(conn_mock, ["obs"])
    conn_mock.commit.assert_called_once()
