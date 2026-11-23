# Report specification

A Power BI report on the gold marts. The web dashboards implement each page; measures are in
[measures.dax](measures.dax).

## Model

- Facts: `fct_panel_weekly`, `fct_sales_weekly`, `rpt_reconciliation_monthly` (monthly grain, its own date),
  `rpt_price_gap_weekly`, `rpt_promo_eval`, `rpt_launch_cohort`.
- Dimensions: `dim_week` (weekly facts), a month table for the monthly fact, `dim_product`, `dim_retailer`
  (with `is_constant_panel`), markets. Weekly and monthly facts do not share a date table: a weekly-to-monthly view
  goes through `int_week_month_bridge`.
- Filter `dim_week[is_complete] = TRUE` on every trend page.

## Pages

| Page | Visuals |
|---|---|
| Executive brief | share cards (reported, comparable, change); share change by market; decision list |
| Market & share | weekly value share, reported against comparable; coverage bridge; category change; weekly against monthly |
| Price gaps | gap by market and pair; UK earbuds share against other markets |
| Launches | cohort curves; Arc / Pulse by market; retailers selling |
| Promotions | lift by depth with p10-p90; incremental margin; lift with intervals; overlap; baseline sensitivity; planned scenario |
| Product portfolio | net sales, growth, ASP, margin, discount by product |

## Acceptance checks

- Value Share for All markets equals the ratio of summed USD, not an average of market shares, under any filter.
- Share Change Comparable equals `rpt_share_change.change_comparable` for each market.
- Lift Units for a promotion equals `rpt_promo_eval` for method pre8.
