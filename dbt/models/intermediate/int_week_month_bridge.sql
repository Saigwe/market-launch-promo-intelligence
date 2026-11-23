-- Date bridge: the share of each week's covered days that falls in each calendar month (weeks crossing a month split).
with d as (select week_start, days_covered, unnest(range(days_covered)) as i from {{ ref('int_weeks') }})
select week_start, date_trunc('month', week_start + cast(i as integer))::date as month_start,
       count(*)::double / any_value(days_covered) as day_share
from d group by week_start, month_start
