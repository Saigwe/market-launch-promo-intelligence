-- Post-launch cohort: units by week since launch, per launched SKU and market (complete weeks only).
select s.sku, p.product_name, s.market, p.launch_date,
       date_diff('day', p.launch_date, s.week_start) // 7 as weeks_since_launch,
       sum(s.units) as units, sum(s.net_sales_usd) as net_sales_usd,
       count(distinct case when s.units > 0 then s.retailer_id end) as retailers_selling
from {{ ref('fct_sales_weekly') }} s join {{ ref('dim_product') }} p using (sku)
where p.launch_date is not null and s.week_start >= p.launch_date and s.is_complete
group by all
