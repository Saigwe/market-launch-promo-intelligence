-- The latest delivery wins: a revised file replaces the earlier figures for the same key.
with ranked as (
    select *, row_number() over (partition by week_start, market, retailer_id, category, brand order by delivered_at desc) as rn,
           count(*) over (partition by week_start, market, retailer_id, category, brand) as deliveries
    from {{ source('raw', 'panel_weekly') }}
)
select week_start::date as week_start, market, retailer_id, category, brand, units, value_local::double as value_local,
       days_covered, delivery_id, delivered_at::timestamp as delivered_at, deliveries > 1 as was_revised
from ranked where rn = 1
