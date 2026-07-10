"""Tests del API. Sin DB real: el pool se mockea y los services se parchean.

Cada endpoint debe responder 200 (o el error esperado) con el shape correcto.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.api import main


@pytest.fixture
def client():
    """TestClient con el ciclo de vida (lifespan) del pool mockeado."""
    with (
        patch("src.api.main.init_pool"),
        patch("src.api.main.close_pool"),
    ):
        with TestClient(main.app) as c:
            yield c


# --- meta -------------------------------------------------------------------

def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Open Finance Pipeline API"


def test_health_connected(client):
    with patch("src.api.main.ping", return_value=True):
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "database": "connected"}


def test_health_disconnected(client):
    with patch("src.api.main.ping", side_effect=Exception("down")):
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["database"] == "disconnected"


def test_cors_header_present_for_allowed_origin(client):
    resp = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert resp.headers["access-control-allow-origin"] == "http://localhost:5173"


# --- prices -------------------------------------------------------------------

def test_get_latest_prices(client):
    rows = [
        {
            "ticker": "^GSPC",
            "display_name": "S&P 500",
            "fecha": "2026-07-09",
            "close": 7543.64,
            "unit": "USD",
        }
    ]
    with patch("src.api.routers.prices.services.get_latest_prices", return_value=rows):
        resp = client.get("/prices/latest")
    assert resp.status_code == 200
    assert resp.json()[0]["ticker"] == "^GSPC"


def test_get_price_series_ok(client):
    rows = [
        {
            "ticker": "^GSPC",
            "fecha": "2026-07-09",
            "open": 1,
            "high": 2,
            "low": 0.5,
            "close": 1.5,
            "volume": 100,
        }
    ]
    with patch("src.api.routers.prices.services.get_price_series", return_value=rows):
        resp = client.get("/prices/%5EGSPC")
    assert resp.status_code == 200
    assert resp.json()[0]["close"] == 1.5


def test_get_price_series_not_found(client):
    with patch("src.api.routers.prices.services.get_price_series", return_value=[]):
        resp = client.get("/prices/UNKNOWN")
    assert resp.status_code == 404


# --- macro ----------------------------------------------------------------------

def test_get_latest_macro(client):
    rows = [
        {
            "series_id": "FEDFUNDS",
            "display_name": "Tasa de fondos federales",
            "fecha": "2026-06-01",
            "valor": 3.63,
            "unit": "%",
        }
    ]
    with patch("src.api.routers.macro.services.get_latest_macro", return_value=rows):
        resp = client.get("/macro/latest")
    assert resp.status_code == 200
    assert resp.json()[0]["series_id"] == "FEDFUNDS"


def test_get_macro_series_ok(client):
    rows = [{"series_id": "DGS10", "fecha": "2026-01-01", "valor": None}]
    with patch("src.api.routers.macro.services.get_macro_series", return_value=rows):
        resp = client.get("/macro/DGS10")
    assert resp.status_code == 200
    assert resp.json()[0]["valor"] is None


def test_get_macro_series_not_found(client):
    with patch("src.api.routers.macro.services.get_macro_series", return_value=[]):
        resp = client.get("/macro/UNKNOWN")
    assert resp.status_code == 404


# --- fx / overview ----------------------------------------------------------------

def test_get_latest_fx(client):
    fx = {
        "oficial": {"fecha": "2026-07-08", "value": 10.10},
        "binance": {"fecha": "2026-07-09", "value": 10.50},
        "brecha_pct": 3.96,
    }
    with patch("src.api.routers.fx.services.get_latest_fx", return_value=fx):
        resp = client.get("/fx/latest")
    assert resp.status_code == 200
    assert resp.json()["brecha_pct"] == 3.96


def test_get_overview(client):
    overview = {
        "prices": [
            {
                "ticker": "^GSPC",
                "display_name": "S&P 500",
                "fecha": "2026-07-09",
                "close": 7543.64,
                "unit": "USD",
            }
        ],
        "macro": [
            {
                "series_id": "FEDFUNDS",
                "display_name": "Tasa de fondos federales",
                "fecha": "2026-06-01",
                "valor": 3.63,
                "unit": "%",
            }
        ],
        "fx": {
            "oficial": {"fecha": "2026-07-08", "value": 10.10},
            "binance": {"fecha": "2026-07-09", "value": 10.50},
            "brecha_pct": 3.96,
        },
    }
    with patch("src.api.main.services.get_overview", return_value=overview):
        resp = client.get("/overview")
    assert resp.status_code == 200
    body = resp.json()
    assert body["prices"][0]["ticker"] == "^GSPC"
    assert body["fx"]["brecha_pct"] == 3.96
