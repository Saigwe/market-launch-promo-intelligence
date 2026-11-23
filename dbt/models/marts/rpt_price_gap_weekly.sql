-- Shelf-price gap for comparable pairs: Corvane price / competitor price - 1, averaged over the retailers observed.
select r.week_start, r.market, r.pair_id, c.category, c.corvane_sku, c.competitor_product,
       avg(r.corvane_price_local) as corvane_price_local, avg(r.competitor_price_local) as competitor_price_local,
       avg(r.corvane_price_local) / avg(r.competitor_price_local) - 1 as price_gap, count(*) as retailers_observed
from {{ ref('stg_retail_prices') }} r join {{ ref('stg_comparable_pairs') }} c using (pair_id)
group by all
