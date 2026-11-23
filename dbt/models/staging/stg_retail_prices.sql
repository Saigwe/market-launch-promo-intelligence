select week_start::date as week_start, market, retailer_id, pair_id, corvane_price_local::double as corvane_price_local,
       competitor_price_local::double as competitor_price_local
from {{ source('raw', 'retail_prices') }}
