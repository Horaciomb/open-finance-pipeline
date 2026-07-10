-- Snapshot diario que combina: último precio de cada activo, último valor de
-- cada indicador macro, y la brecha cambiaria de Bolivia. Formato largo/tidy
-- (una fila por metric_type × metric_key) para que el API y el dashboard lo
-- consuman genéricamente sin necesitar N columnas distintas por tipo de métrica.

with latest_prices as (

    select
        'price'         as metric_type,
        f.ticker        as metric_key,
        a.display_name  as metric_label,
        f.fecha,
        f.close         as value,
        null::numeric   as secondary_value,
        'USD'           as unit,
        row_number() over (partition by f.ticker order by f.fecha desc) as rn
    from {{ ref('fct_daily_prices') }} f
    join {{ ref('dim_asset') }} a using (ticker)

),

latest_macro as (

    select
        'macro'         as metric_type,
        m.series_id     as metric_key,
        i.display_name  as metric_label,
        m.fecha,
        m.valor         as value,
        null::numeric   as secondary_value,
        i.unit,
        row_number() over (partition by m.series_id order by m.fecha desc) as rn
    from {{ ref('fct_macro_indicators') }} m
    join {{ ref('dim_indicator') }} i using (series_id)
    where m.valor is not null

),

-- casa es una fila en el origen ('oficial'/'binance'), no una columna. Las dos
-- casas no siempre cotizan el mismo día (ej. binance reportó 2026-07-09 pero
-- oficial no), así que el "último valor" de cada una se calcula de forma
-- independiente, no sobre una fecha compartida.
fx_oficial_ranked as (

    select
        fecha,
        venta as value,
        row_number() over (order by fecha desc) as rn
    from {{ ref('stg_fx_rates') }}
    where casa = 'oficial' and venta is not null

),

fx_binance_ranked as (

    select
        fecha,
        venta as value,
        brecha_pct as secondary_value,
        row_number() over (order by fecha desc) as rn
    from {{ ref('stg_fx_rates') }}
    where casa = 'binance' and venta is not null

),

fx_oficial_latest as (
    select fecha, value from fx_oficial_ranked where rn = 1
),

fx_binance_latest as (
    select fecha, value, secondary_value from fx_binance_ranked where rn = 1
),

fx_rows as (

    select
        'fx' as metric_type, 'oficial' as metric_key, 'Dólar oficial (Bolivia)' as metric_label,
        fecha, value, null::numeric as secondary_value, 'BOB' as unit
    from fx_oficial_latest

    union all

    select
        'fx', 'binance', 'Dólar paralelo / Binance (Bolivia)',
        fecha, value, secondary_value, 'BOB'
    from fx_binance_latest

)

select metric_type, metric_key, metric_label, fecha, value, secondary_value, unit
from latest_prices where rn = 1

union all

select metric_type, metric_key, metric_label, fecha, value, secondary_value, unit
from latest_macro where rn = 1

union all

select metric_type, metric_key, metric_label, fecha, value, secondary_value, unit
from fx_rows
