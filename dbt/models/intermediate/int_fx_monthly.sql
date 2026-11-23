-- FX policy for monthly figures: the average of the daily rates over the calendar month.
select date_trunc('month', rate_date)::date as month_start, currency, avg(usd_per_unit) as usd_per_unit
from {{ ref('stg_fx_daily') }} group by all
