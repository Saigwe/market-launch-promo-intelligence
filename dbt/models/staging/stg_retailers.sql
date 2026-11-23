select r.retailer_id, r.market, r.retailer_name, c.panel_from::date as panel_from, c.panel_to::date as panel_to
from {{ source('raw', 'retailers') }} r left join {{ source('raw', 'panel_coverage') }} c using (retailer_id, market)
