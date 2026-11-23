"""Write analysis/results.md: the headline numbers the README and brief quote, straight from the gold marts.

Usage: python analysis/report.py --db warehouse/market.duckdb --out analysis/results.md
"""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "warehouse" / "market.duckdb"))
    ap.add_argument("--out", default=str(ROOT / "analysis" / "results.md"))
    a = ap.parse_args()
    con = duckdb.connect(a.db, read_only=True)
    q = lambda sql: con.execute(sql).fetchone()  # noqa: E731
    pts = lambda v: f"{100 * v:+.1f} pts"  # noqa: E731
    pct = lambda v: f"{100 * v:.0f}%"  # noqa: E731
    usd = lambda v: ("-$" if v < 0 else "$") + f"{abs(v):,.0f}"  # noqa: E731

    al = q("select share_latest, change_reported, change_comparable from gold.rpt_share_change where market = 'All' and category = 'All'")
    de = q("select change_reported, change_comparable, share_of_change_surviving from gold.rpt_share_change where market = 'DE' and category = 'All'")
    uk = q("select change_comparable from gold.rpt_share_change where market = 'UK' and category = 'Earbuds'")[0]
    oth = q("select avg(change_comparable) from gold.rpt_share_change where market in ('US', 'FR', 'JP') and category = 'Earbuds'")[0]
    gap = q("""select avg(price_gap) filter (where week_start between '2026-01-01' and '2026-05-31'), avg(price_gap) filter (where week_start >= '2026-06-01')
               from gold.rpt_price_gap_weekly where market = 'UK' and pair_id = 'PAIR-E'""")
    lau = dict(con.execute("""select market, sum(units) filter (where sku = 'CV-E400') / sum(units) filter (where sku = 'CV-E300')
                              from gold.rpt_launch_cohort where weeks_since_launch < 12 group by 1""").fetchall())
    rest = sum(v for k, v in lau.items() if k != "JP") / (len(lau) - 1)
    dep = dict(con.execute("select depth_band, incremental_margin_usd from gold.rpt_promo_depth").fetchall())
    ov = q("select sum(lift_units), sum(lift_units_attributed) from gold.rpt_promo_eval where method = 'pre8' and overlaps_event")
    br = q("select count(*) filter (where not within_tolerance), count(*) from gold.rpt_reconciliation_monthly")
    rows = [
        ("Corvane value share, all markets, latest 13 weeks", pct(al[0]), f"{pts(al[1])} reported, {pts(al[2])} comparable"),
        ("Germany share change, reported", pts(de[0]), "Elektra Markt joined the panel in April 2026"),
        ("Germany share change, comparable panel", pts(de[1]), f"{pct(de[2])} of the reported change survives"),
        ("UK earbuds share change (comparable)", pts(uk), f"US, France, Japan average {pts(oth)}"),
        ("UK earbuds price gap, Corvane Buds against Askel Pods 3", f"{100 * gap[0]:+.0f}% to {100 * gap[1]:+.0f}%", "Jan to May 2026, then since June"),
        ("Arc Buds first 12 weeks against Pulse Buds, Japan", pct(lau["JP"]), f"other markets {pct(rest)}"),
        ("Incremental margin, medium promotions (15-24%)", usd(dep['Medium (15-24%)']), "eligible, 8-week baseline"),
        ("Incremental margin, deep promotions (25%+)", usd(dep['Deep (25%+)']), ""),
        ("Incremental margin, shallow promotions (<15%)", usd(dep['Shallow (<15%)']), ""),
        ("Black Friday SKU promotions inside the event", f"{ov[0]:,.0f} naive, {ov[1]:,.0f} attributed", "extra units"),
        ("Monthly cells outside the 2% tolerance", f"{br[0]} of {br[1]:,}", "Germany, speakers, Corvane, Feb 2026"),
    ]
    out = ["# Results from the current build", "",
           "Written by `analysis/report.py` from the gold marts on every `make dashboards`. Demo results on synthetic data.", "",
           "| Measure | Value | Note |", "|---|---|---|"] + [f"| {a1} | {b} | {c} |" for a1, b, c in rows]
    Path(a.out).write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
