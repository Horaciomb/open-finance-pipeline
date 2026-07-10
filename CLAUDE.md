# CLAUDE.md — Open Finance Pipeline (Medallion Architecture)

## Propósito del proyecto

El proyecto insignia (flagship) del portafolio. Combina múltiples fuentes de
datos financieros públicos (precios de mercado, indicadores macro de EE.UU., y
el tipo de cambio de Bolivia ya construido en un proyecto anterior) en un
pipeline con **arquitectura Medallion (Bronze → Silver → Gold)**, transformado
con **dbt**, expuesto vía **API REST**, y visualizado en un **dashboard React**.

Es la síntesis de los dos proyectos previos: reutiliza el patrón EL(Python)+T(dbt)
del Proyecto 2, reutiliza el dato de tipo de cambio del Proyecto 1 (esquema `fx`),
y añade dos cosas nuevas: (1) arquitectura Medallion explícita con 3 capas
nombradas, y (2) un frontend de visualización, no solo una API.

## Contexto del autor (para no re-explicar)

Ya completados:

- **Proyecto 1** (Bolivia Exchange Rate Tracker): esquema `fx.exchange_rates` en
  la misma instancia Supabase, API FastAPI en Render, cron diario.
- **Proyecto 2** (Latam Economic Pulse): patrón EL(Python)+T(dbt), esquemas
  `econ_raw`/`econ`, dbt docs públicas en GitHub Pages, API en Render.

Este proyecto 3 NO repite explicaciones de esos patrones — los reutiliza. La
única fuente de datos que se re-extrae aquí es Yahoo Finance y FRED; el tipo de
cambio boliviano se REUTILIZA leyendo directamente de `fx.exchange_rates` (ya
existe, no se vuelve a extraer).

## Stack tecnológico (NO cambiar sin justificación)

- **Lenguaje:** Python 3.11+
- **Extracción:** `yfinance` (precios de mercado, sin API key) + `requests`
  contra la API de FRED (requiere API key gratuita, ver más abajo)
- **Transformación:** dbt-core + dbt-postgres (arquitectura Medallion en capas)
- **Base de datos:** PostgreSQL en Supabase, **esquemas nuevos `openfin_raw`
  (Bronze) y `openfin` (Silver + Gold vía dbt)**, MISMA instancia compartida que
  ya tiene `public`, `polla`, `fx`, `econ_raw`, `econ`.
  Conexión directa vía `DATABASE_URL` con psycopg2/SQLAlchemy. NO usar supabase-py.
- **API:** FastAPI + uvicorn
- **Frontend:** React + Vite + Recharts, deploy en Vercel (mismo proveedor que
  Album Tracker)
- **Validación:** pydantic v2
- **Tests Python:** pytest
- **Orquestación:** GitHub Actions (cron diario para precios, semanal para FRED)
- **Docs dbt:** dbt docs generate → GitHub Pages
- **Deploy API:** Render.com (free tier)
- **Linting:** ruff

## Fuentes de datos

### 1. Yahoo Finance (yfinance) — precios de mercado

Sin API key. Librería `yfinance` en Python.

```python
import yfinance as yf
data = yf.download(["^GSPC", "BTC-USD", "CL=F"], period="5y", interval="1d")
```

Tickers sugeridos (ampliable): `^GSPC` (S&P 500), `BTC-USD` (Bitcoin),
`CL=F` (petróleo WTI), `GC=F` (oro). Confirmar con una prueba real qué columnas
devuelve (Open, High, Low, Close, Volume, Adj Close) antes de modelar el schema,
porque el formato de `yfinance` cambia de versión a versión.

### 2. FRED (Federal Reserve Economic Data) — indicadores macro EE.UU.

**Requiere API key gratuita** — registrarse en https://fred.stlouisfed.org/docs/api/api_key.html
(el usuario la generará, ver pasos manuales).

- Base URL: `https://api.stlouisfed.org/fred/series/observations`
- Parámetros: `series_id`, `api_key`, `file_type=json`, `observation_start`,
  `observation_end`
- Ejemplo: `?series_id=FEDFUNDS&api_key=XXX&file_type=json&observation_start=2015-01-01`
- Respuesta JSON: objeto con metadata + array `observations`, cada uno con
  `date` y `value` (value viene como STRING, y puede ser el literal `"."` cuando
  no hay dato — hay que manejar ese caso al castear a numeric).

Series sugeridas (ampliable): `FEDFUNDS` (tasa de fondos federales), `UNRATE`
(desempleo EE.UU.), `CPIAUCSL` (IPC), `DGS10` (bono del tesoro a 10 años).

NOTA: hacer una llamada real de prueba a ambas fuentes ANTES de modelar el
schema. No asumir el shape de los datos.

