select week_start, sum(day_share) as total from {{ ref('int_week_month_bridge') }} group by 1 having abs(sum(day_share) - 1) > 1e-9
