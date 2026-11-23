-- Planned promotions: baseline from the last 8 clean weeks, lift from the history of the same depth band (p10 to p90).
with plan as (select * from {{ ref('stg_promotions') }} where status = 'planned'),
recent as (
    select p.promo_id, avg(s.units) as baseline_units
    from plan p join (
        select *, row_number() over (partition by sku, retailer_id order by week_start desc) as k
        from {{ ref('fct_sales_weekly') }} where is_clean and is_complete
    ) s on s.sku = p.sku and s.retailer_id = p.retailer_id and s.k <= 8
    group by 1
)
select p.promo_id, p.sku, pr.product_name, p.market, p.retailer_id, p.start_week, p.end_week, p.depth, p.depth_band, p.promo_weeks,
       r.baseline_units, d.avg_lift_pct, d.p10_lift_pct, d.p90_lift_pct,
       r.baseline_units * p.promo_weeks * d.avg_lift_pct as expected_incremental_units,
       -- margin per unit at standard prices (USD): full price and promoted price
       pr.list_price_usd - pr.unit_cost_usd as full_margin_unit, pr.list_price_usd * (1 - p.depth) - pr.unit_cost_usd as promo_margin_unit,
       r.baseline_units * p.promo_weeks * (1 + d.avg_lift_pct) * (pr.list_price_usd * (1 - p.depth) - pr.unit_cost_usd)
         + r.baseline_units * 2 * d.avg_dip_pct * (pr.list_price_usd - pr.unit_cost_usd)
         - r.baseline_units * p.promo_weeks * (pr.list_price_usd - pr.unit_cost_usd) as expected_incremental_margin_usd,
       r.baseline_units * p.promo_weeks * (1 + d.p10_lift_pct) * (pr.list_price_usd * (1 - p.depth) - pr.unit_cost_usd)
         + r.baseline_units * 2 * d.avg_dip_pct * (pr.list_price_usd - pr.unit_cost_usd)
         - r.baseline_units * p.promo_weeks * (pr.list_price_usd - pr.unit_cost_usd) as low_incremental_margin_usd,
       r.baseline_units * p.promo_weeks * (1 + d.p90_lift_pct) * (pr.list_price_usd * (1 - p.depth) - pr.unit_cost_usd)
         + r.baseline_units * 2 * d.avg_dip_pct * (pr.list_price_usd - pr.unit_cost_usd)
         - r.baseline_units * p.promo_weeks * (pr.list_price_usd - pr.unit_cost_usd) as high_incremental_margin_usd
from plan p
join recent r using (promo_id)
join {{ ref('rpt_promo_depth') }} d using (depth_band)
join {{ ref('dim_product') }} pr on pr.sku = p.sku
