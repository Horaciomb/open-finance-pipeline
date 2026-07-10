-- Catálogo de activos trackeados. Un ticker nuevo en stg_prices que no esté en
-- el seed no rompe el pipeline: cae con asset_type/display_name genéricos.

with tickers as (
    select distinct ticker from {{ ref('stg_prices') }}
)

select
    t.ticker,
    coalesce(c.asset_type, 'unknown')  as asset_type,
    coalesce(c.display_name, t.ticker) as display_name
from tickers t
left join {{ ref('asset_catalog') }} c using (ticker)
