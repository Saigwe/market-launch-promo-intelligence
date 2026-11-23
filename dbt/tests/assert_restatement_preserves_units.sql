-- Restating history to the current category moves units between categories but never creates or loses any.
select sku, src, fct from (
    select s.sku, sum(s.units) as src, (select sum(units) from {{ ref('fct_sales_weekly') }} f where f.sku = s.sku) as fct
    from {{ source('raw', 'sales_weekly') }} s group by s.sku
) where src <> fct
