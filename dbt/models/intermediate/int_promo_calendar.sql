-- One row per promotion, SKU, retailer and week it touches: the promotion weeks and the two weeks after (post-promotion dip).
-- A store-wide event (no SKU) expands to every SKU.
with p as (select * from {{ ref('stg_promotions') }} where status = 'completed')
select p.promo_id, s.sku, p.retailer_id, p.market, p.depth, p.is_event, p.start_week, p.end_week,
       w::date as week_start, case when w::date <= p.end_week then 'promo' else 'dip' end as kind
from p
join {{ ref('stg_products') }} s on p.sku is null or s.sku = p.sku
cross join unnest(generate_series(p.start_week, p.end_week + interval 14 day, interval 7 day)) as t(w)
