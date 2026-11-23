-- Weekly USD uses the average daily rate over the week's covered days.
select p.week_start, p.retailer_id from {{ ref('fct_panel_weekly') }} p
join (select w.week_start, f.currency, avg(f.usd_per_unit) as r from {{ ref('int_weeks') }} w
      join {{ ref('stg_fx_daily') }} f on f.rate_date >= w.week_start and f.rate_date < w.week_start + cast(w.days_covered as integer)
      group by all) x on x.week_start = p.week_start and x.currency = p.currency
where abs(p.value_usd - p.value_local * x.r) > 0.01
