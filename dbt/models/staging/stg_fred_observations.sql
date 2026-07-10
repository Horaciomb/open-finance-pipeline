-- Observaciones FRED limpias. Grano: series_id × fecha. Conserva los NULLs de
-- `valor`: son huecos reales (feriados, series no publicadas aún), no errores
-- de calidad de dato — descartarlos es decisión de cada consumidor (marts),
-- no de esta capa.

select
    series_id,
    fecha,
    valor::numeric as valor
from {{ source('openfin_raw', 'fred_observations') }}
