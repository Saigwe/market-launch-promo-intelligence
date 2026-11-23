select sku, category, valid_from::date as valid_from, valid_to::date as valid_to from {{ source('raw', 'product_class_history') }}
