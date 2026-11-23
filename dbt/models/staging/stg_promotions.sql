select promo_id, sku, market, retailer_id, start_week::date as start_week, end_week::date as end_week, depth::double as depth,
       mechanic, is_event, status,
       date_diff('day', start_week::date, end_week::date) / 7 + 1 as promo_weeks,
       case when depth < 0.15 then 'Shallow (<15%)' when depth < 0.25 then 'Medium (15-24%)' else 'Deep (25%+)' end as depth_band
from {{ source('raw', 'promotions') }}
