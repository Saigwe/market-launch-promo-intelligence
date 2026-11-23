-- Corvane units in the panel against Corvane's own sales at the same retailer-weeks, by market and month.
with p as (select market, date_trunc('month', week_start)::date as month_start, sum(units) as panel_units, bool_or(was_revised) as has_revision
           from {{ ref('fct_panel_weekly') }} where brand = 'Corvane' group by all),
s as (select f.market, date_trunc('month', f.week_start)::date as month_start, sum(f.units) as own_units
      from {{ ref('fct_sales_weekly') }} f
      join {{ ref('stg_panel_weekly') }} k on k.week_start = f.week_start and k.retailer_id = f.retailer_id and k.brand = 'Corvane' and k.category = f.category_at_sale
      group by all)
select *, panel_units::double / own_units - 1 as diff_pct, abs(panel_units::double / own_units - 1) > 0.02 as outside_2pct
from p join s using (market, month_start)
