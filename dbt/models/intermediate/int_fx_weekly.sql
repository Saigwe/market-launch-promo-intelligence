-- FX policy for weekly figures: the average of the daily rates over the week's covered days.
select w.week_start, f.currency, avg(f.usd_per_unit) as usd_per_unit
from {{ ref('int_weeks') }} w
join {{ ref('stg_fx_daily') }} f on f.rate_date between w.week_start and w.week_start + cast(w.days_covered - 1 as integer)
group by all
