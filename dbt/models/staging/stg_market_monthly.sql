select month::date as month_start, market, category, brand, units::double as units, value_local::double as value_local,
       published_at::timestamp as published_at
from {{ source('raw', 'market_monthly') }}
