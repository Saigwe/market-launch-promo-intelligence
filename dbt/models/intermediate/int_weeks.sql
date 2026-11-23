-- Every week in the feeds and how many of its days are in the extract. A week with fewer than 7 is incomplete.
select week_start, max(days_covered) as days_covered, max(days_covered) = 7 as is_complete,
       date_trunc('month', week_start)::date as month_of_week_start
from {{ ref('stg_panel_weekly') }} group by week_start
