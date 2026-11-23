-- Value share in the last N complete weeks against the same weeks a year earlier, reported and comparable panel.
-- "Survives" = the share of the reported change that remains on a comparable panel.
with w as (select week_start from {{ ref('int_weeks') }} where is_complete order by week_start desc limit {{ var('share_window_weeks') }}),
periods as (
    select week_start, 'latest' as period from w
    union all select week_start - interval 364 day, 'year_ago' from w
),
s as (
    select p.period, r.market, r.category,
           sum(r.corvane_value_usd) / sum(r.market_value_usd) as share,
           sum(r.market_value_usd) as market_value_usd
    from {{ ref('rpt_share_weekly') }} r join periods p using (week_start)
    group by all
),
c as (  -- comparable sums straight from the fact
    select p.period, coalesce(f.market, 'All') as market, coalesce(f.category, 'All') as category,
           sum(f.value_usd) filter (where f.brand = 'Corvane') / sum(f.value_usd) as share_cmp
    from {{ ref('fct_panel_weekly') }} f join periods p using (week_start)
    where f.is_constant_panel
    group by grouping sets ((p.period, f.market, f.category), (p.period, f.market), (p.period, f.category), (p.period))
)
select l.market, l.category,
       y.share as share_year_ago, l.share as share_latest, l.share - y.share as change_reported,
       cy.share_cmp as share_year_ago_comparable, cl.share_cmp as share_latest_comparable, cl.share_cmp - cy.share_cmp as change_comparable,
       (l.share - y.share) - (cl.share_cmp - cy.share_cmp) as change_from_panel_coverage,
       case when abs(l.share - y.share) > 0.002 then (cl.share_cmp - cy.share_cmp) / (l.share - y.share) end as share_of_change_surviving,
       l.market_value_usd / y.market_value_usd - 1 as market_value_growth
from s l
join s y on y.market = l.market and y.category = l.category and y.period = 'year_ago'
join c cl on cl.market = l.market and cl.category = l.category and cl.period = 'latest'
join c cy on cy.market = l.market and cy.category = l.category and cy.period = 'year_ago'
where l.period = 'latest'
