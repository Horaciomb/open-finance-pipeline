# Open Finance Pipeline

![CI](https://github.com/Horaciomb/open-finance-pipeline/actions/workflows/ci.yml/badge.svg)
![dbt docs](https://github.com/Horaciomb/open-finance-pipeline/actions/workflows/dbt-docs.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![dbt](https://img.shields.io/badge/dbt--core-1.11-orange)
![React](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61dafb)

Pipeline de datos financieros con **arquitectura Medallion (Bronze → Silver →
Gold)**: combina precios de mercado (**Yahoo Finance**), indicadores macro de
EE.UU. (**FRED**) y la brecha cambiaria de Bolivia (reutilizada de un proyecto
hermano), transformados con **dbt** y expuestos vía **API REST (FastAPI)** y un
**dashboard React**.

> Tercer proyecto de portafolio de Ingeniería de Datos. Es la síntesis de los
> dos anteriores: reutiliza el patrón EL(Python)+T(dbt) de
> [Latam Economic Pulse](https://github.com/Horaciomb/latam-economic-pulse) y
> el dato de tipo de cambio de
> [Bolivia Exchange Rate Tracker](https://github.com/Horaciomb/bolivia-exchange-tracker),
> y añade una arquitectura Medallion explícita más un frontend de visualización.

🚀 **API en vivo:** _(pendiente de deploy — se agregará el link tras publicar en Render)_
📊 **Documentación dbt (lineage + catálogo):** _(pendiente — se publica en `dev/fase-7-cicd` al hacer push a GitHub Pages)_
🖥️ **Dashboard:** _(pendiente de deploy en Vercel)_

---

## Arquitectura Medallion

```mermaid
flowchart LR
    subgraph Bronze["Bronze — openfin_raw (Python)"]
        YF[Yahoo Finance\nyfinance] -->|diario| PRICES[(prices)]
        FRED[FRED API] -->|semanal| OBS[(fred_observations)]
    end

    subgraph Silver["Silver — openfin (dbt, views)"]
        STGP[stg_prices]
        STGF[stg_fred_observations]
        STGX[stg_fx_rates]
    end

    subgraph Gold["Gold — openfin (dbt, tables)"]
        DIMA[dim_asset]
        DIMI[dim_indicator]
        FCTP[fct_daily_prices]
        FCTM[fct_macro_indicators]
        MART[mart_market_overview]
    end

    FX[("fx.exchange_rates\n(proyecto hermano, solo lectura)")]

    PRICES --> STGP --> FCTP --> MART
    OBS --> STGF --> FCTM --> MART
    FX -->|source cross-schema| STGX --> MART
    STGP --> DIMA --> MART
    STGF --> DIMI --> MART

    MART --> API[FastAPI /overview]
    API --> DASH[Dashboard React]
```

**Separación clave:** Python hace **sólo EL** (extract + load crudo,
idempotente). **Toda la transformación vive en dbt** — staging limpia y
tipa, marts calculan lo que consume el API.

---

## Modelo de datos

| Capa | Esquema | Objeto | Materialización | Descripción |
|------|---------|--------|-----------------|-------------|
| Bronze | `openfin_raw` | `prices` | tabla (Python) | OHLCV crudo, grano ticker×fecha. |
| Bronze | `openfin_raw` | `fred_observations` | tabla (Python) | Observaciones FRED crudas; `valor` nulo si la fuente devolvió `"."`. |
| Silver | `openfin` | `stg_prices` | view | Tipado. |
| Silver | `openfin` | `stg_fred_observations` | view | Tipado; **conserva** nulos (huecos reales, no error). |
| Silver | `openfin` | `stg_fx_rates` | view | `source()` cross-schema a `fx.exchange_rates` (proyecto hermano). |
| Gold | `openfin` | `dim_asset` / `dim_indicator` | table | Catálogos (seeds + tickers/series observados). |
| Gold | `openfin` | `fct_daily_prices` / `fct_macro_indicators` | table | Hechos, grano ticker×fecha / series×fecha. |
| Gold | `openfin` | `mart_market_overview` | table | Snapshot diario combinado (formato tidy) que alimenta el API/dashboard. |

**Nota de diseño — brecha cambiaria:** en `fx.exchange_rates`, oficial vs.
paralelo **no son columnas**, son filas distintas (`casa = 'oficial' |
'binance'`), y no siempre reportan el mismo día. `mart_market_overview` calcula
el último valor de cada `casa` **de forma independiente** en vez de asumir una
fecha compartida — un caso real encontrado y corregido durante el desarrollo.

---

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Info + enlaces a `/docs`, dbt docs y dashboard. |
| GET | `/health` | Estado del API + conexión a la base. |
| GET | `/prices/latest` | Último precio de cada activo trackeado. |
| GET | `/prices/{ticker}?desde=&hasta=` | Serie histórica OHLCV de un ticker. |
| GET | `/macro/latest` | Último valor de cada indicador FRED. |
| GET | `/macro/{series_id}` | Serie histórica de un indicador. |
| GET | `/fx/latest` | Última brecha cambiaria de Bolivia (oficial vs. paralelo). |
| GET | `/overview` | Snapshot combinado que consume el dashboard. |

---

## Setup

### 1. Requisitos
- Python 3.11+.
- Node 18+ (para el frontend).
- Acceso a una instancia PostgreSQL (este proyecto usa una instancia Supabase
  **compartida**, en los esquemas nuevos `openfin_raw` y `openfin`).
- Una API key gratuita de FRED: registrarse en
  https://fred.stlouisfed.org/docs/api/api_key.html (instantánea, solo pide
  nombre/email/uso previsto).

### 2. Instalar (Python)
```bash
python -m venv venv
source venv/Scripts/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configurar entorno
```bash
cp .env.example .env
# Editar .env con tu DATABASE_URL (conexión directa / session, puerto 5432)
# y tu FRED_API_KEY.
```

### 4. Crear esquemas y tablas crudas (una vez)
```bash
psql "$DATABASE_URL" -f sql/bootstrap.sql
```

### 5. Correr el EL (carga cruda)
```bash
python -m src.el.pipeline prices   # diario
python -m src.el.pipeline fred     # semanal
```

### 6. Transformar con dbt
```bash
eval "$(python scripts/parse_database_url.py --export)"  # deriva PG* desde DATABASE_URL

cd dbt
dbt deps
dbt debug
dbt build          # seeds + staging + marts + tests
dbt docs generate  # catálogo + lineage
```

### 7. Levantar el API
```bash
uvicorn src.api.main:app --reload
# Swagger en http://localhost:8000/docs
```

### 8. Levantar el dashboard
```bash
cd frontend
cp .env.example .env   # VITE_API_URL=http://localhost:8000
npm install
npm run dev            # http://localhost:5173
```

---

## Tests y calidad
```bash
pytest                # extract / load / API (mocks, sin DB ni red)
ruff check .           # linting
cd dbt && dbt build    # tests de dbt (not_null, unique, relationships, accepted_values)
cd frontend && npm run build   # build de producción del dashboard
```

---

## Decisiones de diseño

### 1. Un único esquema `openfin` para todo dbt
La instancia Supabase es **compartida** (ya tiene `public`, `polla`, `fx`,
`econ_raw`/`econ`). La macro [`generate_schema_name`](dbt/macros/generate_schema_name.sql)
fuerza que **todos** los modelos (staging y marts) se materialicen en
`openfin`, en vez del comportamiento por defecto de dbt (`openfin_staging`,
`openfin_marts`).

### 2. `DATABASE_URL` → variables `PG*` para dbt
`dbt-postgres` no acepta una connection string. [`scripts/parse_database_url.py`](scripts/parse_database_url.py)
la descompone en las 5 variables `PG*` justo antes de correr dbt, en CI y en
local. Cero credenciales hardcodeadas.

### 3. El tipo de cambio de Bolivia se reutiliza, no se re-extrae
`stg_fx_rates` es un `source()` cross-schema hacia `fx.exchange_rates` (dato
ya extraído por el proyecto hermano). Este proyecto solo lee — nunca escribe
en el esquema `fx`.

### 4. El descarte/conservación de nulos es decisión explícita por fuente
FRED deja huecos reales (feriados, series aún no publicadas: `"."` en la
respuesta). Python landea todo crudo en `openfin_raw`; `stg_fred_observations`
**conserva** los nulos (no son errores de calidad); `fct_macro_indicators` no
fuerza `not_null` en `valor` por la misma razón.

### 5. Compatibilidad dbt-core + Python 3.14
`dbt-core` fija `mashumaro<3.15`, pero ese rango falla en Python 3.14
(`UnserializableField` al construir el JSON schema de `dbt_common`). Se fija
`mashumaro>=3.18` en `requirements.txt` — confirmado compatible con un `dbt
build` real contra Supabase.

### 6. CORS solo en este proyecto
A diferencia de los proyectos hermanos (sin frontend), este API habilita CORS
para `http://localhost:5173` (+ un origen extra configurable vía
`CORS_EXTRA_ORIGIN` para el futuro deploy en Vercel), sin credenciales, solo
`GET`.

---

## Stack

Python 3.11+ · yfinance · requests · **dbt-core + dbt-postgres** · PostgreSQL
(Supabase) · FastAPI · pydantic v2 · pytest · ruff · React + Vite + Recharts ·
GitHub Actions · GitHub Pages.
