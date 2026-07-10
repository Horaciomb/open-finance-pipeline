-- Grano: series_id × fecha. Hecho de indicadores macro. `valor` puede ser
-- nulo (huecos reales de FRED: feriados, series aún no publicadas) — no se
-- fuerza not_null aquí, es un dato legítimo del dominio.

select
    {{ dbt_utils.generate_surrogate_key(['series_id', 'fecha']) }} as indicator_key,
    series_id,
    fecha,
    valor
from {{ ref('stg_fred_observations') }}
