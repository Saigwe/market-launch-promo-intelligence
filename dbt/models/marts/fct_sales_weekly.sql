-- Grain: SKU x retailer x week. USD at the weekly FX policy. Clean = no promotion, event or post-promotion dip on it.
select s.*, m.currency, fx.usd_per_unit as fx_week, w.is_complete,
       s.gross_sales_local * fx.usd_per_unit as gross_sales_usd,
       s.net_sales_local * fx.usd_per_unit as net_sales_usd,
       s.units * p.unit_cost_usd as cogs_usd,
       s.net_sales_local * fx.usd_per_unit - s.units * p.unit_cost_usd as gross_margin_usd,
       not exists (select 1 from {{ ref('int_promo_calendar') }} c
                   where c.sku = s.sku and c.retailer_id = s.retailer_id and c.week_start = s.week_start) as is_clean
from {{ ref('stg_sales_weekly') }} s
join {{ ref('stg_markets') }} m using (market)
join {{ ref('dim_product') }} p using (sku)
join {{ ref('int_fx_weekly') }} fx on fx.week_start = s.week_start and fx.currency = m.currency
join {{ ref('int_weeks') }} w on w.week_start = s.week_start
