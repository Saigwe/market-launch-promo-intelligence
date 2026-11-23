-- Weekly panel spread to calendar months through the date bridge, against the independent monthly provider.
with w as (
    select b.month_start, p.market, p.category, p.brand, sum(p.units * b.day_share) as units_from_weekly,
           sum(p.value_local * b.day_share) as value_local_from_weekly
    from {{ ref('fct_panel_weekly') }} p join {{ ref('int_week_month_bridge') }} b using (week_start)
    group by all
)
select m.month_start, m.market, m.category, m.brand, m.units as units_monthly, w.units_from_weekly,
       m.value_local as value_local_monthly, w.value_local_from_weekly,
       m.value_local / nullif(w.value_local_from_weekly, 0) - 1 as value_diff_pct,
       m.units / nullif(w.units_from_weekly, 0) - 1 as units_diff_pct,
       abs(m.value_local / nullif(w.value_local_from_weekly, 0) - 1) <= {{ var('reconcile_tolerance') }} as within_tolerance,
       m.value_local * fx.usd_per_unit as value_usd_monthly
from {{ ref('stg_market_monthly') }} m
left join w using (month_start, market, category, brand)
join {{ ref('stg_markets') }} mk using (market)
join {{ ref('int_fx_monthly') }} fx on fx.month_start = m.month_start and fx.currency = mk.currency
