-- Corvane share, reported (every retailer in the panel that week) and comparable (only retailers covered since the start).
-- Shares are non-additive: always the ratio of summed values, never an average of shares.
with b as (
    select week_start, market, category,
           sum(value_usd) as market_value_usd, sum(value_usd) filter (where brand = 'Corvane') as corvane_value_usd,
           sum(units) as market_units, sum(units) filter (where brand = 'Corvane') as corvane_units,
           sum(value_usd) filter (where is_constant_panel) as market_value_usd_cmp,
           sum(value_usd) filter (where is_constant_panel and brand = 'Corvane') as corvane_value_usd_cmp,
           sum(units) filter (where is_constant_panel) as market_units_cmp,
           sum(units) filter (where is_constant_panel and brand = 'Corvane') as corvane_units_cmp
    from {{ ref('fct_panel_weekly') }} where is_complete
    group by grouping sets ((week_start, market, category), (week_start, market), (week_start, category), (week_start))
)
select week_start, coalesce(market, 'All') as market, coalesce(category, 'All') as category,
       market_value_usd, corvane_value_usd, market_units, corvane_units,
       corvane_value_usd / market_value_usd as value_share, corvane_units::double / market_units as unit_share,
       corvane_value_usd_cmp / market_value_usd_cmp as value_share_comparable,
       corvane_units_cmp::double / market_units_cmp as unit_share_comparable
from b
