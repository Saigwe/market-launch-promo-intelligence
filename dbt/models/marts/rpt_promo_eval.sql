-- Estimated lift for every completed SKU promotion, against four baselines, with a 95% interval.
--   pre4 / pre8 / pre13 : mean of the 4, 8 or 13 nearest clean complete weeks before the promotion
--   ly                  : the same weeks a year earlier, scaled by the ratio of pre-period sales this year to last
-- Interval: lift +/- 1.96 x sd_pre x sqrt(n x (1 + n / n_pre)), the error of forecasting n weeks from n_pre.
-- Overlap with a store-wide event: the naive estimate credits the SKU promotion with the joint lift; the attributed
-- estimate splits it in proportion to discount depth (a stated approximation).
with promo as (select * from {{ ref('stg_promotions') }} where status = 'completed' and not is_event),
event as (select * from {{ ref('stg_promotions') }} where status = 'completed' and is_event),
pw as (select * from {{ ref('int_promo_calendar') }} c where c.promo_id in (select promo_id from promo)),
pre as (
    select p.promo_id, s.week_start, s.units,
           row_number() over (partition by p.promo_id order by s.week_start desc) as k
    from promo p join {{ ref('fct_sales_weekly') }} s
      on s.sku = p.sku and s.retailer_id = p.retailer_id and s.week_start < p.start_week and s.is_clean and s.is_complete
),
methods as (select * from (values ('pre4', 4), ('pre8', 8), ('pre13', 13)) t(method, n)),
base_pre as (
    select p.promo_id, m.method, avg(pre.units) as baseline_units, stddev_samp(pre.units) as sd_units, count(*) as n_pre
    from promo p cross join methods m join pre on pre.promo_id = p.promo_id and pre.k <= m.n
    group by all
),
ly as (
    select p.promo_id, avg(s.units) as ly_units, count(*) as n_ly
    from promo p join pw on pw.promo_id = p.promo_id and pw.kind = 'promo'
    join {{ ref('fct_sales_weekly') }} s on s.sku = p.sku and s.retailer_id = p.retailer_id and s.week_start = pw.week_start - interval 364 day
    group by 1
),
ly_pre as (
    select p.promo_id, avg(s.units) as ly_pre_units
    from promo p join {{ ref('fct_sales_weekly') }} s
      on s.sku = p.sku and s.retailer_id = p.retailer_id and s.is_clean
     and s.week_start between p.start_week - interval 420 day and p.start_week - interval 365 day
    group by 1
),
base as (
    select * from base_pre
    union all
    select b.promo_id, 'ly', ly.ly_units * b.baseline_units / ly_pre.ly_pre_units, b.sd_units, b.n_pre
    from base_pre b join ly using (promo_id) join ly_pre using (promo_id)
    where b.method = 'pre8' and ly.n_ly = (select promo_weeks from promo where promo_id = b.promo_id)
),
act as (
    select pw.promo_id, pw.kind, count(*) as n_weeks, bool_and(s.is_complete) as all_complete, sum(s.units) as units,
           sum(s.net_sales_usd) as net_sales_usd, sum(s.gross_margin_usd) as margin_usd,
           (sum(s.gross_sales_usd) - sum(s.cogs_usd)) / nullif(sum(s.units), 0) as full_price_margin_per_unit
    from pw join {{ ref('fct_sales_weekly') }} s using (sku, retailer_id, week_start)
    group by 1, 2
),
ov as (
    select p.promo_id, max(e.depth) as event_depth
    from promo p join event e on e.retailer_id = p.retailer_id and e.start_week <= p.end_week and e.end_week >= p.start_week
    group by 1
)
select p.promo_id, p.sku, p.market, p.retailer_id, p.start_week, p.end_week, p.depth, p.depth_band, p.promo_weeks,
       b.method, b.baseline_units, b.sd_units, b.n_pre,
       a.units as promo_units, a.units - b.baseline_units * a.n_weeks as lift_units,
       (a.units - b.baseline_units * a.n_weeks) / nullif(b.baseline_units * a.n_weeks, 0) as lift_pct,
       1.96 * b.sd_units * sqrt(a.n_weeks * (1 + a.n_weeks / b.n_pre)) as ci_half_width_units,
       coalesce(d.units - b.baseline_units * d.n_weeks, 0) as post_dip_units,
       a.margin_usd + coalesce(d.margin_usd, 0)
         - b.baseline_units * (a.n_weeks + coalesce(d.n_weeks, 0)) * a.full_price_margin_per_unit as incremental_margin_usd,
       ov.promo_id is not null as overlaps_event, ov.event_depth,
       case when ov.promo_id is not null then (a.units - b.baseline_units * a.n_weeks) * p.depth / (p.depth + ov.event_depth)
            else a.units - b.baseline_units * a.n_weeks end as lift_units_attributed,
       b.n_pre >= least({{ var('min_clean_pre_weeks') }}, case b.method when 'pre4' then 4 else 99 end) and a.all_complete and ov.promo_id is null as is_eligible
from promo p
join base b using (promo_id)
join act a on a.promo_id = p.promo_id and a.kind = 'promo'
left join act d on d.promo_id = p.promo_id and d.kind = 'dip'
left join ov on ov.promo_id = p.promo_id
