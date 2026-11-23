-- One row per market: where Corvane stands and what moved it.
with sc as (select * from {{ ref('rpt_share_change') }} where category = 'All'),
sales as (
    select market,
           sum(net_sales_usd) filter (where week_start > (select max(week_start) from {{ ref('int_weeks') }} where is_complete) - interval {{ 7 * var('share_window_weeks') }} day) as net_latest,
           sum(net_sales_usd) filter (where week_start > (select max(week_start) from {{ ref('int_weeks') }} where is_complete) - interval {{ 7 * var('share_window_weeks') + 364 }} day
                                      and week_start <= (select max(week_start) from {{ ref('int_weeks') }} where is_complete) - interval 364 day) as net_year_ago
    from {{ ref('fct_sales_weekly') }} where is_complete group by 1
)
select sc.*, s.net_latest as corvane_net_sales_usd, s.net_latest / s.net_year_ago - 1 as corvane_sales_growth
from sc left join sales s using (market)
