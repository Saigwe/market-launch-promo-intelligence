-- Product portfolio (PPPD overview): last N complete weeks against the same weeks a year earlier, all markets, USD.
with w as (select week_start from {{ ref('int_weeks') }} where is_complete order by week_start desc limit {{ var('share_window_weeks') }}),
s as (
    select f.sku, case when f.week_start in (select week_start from w) then 'latest' else 'year_ago' end as period,
           sum(f.units) as units, sum(f.net_sales_usd) as net_sales_usd, sum(f.gross_margin_usd) as gross_margin_usd,
           sum(f.discount_local * f.fx_week) as discount_usd
    from {{ ref('fct_sales_weekly') }} f
    where f.week_start in (select week_start from w) or f.week_start in (select week_start - interval 364 day from w)
    group by all
)
select p.sku, p.product_name, p.category, p.launch_date, p.was_reclassified,
       l.units, l.net_sales_usd, l.net_sales_usd / nullif(l.units, 0) as asp_usd, l.gross_margin_usd / nullif(l.net_sales_usd, 0) as margin_pct,
       l.discount_usd / nullif(l.net_sales_usd + l.discount_usd, 0) as discount_rate,
       y.net_sales_usd as net_sales_usd_year_ago, l.net_sales_usd / nullif(y.net_sales_usd, 0) - 1 as growth,
       l.net_sales_usd / sum(l.net_sales_usd) over () as share_of_brand
from {{ ref('dim_product') }} p
left join s l on l.sku = p.sku and l.period = 'latest'
left join s y on y.sku = p.sku and y.period = 'year_ago'
