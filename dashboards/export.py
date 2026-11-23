"""Collect what the dashboard pages show into one JSON document, from the gold marts.

Usage: python dashboards/export.py --db warehouse/market.duckdb --out dashboards/site/data.json
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def rows(con, sql: str) -> list[dict]:
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    out = []
    for r in cur.fetchall():
        rec = {}
        for k, v in zip(cols, r):
            if isinstance(v, date):
                v = v.isoformat()[:10]
            elif isinstance(v, float):
                v = round(v, 6)
            elif v is not None and not isinstance(v, (int, str, bool)):
                v = float(v)
            rec[k] = v
        out.append(rec)
    return out


def collect(con) -> dict:
    d: dict = {}
    d["markets"] = rows(con, "select * from silver.stg_markets order by market")
    d["share"] = rows(con, """select week_start as w, market as m, category as c, value_share as s, value_share_comparable as sc,
                                     unit_share as u, market_value_usd as mv from gold.rpt_share_weekly order by 1""")
    d["change"] = rows(con, "select * from gold.rpt_share_change order by market, category")
    d["brief"] = rows(con, "select * from gold.rpt_exec_brief order by market")
    d["recon"] = rows(con, """select month_start as month, market, sum(value_local_monthly) as monthly, sum(value_local_from_weekly) as weekly,
                                     sum(value_local_monthly) / sum(value_local_from_weekly) - 1 as diff,
                                     count(*) filter (where not within_tolerance) as breaks, max(abs(value_diff_pct)) as worst_cell
                              from gold.rpt_reconciliation_monthly group by all order by 1, 2""")
    d["breaks"] = rows(con, "select * from gold.rpt_reconciliation_monthly where not within_tolerance")
    d["gap"] = rows(con, """select week_start as w, market as m, pair_id as p, category as c, competitor_product as comp, price_gap as g
                            from gold.rpt_price_gap_weekly order by 1""")
    d["cohort"] = rows(con, "select * from gold.rpt_launch_cohort where weeks_since_launch <= 30 order by sku, market, weeks_since_launch")
    d["promo"] = rows(con, """select promo_id, sku, market, retailer_id, start_week, depth, depth_band, promo_weeks, method, baseline_units,
                                     promo_units, lift_units, lift_pct, ci_half_width_units, post_dip_units, incremental_margin_usd,
                                     overlaps_event, lift_units_attributed, is_eligible, n_pre
                              from gold.rpt_promo_eval order by start_week""")
    d["depth"] = rows(con, "select * from gold.rpt_promo_depth order by avg_lift_pct")
    d["scenario"] = rows(con, "select * from gold.rpt_promo_scenario order by start_week")
    d["portfolio"] = rows(con, "select * from gold.rpt_portfolio order by net_sales_usd desc")
    d["products"] = rows(con, "select sku, product_name, category, launch_date from gold.dim_product")
    d["retailers"] = rows(con, "select retailer_id, market, retailer_name, panel_from, is_constant_panel from gold.dim_retailer")
    d["checks"] = rows(con, "select * from gold.rpt_data_checks")
    d["panel_vs_sales"] = rows(con, "select * from gold.rpt_panel_vs_sales order by month_start, market")
    d["as_of"] = rows(con, "select max(week_start) as w from gold.dim_week where is_complete")[0]["w"]
    return d


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "warehouse" / "market.duckdb"))
    ap.add_argument("--out", default=str(HERE / "site" / "data.json"))
    ap.add_argument("--dbt-results", default=str(ROOT / "dbt" / "target" / "run_results.json"))
    a = ap.parse_args()
    with duckdb.connect(a.db, read_only=True) as con:
        data = collect(con)
    rr = Path(a.dbt_results)
    if rr.exists():
        results = json.loads(rr.read_text(encoding="utf-8"))["results"]
        data["dbt"] = {"nodes": len(results), "passed": sum(r["status"] in ("pass", "success") for r in results),
                       "tests": sum(r["unique_id"].startswith("test.") for r in results)}
    Path(a.out).write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {a.out} ({Path(a.out).stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
