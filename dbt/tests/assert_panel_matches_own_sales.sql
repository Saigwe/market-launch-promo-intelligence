-- Corvane in the panel matches Corvane's own sales at the same retailers within 2% per market and month (independent sources).
-- Revised panel rows are compared separately (rpt_panel_vs_sales): a revision is the provider restating, not an error here.
with p as (select market, date_trunc('month', week_start) as m, sum(units) as u from {{ ref('fct_panel_weekly') }} where brand = 'Corvane' and not was_revised group by all),
s as (select f.market, date_trunc('month', f.week_start) as m, sum(f.units) as u
      from {{ ref('fct_sales_weekly') }} f
      join {{ ref('stg_panel_weekly') }} k on k.week_start = f.week_start and k.retailer_id = f.retailer_id and k.brand = 'Corvane' and k.category = f.category_at_sale and not k.was_revised
      group by all)
select * from p join s using (market, m) where abs(p.u::double / s.u - 1) > 0.02