### 3. Tipo de cambio Bolivia — REUTILIZADO, no se re-extrae

Leer directamente de `fx.exchange_rates` (proyecto 1, misma instancia). El
pipeline de este proyecto NO extrae este dato — solo lo consume vía una source
de dbt que apunta al esquema `fx`.

## Arquitectura Medallion — mapeo exacto de capas

| Capa   | Qué contiene                                                   | Dónde vive                                   | Quién la escribe |
| ------ | -------------------------------------------------------------- | -------------------------------------------- | ---------------- |
| Bronze | Datos crudos, sin transformar, tal cual la fuente              | `openfin_raw.*` (tablas landing)             | Python (EL)      |
| Silver | Datos limpios, tipados, validados, un registro por observación | `openfin.stg_*` (views, vía dbt)             | dbt              |
| Gold   | Métricas agregadas, listas para consumo (BI/API)               | `openfin.fct_*` / `mart_*` (tables, vía dbt) | dbt              |

Esto es EXACTAMENTE el patrón staging→marts del Proyecto 2, pero aquí se nombra
explícitamente como Bronze/Silver/Gold en la documentación y el README, porque
es el término que reconoce la industria y que se evalúa en el puesto objetivo.

## Arquitectura del repositorio

```
open-finance-pipeline/
├── .github/workflows/
│   ├── ci.yml                  # ruff + pytest + dbt build
│   ├── pipeline-daily.yml      # cron diario: precios (yfinance)
│   ├── pipeline-weekly.yml     # cron semanal: FRED + dbt run/test
│   └── dbt-docs.yml            # dbt docs → GitHub Pages
├── src/
│   ├── el/
│   │   ├── __init__.py
│   │   ├── extract_prices.py   # yfinance
│   │   ├── extract_fred.py     # FRED API, maneja "." como NULL
│   │   ├── load.py             # upsert a openfin_raw.* (idempotente)
│   │   └── pipeline.py         # orquesta extract→load, entry points separados
│   │                            # para precios (diario) y FRED (semanal)
│   ├── models/
│   │   └── schemas.py          # pydantic para validar extracción
│   └── api/
│       ├── __init__.py
│       ├── main.py
│       ├── database.py         # pool psycopg2, search_path openfin
│       ├── schemas.py
│       ├── services.py         # SQL contra marts (Gold)
│       └── routers/
│           ├── prices.py
│           ├── macro.py
│           └── fx.py            # lee de fx.exchange_rates (cross-schema)
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml             # env_var(DATABASE_URL), derivar PG* (igual que proyecto 2)
│   ├── models/
│   │   ├── staging/             # SILVER
│   │   │   ├── _staging.yml
│   │   │   ├── stg_prices.sql
│   │   │   ├── stg_fred_observations.sql
│   │   │   └── stg_fx_rates.sql       # source() apuntando a fx.exchange_rates
│   │   └── marts/               # GOLD
│   │       ├── _marts.yml
│   │       ├── dim_asset.sql
│   │       ├── dim_indicator.sql
│   │       ├── fct_daily_prices.sql
│   │       ├── fct_macro_indicators.sql
│   │       └── mart_market_overview.sql   # métricas combinadas para el dashboard
│   └── tests/
├── frontend/                     # dashboard React
│   ├── package.json
│   ├── vite.config.js
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── api/client.js         # fetch a la API de Render
│   │   └── components/
│   │       ├── PriceChart.jsx     # Recharts line chart
│   │       ├── MacroCard.jsx
│   │       └── FxGapBanner.jsx    # muestra la brecha cambiaria del proyecto 1
│   └── .env.example               # VITE_API_URL
├── tests/
│   ├── test_extract_prices.py
│   ├── test_extract_fred.py
│   ├── test_load.py
│   └── test_api.py
├── sql/
│   └── bootstrap.sql             # crea openfin_raw y openfin
├── .env.example
├── requirements.txt
├── pyproject.toml
├── README.md
└── CLAUDE.md
```

## Modelo de datos — Bronze (Python)

### openfin_raw.prices

| Columna     | Tipo        | Notas                  |
| ----------- | ----------- | ---------------------- |
| ticker      | text        | ej. '^GSPC', 'BTC-USD' |
| fecha       | date        |                        |
| open        | numeric     |                        |
| high        | numeric     |                        |
| low         | numeric     |                        |
| close       | numeric     |                        |
| volume      | bigint      |                        |
| ingested_at | timestamptz | default now()          |

UNIQUE(ticker, fecha). UPSERT.

### openfin_raw.fred_observations

| Columna     | Tipo        | Notas                          |
| ----------- | ----------- | ------------------------------ |
| series_id   | text        | ej. 'FEDFUNDS'                 |
| fecha       | date        |                                |
| valor       | numeric     | NULL si la fuente devolvió "." |
| ingested_at | timestamptz | default now()                  |

