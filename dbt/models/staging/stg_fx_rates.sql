-- Tipo de cambio de Bolivia, REUTILIZADO del proyecto hermano "Bolivia Exchange
-- Rate Tracker" (esquema fx, NO se re-extrae aquí). Pass-through de las
-- columnas relevantes; la brecha oficial/paralelo se pivotea aguas abajo en
-- mart_market_overview (casa es una fila, no una columna, en el origen).

select
    fecha,
    casa,
    compra::numeric      as compra,
    venta::numeric       as venta,
    brecha_pct::numeric  as brecha_pct,
    imputado
from {{ source('fx', 'exchange_rates') }}
