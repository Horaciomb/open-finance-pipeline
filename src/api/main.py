"""Aplicación FastAPI de Open Finance Pipeline.

Expone los datos limpios de los marts dbt (openfin). Sólo lectura. El pipeline
EL (Python) y la transformación (dbt) son procesos aparte; el API únicamente
sirve.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import services
from src.api.database import close_pool, init_pool, ping
from src.api.routers import fx, macro, prices
from src.api.schemas import HealthOut, OverviewOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa el pool al arrancar y lo cierra al apagar."""
    init_pool()
    yield
    close_pool()


app = FastAPI(
    title="Open Finance Pipeline API",
    description=(
        "Precios de mercado (Yahoo Finance), indicadores macro (FRED) y la "
        "brecha cambiaria de Bolivia, transformados con dbt (Bronze/Silver/Gold) "
        "y servidos sobre un modelo dimensional."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: el dashboard React (Vite, sin auth) consume el API desde el navegador.
_extra_origin = os.environ.get("CORS_EXTRA_ORIGIN")
_allow_origins = ["http://localhost:5173"]
if _extra_origin:
    _allow_origins.append(_extra_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
    allow_credentials=False,
)

app.include_router(prices.router)
app.include_router(macro.router)
app.include_router(fx.router)


@app.get("/", tags=["meta"])
def root() -> dict:
    """Información del API y enlaces a la documentación."""
    return {
        "name": "Open Finance Pipeline API",
        "docs": "/docs",
        "dbt_docs": os.environ.get("DBT_DOCS_URL", "(configurar DBT_DOCS_URL)"),
        "dashboard": os.environ.get("DASHBOARD_URL", "(configurar DASHBOARD_URL)"),
        "sources": ["Yahoo Finance (yfinance)", "FRED API", "fx.exchange_rates (proyecto hermano)"],
    }


@app.get("/health", response_model=HealthOut, tags=["meta"])
def health() -> HealthOut:
    """Estado del API y de la conexión a la base."""
    try:
        connected = ping()
    except Exception:
        connected = False
    return HealthOut(
        status="ok",
        database="connected" if connected else "disconnected",
    )


@app.get("/overview", response_model=OverviewOut, tags=["meta"])
def overview() -> dict:
    """Snapshot combinado que consume el dashboard: precios, macro y brecha FX."""
    return services.get_overview()
