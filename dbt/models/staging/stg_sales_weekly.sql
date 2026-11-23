-- Corvane sell-out by SKU, retailer and week, restated to the current product category.
select s.week_start::date as week_start, s.days_covered, s.market, s.retailer_id, s.sku,
       p.category, s.category_at_sale, p.category <> s.category_at_sale as is_restated,
       s.units, s.gross_sales_local::double as gross_sales_local, s.discount_local::double as discount_local,
       s.net_sales_local::double as net_sales_local
from {{ source('raw', 'sales_weekly') }} s
join {{ ref('stg_products') }} p using (sku)
