-- Current classification. History is restated to it (see stg_sales_weekly); the source category is kept for audit.
select sku, product_name, brand, category, launch_date::date as launch_date, list_price_usd::double as list_price_usd,
       unit_cost_usd::double as unit_cost_usd,
       sku in (select sku from {{ source('raw', 'product_class_history') }} group by sku having count(*) > 1) as was_reclassified
from {{ source('raw', 'products') }}
