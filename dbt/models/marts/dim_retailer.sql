select r.*, m.currency, r.panel_from <= (select min(week_start) from {{ ref('int_weeks') }}) as is_constant_panel
from {{ ref('stg_retailers') }} r join {{ ref('stg_markets') }} m using (market)
