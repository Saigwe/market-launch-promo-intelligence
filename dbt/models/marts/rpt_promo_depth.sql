-- What a promotion of each depth has earned, from eligible promotions on the 8-week baseline.
select depth_band, count(*) as promotions, avg(lift_pct) as avg_lift_pct,
       quantile_cont(lift_pct, 0.1) as p10_lift_pct, quantile_cont(lift_pct, 0.9) as p90_lift_pct,
       avg(post_dip_units / nullif(baseline_units * 2, 0)) as avg_dip_pct,
       sum(incremental_margin_usd) as incremental_margin_usd, avg(incremental_margin_usd) as avg_incremental_margin_usd
from {{ ref('rpt_promo_eval') }}
where method = 'pre8' and is_eligible
group by 1
