select market, market_name, currency, std_usd_per_unit from {{ source('raw', 'markets') }}
