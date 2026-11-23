# Market, launch and promotion intelligence

[![ci](https://github.com/Saigwe/market-launch-promo-intelligence/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Saigwe/market-launch-promo-intelligence/actions/workflows/ci.yml)
[![dashboards](https://github.com/Saigwe/market-launch-promo-intelligence/actions/workflows/pages.yml/badge.svg?branch=main)](https://saigwe.github.io/market-launch-promo-intelligence/)

**Live dashboards: [saigwe.github.io/market-launch-promo-intelligence](https://saigwe.github.io/market-launch-promo-intelligence/)**

A commercial intelligence product that tells an executive whether growth came from the market, product mix, price or a
promotion, and makes the uncertainty visible. It combines a retail-tracking panel, the brand's own sell-out, an
independent monthly market series, scraped shelf prices and a promotion calendar, keeping each at its own grain.

Built end to end: a seeded synthetic data generator, a dbt warehouse on DuckDB, seven web dashboards, a promotion
effect-estimation notebook, an executive brief and a DAX measure spec. The scenario is modelled on weekly and monthly
market reporting, product-portfolio (PPPD/PPD) and pricing-and-promotions work at a global consumer-electronics company.

**Everything here is invented.** Corvane Audio, Askel, Nobu, Tervo, every retailer and every number come from
`generator/simulate.py`. The results are demo results on synthetic data, not any company's figures.

## The business

Corvane Audio sells 15 headphones, earbuds and speakers in five markets (US, UK, Germany, France, Japan) through 21
retailers. A retail panel tracks the market weekly; a second provider publishes monthly totals. January 2024 to
October 2026.

## What the reports find

The generator plants known problems; `tests/test_planted_answers.py` checks the marts find each one. From the current
build ([analysis/results.md](analysis/results.md), regenerated on every build):

| Finding | Where |
|---|---|
| Germany's reported share gain of +8.9 points is mostly panel coverage: on a comparable panel it is +2.1 points (24% survives). A retailer where Corvane is strong joined the panel in April 2026 | Market & share |
| UK earbuds lost share (-0.8 points) while other markets gained about +8; a competitor's 15% price cut widened the gap from +7% to +26% | Price gaps |
| Arc Buds sold 80% of the previous launch's first 12 weeks in Japan against 115% elsewhere: two of four retailers listed it ten weeks late | Launches |
| Medium-depth promotions (15-24%) earned about $269k of incremental margin; deep and shallow ones lost money once the dip after is counted | Promotions |
| Three Black Friday SKU promotions inside a store-wide event: 6,887 extra units if credited with everything, 3,935 when the joint lift is split | Promotions |
| The weekly panel and the independent monthly series agree within 2% in 2,474 of 2,475 cells; the exception is flagged | Data checks |

The estimator is checked against the planted truth too: on the 8-week baseline, 88% of 95% intervals contain the true
lift and the weighted error is 14% ([analysis/promo_effects.md](analysis/promo_effects.md)).

## How it fits together

```
generator/simulate.py  ->  data/raw/*.parquet (12 tables + answer key)
dbt/ (DuckDB)          ->  silver: staging (latest delivery, restated categories), date bridge, FX policies, promo calendar
                       ->  gold:   dims, sales and panel facts, 12 report marts                (47 models and tests)
dashboards/            ->  export.py -> data.json -> build.py -> 7 static pages (ECharts), GitHub Pages
analysis/              ->  promo_effects.py (notebook), report.py -> results.md, executive_brief.md, fingerprint.py
bi/                    ->  DAX measures and report spec
docs/                  ->  metric dictionary, design decisions and lineage, demo script
```

## What is tested

- **Comparable panel.** The share jump in the week a retailer joins disappears on the comparable panel.
- **Non-additive share.** Shares are ratios of sums; the all-markets share is in USD; averaging shares gives a different answer.
- **FX date policy.** Weekly figures use the average daily rate over the week; monthly figures the monthly average.
- **Incomplete weeks** are excluded from trends, shares and cohorts.
- **Reclassification.** History is restated to the current category without losing a unit; the false January jump in
  earbuds disappears.
- **Revisions and gaps.** The latest panel delivery wins; a missing retailer-week is counted; panel and own sales agree
  within 2% outside revised weeks.
- **Weekly against monthly.** Weekly panel spread to months by day reconciles to the independent monthly series within a
  2% tolerance; only the planted break fails.
- **Overlapping promotions** are flagged, attributed and kept out of the depth curve.
- **Rebuild consistency.** CI regenerates from the same seed, rebuilds, and compares a fingerprint of every gold mart.

## Run it

```bash
pip install -r requirements.txt
make all        # generate, dbt build, dashboards, notebook and results (about a minute)
make rebuild    # regenerate and rebuild: every gold mart must be identical
make test       # pytest against the built warehouse
make serve      # dashboards on http://localhost:8000
```

On Windows without `make`, run the commands in the `Makefile` in order.

## Limits

- Synthetic data with planted patterns: the findings show the method works, not that any market behaves this way.
- Promotion lifts are estimates from observational data. Intervals are slightly narrow (88% coverage at 95%).
- Spreading weeks to months assumes even daily sales.
- No Power BI file is included: `bi/` holds the DAX measures and report spec. The web dashboards show each page.

## Built by

[Stanley Igwe](https://saigwe.github.io). MIT licence.
