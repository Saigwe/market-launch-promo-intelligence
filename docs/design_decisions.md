# Design decisions and lineage

## Lineage

```
raw (Parquet, as delivered)        silver                                              gold
sales_weekly ───────────────────> stg_sales_weekly (restated category) ─┐
products, class history ────────> stg_products ─────────────────────────┼─> fct_sales_weekly ─> rpt_launch_cohort, rpt_portfolio
promotions ─────────────────────> stg_promotions ─> int_promo_calendar ─┘                     └> rpt_promo_eval ─> rpt_promo_depth ─> rpt_promo_scenario
panel_weekly (revisions) ───────> stg_panel_weekly (latest wins) ───────> fct_panel_weekly ─> rpt_share_weekly ─> rpt_share_change ─> rpt_exec_brief
panel_coverage, retailers ──────> stg_retailers ─> dim_retailer (constant panel flag) ┘
market_monthly ─────────────────> stg_market_monthly ────────────────────────────────────────> rpt_reconciliation_monthly <─ int_week_month_bridge
fx_daily ───────────────────────> stg_fx_daily ─> int_fx_weekly, int_fx_monthly
retail_prices, comparable_pairs > stg_* ────────────────────────────────────────────────────> rpt_price_gap_weekly
```

## Decisions

1. **Keep source grains.** Weekly panel and monthly provider are separate facts. The monthly series is the
   independent check, so it is never blended in.
2. **Comparable panel by coverage, not by sales.** A retailer is comparable if the panel covered it for the whole
   period. This removes the coverage effect without choosing retailers by results.
3. **Shares are recomputed, never averaged.** Every share is a ratio of sums at the level asked for, with grouping
   sets for the totals.
4. **Restate history to the current category.** Otherwise a reclassification looks like category growth.
5. **Estimated lift, with intervals and a sensitivity table.** The data is observational; four baselines are shown
   so a reader can see how much the answer depends on the choice.
6. **Overlap is split by an explicit rule.** The joint lift cannot be separated from the data alone, so the split is a
   stated assumption and overlapped promotions stay out of the depth curve.
7. **Rebuild consistency is a CI step.** `make rebuild` regenerates from the same seed, rebuilds with
   `--full-refresh` and compares a fingerprint of every gold mart.
