-- Precios OHLCV limpios. Grano: ticker × fecha. Pass-through tipado desde Bronze.

select
    ticker,
    fecha,
    open::numeric  as open,
    high::numeric  as high,
    low::numeric   as low,
    close::numeric as close,
    volume::bigint as volume
from {{ source('openfin_raw', 'prices') }}
