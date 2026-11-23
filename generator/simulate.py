"""Synthetic market-intelligence feeds for Corvane Audio, a fictional headphone and speaker brand.

Writes, as the source systems would deliver them:
  sales_weekly      Corvane sell-out by SKU, retailer and week (the brand's own data, every retailer)
  panel_weekly      a retail-tracking panel: units and value by retailer, category and brand, panel retailers only,
                    with a revised delivery for some weeks and one missing retailer-week
  market_monthly    an independently sourced monthly market series (different provider), months closed to Sep 2026
  retail_prices     scraped shelf prices for comparable product pairs
  promotions        the promotion calendar (completed and planned), including a store-wide event
  products, product_class_history, retailers, markets, panel_coverage, comparable_pairs, fx_daily
  answer_key.json   what was planted, for the tests

Planted:
  * Elektra Markt (Germany) joins the panel on 2026-04-06. Corvane is strong there, so reported share jumps.
  * Askel cuts the price of its flagship earbuds in the UK by 15% from 2026-06-01; Corvane UK earbuds lose share.
  * Arc Buds launch on 2026-03-02 everywhere; in Japan two of four retailers list them only ten weeks later.
  * A store-wide event at Grandmart (US) in Black Friday weeks overlaps three SKU promotions.
  * Corvane Loop is reclassified from Headphones to Earbuds on 2026-01-05.
  * The monthly provider's Germany speakers figure for Corvane in Feb 2026 is 6% off (a source revision).
Every name and number is invented.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

START = date(2024, 1, 1)            # Monday
AS_OF = date(2026, 10, 28)          # extract date: the week of 26 Oct holds only three days
MONTHLY_CLOSED = date(2026, 9, 30)  # monthly provider publishes closed months only

MARKETS = pd.DataFrame([
    ("US", "United States", "USD", 1.0), ("UK", "United Kingdom", "GBP", 1.27), ("DE", "Germany", "EUR", 1.08),
    ("FR", "France", "EUR", 1.08), ("JP", "Japan", "JPY", 0.0068)],
    columns=["market", "market_name", "currency", "std_usd_per_unit"])
SIZE = {"US": 1.0, "UK": 0.25, "DE": 0.30, "FR": 0.22, "JP": 0.35}
CAT_BASE = {"Headphones": 30000, "Earbuds": 45000, "Speakers": 25000}   # weekly units, US panel

RETAILERS = [
    ("R-US1", "US", "Grandmart", 0.35), ("R-US2", "US", "Voltline", 0.30), ("R-US3", "US", "ClickCart", 0.20), ("R-US4", "US", "Sonic Depot", 0.15),
    ("R-UK1", "UK", "Highstreet Tech", 0.35), ("R-UK2", "UK", "Brightbuy", 0.30), ("R-UK3", "UK", "Parcelhub", 0.20), ("R-UK4", "UK", "Audio Corner", 0.15),
    ("R-DE1", "DE", "Kaufzone", 0.35), ("R-DE2", "DE", "Technikhaus", 0.30), ("R-DE3", "DE", "Netzkauf", 0.20), ("R-DE4", "DE", "Klangwelt", 0.15),
    ("R-DE5", "DE", "Elektra Markt", 0.33),
    ("R-FR1", "FR", "Maison Tech", 0.35), ("R-FR2", "FR", "Achat Plus", 0.30), ("R-FR3", "FR", "Le Son", 0.20), ("R-FR4", "FR", "Rapide", 0.15),
    ("R-JP1", "JP", "Denki One", 0.35), ("R-JP2", "JP", "Sora Mart", 0.30), ("R-JP3", "JP", "Kaden Plaza", 0.20), ("R-JP4", "JP", "Oto Shop", 0.15),
]
PANEL_JOIN = ("R-DE5", date(2026, 4, 6))
BRANDS = ["Corvane", "Askel", "Nobu", "Tervo", "Other brands"]
SHARE = {  # unit share by category in the panel, before planted effects
    "Headphones": {"Corvane": 0.18, "Askel": 0.22, "Nobu": 0.15, "Tervo": 0.12},
    "Earbuds": {"Corvane": 0.12, "Askel": 0.25, "Nobu": 0.18, "Tervo": 0.10},
    "Speakers": {"Corvane": 0.16, "Askel": 0.14, "Nobu": 0.20, "Tervo": 0.18},
}
PRICE_USD = {  # average selling price per unit, USD at standard rates
    "Askel": {"Headphones": 200, "Earbuds": 130, "Speakers": 120}, "Nobu": {"Headphones": 150, "Earbuds": 100, "Speakers": 140},
    "Tervo": {"Headphones": 120, "Earbuds": 80, "Speakers": 110}, "Other brands": {"Headphones": 60, "Earbuds": 40, "Speakers": 50},
}
PRODUCTS = [  # sku, name, category (current), launch, list price USD, weight within Corvane category
    ("CV-H100", "Corvane Halo", "Headphones", None, 179, 0.30), ("CV-H200", "Corvane Halo Pro", "Headphones", None, 299, 0.25),
    ("CV-H300", "Corvane Studio", "Headphones", None, 349, 0.15), ("CV-H400", "Corvane Loop", "Earbuds", None, 99, 0.20),
    ("CV-H500", "Corvane Kid", "Headphones", None, 59, 0.10),
    ("CV-E100", "Corvane Buds", "Earbuds", None, 149, 0.40), ("CV-E200", "Corvane Buds Sport", "Earbuds", None, 129, 0.25),
    ("CV-E300", "Corvane Pulse Buds", "Earbuds", date(2025, 3, 3), 199, 0.0), ("CV-E400", "Corvane Arc Buds", "Earbuds", date(2026, 3, 2), 229, 0.0),
    ("CV-E500", "Corvane Buds Lite", "Earbuds", None, 79, 0.35),
    ("CV-S100", "Corvane Go", "Speakers", None, 129, 0.35), ("CV-S200", "Corvane Go Max", "Speakers", None, 199, 0.20),
    ("CV-S300", "Corvane Home", "Speakers", None, 249, 0.20), ("CV-S400", "Corvane Bar", "Speakers", None, 399, 0.15),
    ("CV-S500", "Corvane Bar Max", "Speakers", None, 699, 0.10),
]
RECLASS = ("CV-H400", "Headphones", "Earbuds", date(2026, 1, 5))
JP_LATE_LISTING = {"R-JP3", "R-JP4"}
UK_PRICE_CUT = date(2026, 6, 1)
EVENT = ("R-US1", [date(2025, 11, 24), date(2025, 12, 1)], 0.15)
PAIRS = [("PAIR-H", "CV-H200", "Askel AX7", "Headphones", 279), ("PAIR-E", "CV-E100", "Askel Pods 3", "Earbuds", 139),
         ("PAIR-S", "CV-S100", "Askel Boom", "Speakers", 119)]


def season(d: date) -> float:
    s = 1.0 + 0.08 * np.sin(2 * np.pi * (d.timetuple().tm_yday - 80) / 365)
    nov = date(d.year, 11, 1)
    bf = nov + timedelta(days=(4 - nov.weekday()) % 7 + 21)       # fourth Friday of November
    if bf - timedelta(days=4) <= d <= bf + timedelta(days=2):
        s += 0.9
    elif date(d.year, 12, 1) <= d <= date(d.year, 12, 21):
        s += 0.45
    return s


def ramp(d: date, launch: date | None, weeks: int = 8) -> float:
    if launch is None:
        return 1.0
    if d < launch:
        return 0.0
    return min(1.0, ((d - launch).days // 7 + 1) / weeks)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="data/raw")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    weeks = []
    d = START
    while d <= AS_OF:
        weeks.append(d)
        d += timedelta(days=7)
    std = dict(zip(MARKETS.market, MARKETS.std_usd_per_unit))
    cur = dict(zip(MARKETS.market, MARKETS.currency))

    # FX: daily rates, a gentle walk around the standard rate
    days = pd.date_range(START - timedelta(days=7), AS_OF, freq="D")
    fx = []
    for c, s in {"GBP": 1.27, "EUR": 1.08, "JPY": 0.0068}.items():
        walk = np.cumsum(rng.normal(0, 0.0025, len(days)))
        fx += [(dd.date(), c, round(float(s * np.exp(w)), 6)) for dd, w in zip(days, walk)]
    fx += [(dd.date(), "USD", 1.0) for dd in days]
    fx = pd.DataFrame(fx, columns=["rate_date", "currency", "usd_per_unit"])

    prods = pd.DataFrame(PRODUCTS, columns=["sku", "product_name", "category", "launch_date", "list_price_usd", "weight"])
    prods["brand"] = "Corvane"
    prods["unit_cost_usd"] = (prods.list_price_usd * 0.35).round(2)
    hist = []
    for p in PRODUCTS:
        if p[0] == RECLASS[0]:
            hist += [(p[0], RECLASS[1], START, RECLASS[3] - timedelta(days=1)), (p[0], RECLASS[2], RECLASS[3], None)]
        else:
            hist.append((p[0], p[2], START, None))
    hist = pd.DataFrame(hist, columns=["sku", "category", "valid_from", "valid_to"])

    def gen_category(sku: str) -> str:                    # the category used for generating volume (stable)
        return RECLASS[1] if sku == RECLASS[0] else prods.set_index("sku").category[sku]

    def cat_at(sku: str, d: date) -> str:                 # the category the source systems label it with on day d
        if sku == RECLASS[0]:
            return RECLASS[1] if d < RECLASS[3] else RECLASS[2]
        return prods.set_index("sku").category[sku]

    gen_cat = {p[0]: gen_category(p[0]) for p in PRODUCTS}
    pinfo = {p[0]: p for p in PRODUCTS}

    # Promotions: SKU promotions with clean pre-periods, the store-wide event, and planned ones for the scenario page
    promos = []
    pid = 0
    retailers = pd.DataFrame(RETAILERS, columns=["retailer_id", "market", "retailer_name", "weight"])
    for r in retailers.itertuples():
        last_on = {}
        for _ in range(int(rng.integers(5, 8))):
            for _try in range(30):
                sku = PRODUCTS[int(rng.integers(len(PRODUCTS)))][0]
                wk = weeks[int(rng.integers(14, len(weeks) - 3))]
                launch = pinfo[sku][3]
                if launch and wk < launch + timedelta(weeks=10):
                    continue
                if sku in last_on and any(abs((wk - x).days) < 84 for x in last_on[sku]):
                    continue
                if r.retailer_id == EVENT[0] and any(abs((wk - e).days) < 70 for e in EVENT[1]):
                    continue
                break
            else:
                continue
            dur = int(rng.choice([1, 2, 2, 3]))
            depth = float(rng.choice([0.10, 0.15, 0.20, 0.25, 0.30]))
            pid += 1
            promos.append((f"PR{pid:04d}", sku, r.market, r.retailer_id, wk, wk + timedelta(weeks=dur - 1), depth, "Price cut", False))
            last_on.setdefault(sku, []).append(wk)
    pid += 1
    promos.append((f"PR{pid:04d}", None, "US", EVENT[0], EVENT[1][0], EVENT[1][-1], EVENT[2], "Store-wide event", True))
    for sku in ["CV-H200", "CV-E100", "CV-S100"]:                  # SKU promotions inside the event
        pid += 1
        promos.append((f"PR{pid:04d}", sku, "US", EVENT[0], EVENT[1][0], EVENT[1][-1], 0.20, "Price cut", False))
    promos = pd.DataFrame(promos, columns=["promo_id", "sku", "market", "retailer_id", "start_week", "end_week", "depth", "mechanic", "is_event"])
    promos["status"] = "completed"
    plan = [("PL001", "CV-E400", "US", "R-US2", date(2026, 11, 23), date(2026, 11, 30), 0.20), ("PL002", "CV-H200", "UK", "R-UK1", date(2026, 11, 23), date(2026, 11, 30), 0.25),
            ("PL003", "CV-S100", "DE", "R-DE1", date(2026, 11, 16), date(2026, 11, 23), 0.30), ("PL004", "CV-E100", "FR", "R-FR2", date(2026, 11, 23), date(2026, 11, 23), 0.15),
            ("PL005", "CV-E300", "JP", "R-JP1", date(2026, 12, 7), date(2026, 12, 14), 0.20), ("PL006", "CV-S400", "US", "R-US1", date(2026, 11, 23), date(2026, 11, 30), 0.10)]
    promos = pd.concat([promos, pd.DataFrame([(p[0], p[1], p[2], p[3], p[4], p[5], p[6], "Price cut", False, "planned") for p in plan], columns=promos.columns)], ignore_index=True)

    def mults(sku: str, rid: str, wk: date):
        """(promo_id, multiplier, depth) for every completed promotion acting on this SKU-retailer-week, including post-promo dips."""
        res = []
        for p in promo_idx.get(rid, []):
            if p.sku is not None and p.sku != sku:
                continue
            k = 2.0 if p.is_event else 3.5
            lift = 1 + k * p.depth
            if p.start_week <= wk <= p.end_week:
                res.append((p.promo_id, lift, p.depth, "promo"))
            elif p.end_week < wk <= p.end_week + timedelta(weeks=2):
                res.append((p.promo_id, 1 - 0.12 * (lift - 1), 0.0, "dip"))
        return res

    done = promos[promos.status == "completed"]
    promo_idx = {}
    for p in done.itertuples():
        promo_idx.setdefault(p.retailer_id, []).append(p)

    sales, panel, truth = [], [], []
    incr = {p: [0.0, 0.0] for p in done.promo_id}
    rows_price = []
    for wi, wk in enumerate(weeks):
        n_days = min(7, (AS_OF - wk).days + 1)
        frac = n_days / 7
        s = season(wk) * (1 + 0.04 * (wk - START).days / 365)
        for r in retailers.itertuples():
            m = r.market
            in_panel = not (r.retailer_id == PANEL_JOIN[0] and wk < PANEL_JOIN[1])
            for cat in CAT_BASE:
                cat_units = CAT_BASE[cat] * SIZE[m] * r.weight * s * frac * np.exp(rng.normal(0, 0.05))
                sh = dict(SHARE[cat])
                if cat == "Earbuds":
                    late = m == "JP" and r.retailer_id in JP_LATE_LISTING
                    arc_launch = pinfo["CV-E400"][3] + (timedelta(weeks=10) if late else timedelta(0))
                    sh["Corvane"] += 0.02 * ramp(wk, pinfo["CV-E300"][3]) + 0.03 * ramp(wk, arc_launch)
                    if m == "UK" and wk >= UK_PRICE_CUT:
                        sh["Corvane"] *= 0.62
                        sh["Askel"] *= 1.35
                if r.retailer_id == PANEL_JOIN[0]:
                    sh["Corvane"] *= 2.3
                sh["Other brands"] = max(0.05, 1 - sum(sh.values()))
                tot = sum(sh.values())
                sh = {b: v / tot for b, v in sh.items()}
                # Corvane SKUs
                cv_by_cat = {}
                cv_val_by_cat = {}
                skus = [p for p in PRODUCTS if gen_cat[p[0]] == cat]
                w = []
                for p in skus:
                    launch = p[3]
                    if p[0] == "CV-E400" and m == "JP" and r.retailer_id in JP_LATE_LISTING:
                        launch = launch + timedelta(weeks=10)
                    base_w = p[5] if p[3] is None else (0.30 if p[0] == "CV-E300" else 0.35)
                    w.append(base_w * ramp(wk, launch))
                w = np.array(w) / sum(w)
                for p, wt in zip(skus, w):
                    if wt == 0:
                        continue
                    base = cat_units * sh["Corvane"] * wt * np.exp(rng.normal(0, 0.08))
                    ms = mults(p[0], r.retailer_id, wk)
                    mult = float(np.prod([x[1] for x in ms])) if ms else 1.0
                    units = base * mult
                    for (prid, mm, _dp, kind) in ms:
                        incr[prid][0 if kind == "promo" else 1] += units - units / mm
                    depth_total = 1 - float(np.prod([1 - x[2] for x in ms])) if ms else 0.0
                    list_local = round(p[4] / std[m], 2)
                    u = int(round(units))
                    gross = u * list_local
                    disc = gross * depth_total
                    c_sale = cat_at(p[0], wk)
                    sales.append((wk, n_days, m, r.retailer_id, p[0], c_sale, u, round(gross, 2), round(disc, 2), round(gross - disc, 2)))
                    cv_by_cat[c_sale] = cv_by_cat.get(c_sale, 0) + u
                    cv_val_by_cat[c_sale] = cv_val_by_cat.get(c_sale, 0) + gross - disc
                # panel rows (panel retailers only)
                if in_panel:
                    for b in BRANDS[1:]:
                        u = int(round(cat_units * sh[b]))
                        price = PRICE_USD[b][cat] / std[m] * (0.85 if (b == "Askel" and cat == "Earbuds" and m == "UK" and wk >= UK_PRICE_CUT) else 1.0)
                        panel.append((wk, m, r.retailer_id, cat, b, u, round(u * price * np.exp(rng.normal(0, 0.01)), 2)))
                    for c_sale, u in cv_by_cat.items():
                        e = np.exp(rng.normal(0, 0.004))
                        panel.append((wk, m, r.retailer_id, c_sale, "Corvane", int(round(u * e)), round(cv_val_by_cat[c_sale] * e, 2)))
            # shelf prices for comparable pairs (panel retailers, complete weeks)
            if in_panel and n_days == 7:
                for pair, cv_sku, comp, cat, comp_usd in PAIRS:
                    ms = [x for x in mults(cv_sku, r.retailer_id, wk) if x[3] == "promo"]
                    dep = 1 - float(np.prod([1 - x[2] for x in ms])) if ms else 0.0
                    cv_p = pinfo[cv_sku][4] / std[m] * (1 - dep)
                    comp_p = comp_usd / std[m] * (0.85 if (cat == "Earbuds" and m == "UK" and wk >= UK_PRICE_CUT) else 1.0)
                    if rng.random() > 0.03:
                        rows_price.append((wk, m, r.retailer_id, pair, round(cv_p * np.exp(rng.normal(0, 0.01)), 2), round(comp_p * np.exp(rng.normal(0, 0.015)), 2)))

    sales = pd.DataFrame(sales, columns=["week_start", "days_covered", "market", "retailer_id", "sku", "category_at_sale", "units", "gross_sales_local", "discount_local", "net_sales_local"])
    panel = pd.DataFrame(panel, columns=["week_start", "market", "retailer_id", "category", "brand", "units", "value_local"])
    panel = panel.groupby(["week_start", "market", "retailer_id", "category", "brand"], as_index=False).sum()
    panel["days_covered"] = panel.week_start.map(lambda w: min(7, (AS_OF - w).days + 1))
    panel["delivery_id"] = "D1"
    panel["delivered_at"] = panel.week_start.map(lambda w: pd.Timestamp(w + timedelta(days=11)))
    # one missing retailer-week, and a revised delivery for four US weeks
    miss = (panel.retailer_id == "R-UK3") & (panel.week_start == date(2026, 2, 9))
    panel_final = panel.copy()
    rev_mask = (panel.market == "US") & panel.week_start.between(date(2026, 5, 4), date(2026, 5, 25))
    rev = panel[rev_mask].copy()
    rev["units"] = (rev.units * 1.03).round().astype(int)
    rev["value_local"] = (rev.value_local * 1.03).round(2)
    rev["delivery_id"] = "D2"
    rev["delivered_at"] = rev.delivered_at + pd.Timedelta(days=21)
    panel_final.loc[rev_mask, "units"] = rev.units.values
    panel_final.loc[rev_mask, "value_local"] = rev.value_local.values
    panel_out = pd.concat([panel[~miss], rev[~((rev.retailer_id == "R-UK3") & (rev.week_start == date(2026, 2, 9)))]], ignore_index=True)

    # Monthly provider: the panel (final values) spread evenly over the days covered, summed by month, small noise
    pf = panel_final[~miss]
    rows = []
    for row in pf.itertuples():
        for i in range(row.days_covered):
            dd = row.week_start + timedelta(days=i)
            rows.append((dd.replace(day=1), row.market, row.category, row.brand, row.units / row.days_covered, row.value_local / row.days_covered))
    mm = pd.DataFrame(rows, columns=["month", "market", "category", "brand", "units", "value_local"]).groupby(["month", "market", "category", "brand"], as_index=False).sum()
    mm = mm[mm.month <= MONTHLY_CLOSED]
    noise = np.exp(rng.normal(0, 0.004, len(mm)))
    mm["units"] = mm.units * noise
    mm["value_local"] = mm.value_local * noise
    bad = (mm.month == date(2026, 2, 1)) & (mm.market == "DE") & (mm.category == "Speakers") & (mm.brand == "Corvane")
    mm["units"] = (mm.units * np.where(bad, 1.06, 1.0)).round().astype(int)
    mm["value_local"] = (mm.value_local * np.where(bad, 1.06, 1.0)).round(2)
    mm["published_at"] = mm.month.map(lambda x: pd.Timestamp((pd.Timestamp(x) + pd.offsets.MonthEnd(1)).date() + timedelta(days=12)))

    prices = pd.DataFrame(rows_price, columns=["week_start", "market", "retailer_id", "pair_id", "corvane_price_local", "competitor_price_local"])
    pairs = pd.DataFrame([(p[0], p[1], "Askel", p[2], p[3]) for p in PAIRS], columns=["pair_id", "corvane_sku", "competitor_brand", "competitor_product", "category"])
    coverage = pd.DataFrame([(r[0], r[1], PANEL_JOIN[1] if r[0] == PANEL_JOIN[0] else START, None) for r in RETAILERS],
                            columns=["retailer_id", "market", "panel_from", "panel_to"])

    tables = {"markets": MARKETS, "retailers": retailers.drop(columns="weight"), "panel_coverage": coverage, "fx_daily": fx,
              "products": prods.drop(columns="weight"), "product_class_history": hist, "comparable_pairs": pairs,
              "sales_weekly": sales, "panel_weekly": panel_out, "market_monthly": mm, "retail_prices": prices, "promotions": promos}
    for name, df in tables.items():
        df.to_parquet(out / f"{name}.parquet", index=False)
        print(f"{name:22s} {len(df):>9,} rows")

    key = {
        "panel_join": {"retailer_id": PANEL_JOIN[0], "from": str(PANEL_JOIN[1]), "market": "DE"},
        "uk_price_cut": {"brand": "Askel", "category": "Earbuds", "from": str(UK_PRICE_CUT), "cut": 0.15},
        "launch": {"sku": "CV-E400", "date": "2026-03-02", "late_market": "JP", "late_retailers": sorted(JP_LATE_LISTING), "late_weeks": 10, "prior_launch": "CV-E300"},
        "event": {"retailer_id": EVENT[0], "weeks": [str(x) for x in EVENT[1]], "depth": EVENT[2]},
        "reclass": {"sku": RECLASS[0], "from": RECLASS[1], "to": RECLASS[2], "on": str(RECLASS[3])},
        "monthly_revision": {"month": "2026-02-01", "market": "DE", "category": "Speakers", "brand": "Corvane", "factor": 1.06},
        "panel_revision": {"market": "US", "weeks": ["2026-05-04", "2026-05-25"], "factor": 1.03},
        "missing_panel_week": {"retailer_id": "R-UK3", "week_start": "2026-02-09"},
        "promo_truth": {p: {"incremental_units": round(v[0], 1), "post_dip_units": round(v[1], 1)} for p, v in incr.items()},
    }
    (out / "answer_key.json").write_text(json.dumps(key, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
