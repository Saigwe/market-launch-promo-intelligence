"""Write the seven dashboard pages and data.js. Run export.py first.

Usage: python dashboards/build.py [--data dashboards/site/data.json] [--site dashboards/site]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ECHARTS = "https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"
REPO = "https://github.com/Saigwe/market-launch-promo-intelligence"

PAGES = [
    ("index.html", "brief", "Executive brief"),
    ("share.html", "share", "Market &amp; share"),
    ("pricing.html", "pricing", "Price gaps"),
    ("launch.html", "launch", "Launches"),
    ("promotions.html", "promo", "Promotions"),
    ("portfolio.html", "portfolio", "Product portfolio"),
    ("checks.html", "checks", "Data checks"),
]


def card(cid: str, title: str, sub: str, src: str = "", wide: bool = False, tall: bool = False, chart: bool = True,
         extra: str = "") -> str:
    return f'''
    <section class="card{' wide' if wide else ''}" id="{cid}">
      <header><div><h2>{title}</h2><p class="sub">{sub}</p></div>{'<button class="tbl-btn" type="button" aria-pressed="false">Table</button>' if chart else ''}</header>
      {extra}{f'<div class="chart{" tall" if tall else ""}" role="img" aria-label="{title}"></div>' if chart else ''}
      <div class="table-view" hidden></div>
      <p class="src">{src or "Source: dbt gold marts on DuckDB"}</p>
    </section>'''


def scope(text: str) -> str:
    return f'\n  <div class="filters"><span class="scope">{text}</span></div>'


MARKET_FILTER = '''
  <div class="filters" role="group" aria-label="Filters">
    <label>Market <span class="seg" id="f-market">
      <button type="button" data-v="DE" aria-pressed="true">Germany</button><button type="button" data-v="All" aria-pressed="false">All markets</button><button type="button" data-v="US" aria-pressed="false">US</button><button type="button" data-v="UK" aria-pressed="false">UK</button><button type="button" data-v="FR" aria-pressed="false">France</button><button type="button" data-v="JP" aria-pressed="false">Japan</button></span></label>
    <span class="scope" id="f-scope"></span>
  </div>'''

GRID_OPEN, GRID_CLOSE = '\n  <div class="tiles" id="tiles"></div>\n  <div class="grid">', '\n  </div>'

BODIES = {
    "brief": ("Executive brief",
              "Did Corvane grow because the market grew, because of mix, price or promotions, or because the panel changed? And how sure are we?",
              scope("Corvane Audio (fictional), five markets, a retail-tracking panel and the brand's own sell-out, Jan 2024 to Oct 2026. "
                    "Share is value share in USD. \"Latest\" is the last 13 complete weeks against the same weeks a year earlier. Synthetic data.") + GRID_OPEN +
              card("br-insights", "What the evidence supports", "Each item links to the page with the detail.",
                   "Computed from every page", wide=True, chart=False, extra='<ul class="insights" id="insights"></ul>') +
              card("br-change", "Share change by market: reported and comparable panel", "Value share, latest 13 weeks against a year earlier, points") +
              card("br-share", "Corvane value share, all markets", "Weekly. Comparable panel: retailers covered since January 2024") +
              GRID_CLOSE),
    "share": ("Market &amp; share",
              "Weekly value share from the panel, on the retailers it reports and on a comparable panel, with the monthly provider as an independent check.",
              MARKET_FILTER + GRID_OPEN +
              card("sh-line", "Corvane value share by week", "Reported against comparable panel", wide=True) +
              card("sh-bridge", "What explains the change", "Points of value share: year ago, panel coverage, comparable change, latest") +
              card("sh-cat", "Share change by category", "Comparable panel, latest 13 weeks against a year earlier, points") +
              card("sh-recon", "Weekly panel against the monthly provider", "Market value by month, local currency. The weekly series is spread to months by day", wide=True) +
              GRID_CLOSE),
    "pricing": ("Price gaps",
                "Shelf prices for comparable products at the same retailers: Corvane against Askel's equivalent.",
                scope("Gap = Corvane shelf price / competitor shelf price - 1, averaged over panel retailers observed that week. Corvane "
                      "promotions show as dips. Synthetic data.") + GRID_OPEN +
                card("pg-earbuds", "Earbuds price gap: Corvane Buds against Askel Pods 3", "By market, weekly", wide=True) +
                card("pg-uk", "UK earbuds: Corvane share against other markets", "Comparable-panel value share, earbuds, weekly") +
                card("pg-pairs", "Average gap by pair and market, last 13 weeks", "Positive: Corvane is dearer") +
                GRID_CLOSE),
    "launch": ("Launches",
               "Post-launch cohorts: how each launch sold week by week, against the previous launch in the same market.",
               scope("Arc Buds launched on 2 March 2026; Pulse Buds on 3 March 2025. Week 0 is the launch week. Complete weeks only.") + GRID_OPEN +
               card("ln-curve", "Units by week since launch, all markets", "Arc Buds against Pulse Buds") +
               card("ln-index", "Arc Buds first 12 weeks against Pulse Buds, by market", "Units, Arc / Pulse, same weeks since launch") +
               card("ln-jp", "Japan: retailers selling Arc Buds", "Number of panel retailers with sales, by week since launch") +
               card("ln-mkt", "Arc Buds units by market", "By week since launch") +
               GRID_CLOSE),
    "promo": ("Promotions",
              "Estimated lift, margin and uncertainty for each completed promotion, and what the planned ones are likely to earn.",
              scope("Estimated lift = units in the promotion weeks minus a baseline from clean weeks before it. Intervals are 95%. This "
                    "is an estimate from observational data, not an experiment.") + GRID_OPEN +
              card("pm-depth", "Lift and incremental margin by depth", "Eligible promotions, 8-week baseline. Bars: average lift; table adds the p10 to p90 range and margin") +
              card("pm-margin", "Incremental margin by depth", "USD, after the discount on baseline units and the dip in the two weeks after") +
              card("pm-forest", "Estimated lift with 95% interval, largest promotions", "Eligible promotions, 8-week baseline. Lift as a share of baseline units", wide=True, tall=True) +
              card("pm-overlap", "Promotions inside a store-wide event", "Grandmart, Black Friday 2025. Naive credits the SKU promotion with everything") +
              card("pm-sens", "Sensitivity to the baseline", "Average estimated lift, eligible promotions, by baseline method") +
              card("pm-scenario", "Planned promotions: likely margin", "Expected incremental margin, with the p10 to p90 range from history", wide=True) +
              GRID_CLOSE),
    "portfolio": ("Product portfolio",
                  "Every Corvane product: what it sells, at what price and margin, and how it is moving.",
                  scope("Last 13 complete weeks against the same weeks a year earlier, all markets, USD at weekly average rates. "
                        "Corvane Loop is shown under Earbuds for all history (reclassified January 2026).") + GRID_OPEN +
                  card("pf-sales", "Net sales by product, last 13 weeks", "USD") +
                  card("pf-growth", "Growth against a year earlier", "Net sales, last 13 weeks") +
                  card("pf-table", "All products", "Sorted by net sales", wide=True, chart=False, extra='<div id="product-table" class="table-view"></div>') +
                  GRID_CLOSE),
    "checks": ("Data checks",
               "What the pipeline found and handled, and the reconciliations that run on every build.",
               scope("dbt staging and tests, plus pytest, on every push. Revised deliveries replace earlier ones; nothing is silently dropped.") + GRID_OPEN +
               card("ck-list", "Checks on the latest build", "From rpt_data_checks", wide=True, chart=False, extra='<div id="checks"></div>') +
               card("ck-recon", "Monthly provider against the weekly panel", "Largest cell difference (category x brand) by market and month. Tolerance 2%", wide=True) +
               card("ck-panel", "Panel against Corvane's own sales", "Corvane units, same retailer-weeks, difference by market and month") +
               card("ck-rules", "Definitions this warehouse enforces", "Where each is tested", chart=False, extra='<div id="rules"></div>') +
               GRID_CLOSE),
}


def ver(site: Path) -> str:
    h = hashlib.sha1()
    for f in ("assets/style.css", "assets/charts.js", "assets/pages.js", "data.js"):
        h.update((site / f).read_bytes())
    return h.hexdigest()[:10]


def page(key: str, v: str = "") -> str:
    title, lede, body = BODIES[key]
    nav = "".join(f'<a href="{f}"{" aria-current=page" if k == key else ""}>{label}</a>' for f, k, label in PAGES)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title.replace("&amp;", "&")} · Market, launch and promotion intelligence</title>
<meta name="description" content="Market share on a comparable panel, price gaps, launch cohorts and promotion lift with uncertainty, for a fictional audio brand, on synthetic data.">
<link rel="stylesheet" href="assets/style.css?v={v}">
<script src="{ECHARTS}" defer></script>
<script src="assets/charts.js?v={v}" defer></script>
<script src="data.js?v={v}" defer></script>
<script src="assets/pages.js?v={v}" defer></script>
</head>
<body class="viz-root" data-page="{key}">
<div class="top"><div class="wrap">
  <div class="brand">Corvane Audio <span>· market intelligence · synthetic data</span></div>
  <nav class="tabs" aria-label="Dashboards">{nav}</nav>
  <button class="theme-btn" type="button">Dark mode</button>
</div></div>
<main class="wrap">
  <div class="page-head"><h1>{title}</h1><p>{lede}</p></div>
{body}
  <p class="footnote">Corvane Audio, Askel, Nobu, Tervo, every retailer and every number here are invented. Demo results, not any company's figures.
  Built from dbt marts on DuckDB, rebuilt by CI on every change. Code: <a href="{REPO}">market-launch-promo-intelligence</a>.
  Built by <a href="https://saigwe.github.io">Stanley Igwe</a>.</p>
</main>
</body>
</html>
'''


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(HERE / "site" / "data.json"))
    ap.add_argument("--site", default=str(HERE / "site"))
    a = ap.parse_args()
    site = Path(a.site)
    data = json.loads(Path(a.data).read_text(encoding="utf-8"))
    (site / "data.js").write_text("window.DASH = " + json.dumps(data, separators=(",", ":")) + ";\n", encoding="utf-8")
    v = ver(site)
    for fname, key, _ in PAGES:
        (site / fname).write_text(page(key, v), encoding="utf-8", newline="\n")
    print(f"wrote {len(PAGES)} pages to {site}")


if __name__ == "__main__":
    main()
