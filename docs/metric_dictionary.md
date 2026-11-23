# Metric dictionary

Every measure states its grain, its source and its currency policy. Thresholds are demo assumptions (dbt vars).

## Sources and grains

| Source | Grain | Notes |
|---|---|---|
| `sales_weekly` (own sell-out) | SKU x retailer x week | every retailer; local currency; the source's category label kept as `category_at_sale` |
| `panel_weekly` (retail panel) | retailer x category x brand x week | panel retailers only; revised deliveries replace earlier ones |
| `market_monthly` (second provider) | market x category x brand x month | closed months only; used to reconcile, never mixed into weekly figures |
| `retail_prices` (shelf scrape) | pair x retailer x week | comparable product pairs |
| `promotions` | promotion | completed and planned; a store-wide event has no SKU |

Weekly and monthly series keep their own grain. Weekly figures reach a month only through `int_week_month_bridge`,
which splits each week by the days that fall in each month (assumes even daily sales).

## Market measures

| Measure | Definition |
|---|---|
| Units, value | panel units and value; value in USD at the weekly FX policy |
| Value share | Corvane value / market value, summed over the selection. Non-additive: never averaged across markets, categories or weeks |
| Unit share | Corvane units / market units, same rule |
| Comparable (constant) panel | only retailers covered by the panel for the whole period; a retailer that joins later is excluded |
| Share change | share in the last 13 complete weeks minus share in the same weeks a year earlier |
| Change from panel coverage | reported change minus comparable change |
| Share of change surviving | comparable change / reported change |
| Price gap | Corvane shelf price / competitor shelf price - 1, averaged over retailers observed that week |

## Sales and product measures

| Measure | Definition |
|---|---|
| Net sales | gross sales - discount, local currency, then USD at the weekly FX policy |
| ASP | net sales / units |
| Gross margin | net sales USD - units x unit cost USD |
| Growth | net sales in the latest 13 weeks / same weeks a year earlier - 1 |
| Launch cohort | units by weeks since launch (week 0 = launch week); Arc / Pulse compares the same weeks since launch |

## Promotion measures

See [../analysis/promo_effects.md](../analysis/promo_effects.md) for the method and current results.

| Measure | Definition |
|---|---|
| Baseline | mean units of the nearest 4, 8 or 13 clean complete pre-weeks; or the same weeks a year earlier scaled by pre-period growth |
| Estimated lift | promotion-week units - baseline x weeks; as a % of baseline units |
| 95% interval | lift +/- 1.96 x sd_pre x sqrt(n x (1 + n / n_pre)) |
| Post-promotion dip | units in the two weeks after - baseline x 2 |
| Incremental margin | margin in promotion and dip weeks - baseline units x full-price margin |
| Attributed lift (overlap) | joint lift x SKU depth / (SKU depth + event depth) |

## Policies

- **FX.** Weekly figures convert at the average daily rate over the week's covered days; monthly figures at the
  average daily rate over the month. The two are never mixed.
- **Incomplete weeks.** The last week holds three days of data; it is excluded from trends, shares and cohorts.
- **Reclassification.** History is restated to the current category; the source label is kept for audit.
- **Revisions.** The latest delivery of a panel week wins; the count of replaced rows is reported.
