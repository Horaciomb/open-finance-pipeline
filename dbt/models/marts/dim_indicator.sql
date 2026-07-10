-- Catálogo de series FRED trackeadas. Igual que dim_asset: una serie nueva sin
-- catalogar cae con display_name/unit genéricos en vez de romper el pipeline.

with series as (
    select distinct series_id from {{ ref('stg_fred_observations') }}
)

select
    s.series_id,
    coalesce(c.display_name, s.series_id) as display_name,
    coalesce(c.unit, 'unknown')           as unit
from series s
left join {{ ref('indicator_catalog') }} c using (series_id)
