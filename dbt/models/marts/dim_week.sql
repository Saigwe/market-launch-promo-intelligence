select w.*, year(w.week_start) as year, weekofyear(w.week_start) as iso_week
from {{ ref('int_weeks') }} w
