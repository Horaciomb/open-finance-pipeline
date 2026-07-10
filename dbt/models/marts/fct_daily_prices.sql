-- Grano: ticker × fecha. Hecho de precios diarios listo para consumo.

select
    {{ dbt_utils.generate_surrogate_key(['ticker', 'fecha']) }} as price_key,
    ticker,
    fecha,
    open,
    high,
    low,
    close,
    volume
from {{ ref('stg_prices') }}