UNIQUE(series_id, fecha). UPSERT.

## Capas dbt

**Staging (Silver)** — `stg_prices`, `stg_fred_observations`: limpian tipos,
descartan o marcan nulls, normalizan nombres. Materialización: view.
`stg_fx_rates`: source() apuntando a `fx.exchange_rates` (cross-schema source,
documentar en el .yml que este dato pertenece a otro proyecto/esquema).

**Marts (Gold)**:

- `dim_asset`: catálogo de tickers con su tipo (equity_index, crypto, commodity)
- `dim_indicator`: catálogo de series FRED
- `fct_daily_prices`: grano ticker×fecha
- `fct_macro_indicators`: grano series×fecha
- `mart_market_overview`: tabla resumen diaria que combina el último precio de
  cada activo + últimos indicadores macro relevantes + la brecha cambiaria de
  Bolivia (leída de `stg_fx_rates`) — ESTA es la tabla que alimenta el dashboard
  principal.

Todo mart con tests (unique, not_null, relationships) y descripciones completas
para que dbt docs salga profesional, igual que en el Proyecto 2.

## Endpoints del API

- `GET /` → info + links a /docs, dbt docs, dashboard
- `GET /health`
- `GET /prices/{ticker}?desde=...&hasta=...` → serie histórica
- `GET /prices/latest` → último precio de cada activo trackeado
- `GET /macro/{series_id}` → serie histórica de un indicador FRED
- `GET /macro/latest` → último valor de cada indicador
- `GET /fx/latest` → último dato de brecha cambiaria (lee de mart que incluye fx)
- `GET /overview` → snapshot combinado (lo que consume el dashboard React)

## Frontend — dashboard mínimo

Una sola página con: gráfico de líneas de 1-2 activos (Recharts), tarjetas de
indicadores macro clave, y un banner con la brecha cambiaria boliviana. Consume
la API vía `fetch` a `/overview`. Sin autenticación, sin rutas múltiples —
mantenerlo simple, es una vitrina, no una app compleja.

## Convenciones (idénticas a proyectos 1 y 2)

- Type hints, docstrings Google, sin lógica de negocio en routers/componentes.
- Reintentos con backoff en toda extracción externa (yfinance y FRED).
- Credenciales SOLO desde entorno (incluida la FRED_API_KEY).
- `ref()`/`source()` siempre en dbt, nunca nombres hardcodeados.
- Conventional commits.
- staging = views, marts = tables.

## Lo que NO debe hacer Claude Code

- NO crear un proyecto Supabase nuevo — reutiliza la instancia, esquemas
  `openfin_raw` y `openfin`.
- NO re-extraer el tipo de cambio boliviano — se LEE de `fx.exchange_rates`
  vía dbt source(), no se duplica la extracción.
- NO hardcodear la FRED_API_KEY en ningún archivo.
- NO sobre-diseñar el frontend — una página, sin routing, sin autenticación.
- NO commitear `.env`, `node_modules/`, `target/`, `dbt_packages/`.

## Orden de implementación sugerido

1. Setup Python: requirements.txt, pyproject.toml, .gitignore, .env.example.
2. Prueba real de yfinance (unos tickers, unos días) — confirmar columnas.
3. Prueba real de FRED con una API key de prueba del usuario — confirmar shape,
   incluido el caso del valor "." como missing.
4. sql/bootstrap.sql: esquemas openfin_raw y openfin.
5. models/schemas.py (pydantic).
6. el/extract_prices.py + test. el/extract_fred.py + test (mockeados).
7. el/load.py (upsert) + test.
8. el/pipeline.py con dos entry points (precios diario, FRED semanal). Correr
   localmente y verificar carga en openfin_raw.
9. Proyecto dbt: dbt_project.yml + profiles.yml (mismo patrón derivar PG\* del
   DATABASE_URL que en proyecto 2). `dbt debug`.
10. Staging: stg_prices, stg_fred_observations, stg_fx_rates (source cross-schema
    a fx.exchange_rates). Tests. `dbt run --select staging`.
11. Marts: dims, facts, y mart_market_overview. Tests. `dbt build`.
12. dbt docs generate — verificar lineage, incluyendo que se vea la referencia
    cross-schema a fx.
13. api/ completa.
14. tests/test_api.py.
15. frontend/: scaffold Vite+React, componente de gráfico, conectar a la API
    (usar VITE_API_URL en .env, apuntando a localhost mientras se desarrolla).
16. Workflows: ci.yml, pipeline-daily.yml, pipeline-weekly.yml, dbt-docs.yml.
17. README con badges, diagrama Bronze→Silver→Gold, links a API/dbt docs/dashboard,
    instrucciones de setup incluyendo cómo obtener la FRED_API_KEY.
