select pair_id, corvane_sku, competitor_brand, competitor_product, category from {{ source('raw', 'comparable_pairs') }}
