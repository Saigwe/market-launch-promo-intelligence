-- Grain: week x retailer x category x brand, panel retailers only. Value in USD at the weekly FX policy.
select p.*, m.currency, fx.usd_per_unit as fx_week, p.value_local * fx.usd_per_unit as value_usd,
       r.is_constant_panel, w.is_complete
from {{ ref('stg_panel_weekly') }} p
join {{ ref('stg_markets') }} m using (market)
join {{ ref('dim_retailer') }} r using (retailer_id, market)
join {{ ref('int_fx_weekly') }} fx on fx.week_start = p.week_start and fx.currency = m.currency
join {{ ref('int_weeks') }} w on w.week_start = p.week_start
