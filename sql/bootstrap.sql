-- =============================================================================
-- bootstrap.sql — Open Finance Pipeline
-- =============================================================================
-- Crea los esquemas y las tablas crudas (landing zone) en la instancia Supabase
-- COMPARTIDA ya existente. NO crea un proyecto nuevo.
--
-- Ejecutar UNA sola vez, manualmente, con tu DATABASE_URL:
--     psql "$DATABASE_URL" -f sql/bootstrap.sql
--
-- Esquemas:
--   openfin_raw → datos crudos cargados por Python (este archivo). Bronze.
--   openfin     → modelos transformados por dbt (dbt los gestiona; aquí solo
--                 se crea el esquema). Silver + Gold.
--
-- El tipo de cambio de Bolivia vive en fx.exchange_rates (proyecto hermano
-- "Bolivia Exchange Rate Tracker") y NO se toca aquí — se consume vía
-- source() de dbt.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS openfin_raw;
CREATE SCHEMA IF NOT EXISTS openfin;

-- -----------------------------------------------------------------------------
-- openfin_raw.prices — precios diarios OHLCV crudos de Yahoo Finance (yfinance).
-- Grano: ticker × fecha. Se cargan tal cual vienen de la fuente.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS openfin_raw.prices (
    ticker      text        NOT NULL,
    fecha       date        NOT NULL,
    open        numeric     NOT NULL,
    high        numeric     NOT NULL,
    low         numeric     NOT NULL,
    close       numeric     NOT NULL,
    volume      bigint      NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now(),

    -- Idempotencia: un registro por ticker × fecha. Habilita UPSERT.
    CONSTRAINT uq_prices_ticker_fecha UNIQUE (ticker, fecha)
);

CREATE INDEX IF NOT EXISTS idx_prices_ticker_fecha
    ON openfin_raw.prices (ticker, fecha DESC);

-- -----------------------------------------------------------------------------
-- openfin_raw.fred_observations — observaciones crudas de series macro FRED.
-- Grano: series_id × fecha. valor es NULL cuando FRED devuelve el literal "."
-- (dato faltante); el descarte de nulos es trabajo de dbt en staging.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS openfin_raw.fred_observations (
    series_id   text        NOT NULL,
    fecha       date        NOT NULL,
    valor       numeric,                         -- NULL permitido (huecos FRED)
    ingested_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT uq_fred_series_fecha UNIQUE (series_id, fecha)
);

CREATE INDEX IF NOT EXISTS idx_fred_series_fecha
    ON openfin_raw.fred_observations (series_id, fecha DESC);
