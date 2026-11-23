"""Every planted pattern comes back out of the gold marts, found by the reports' own logic."""
import json

from conftest import ROOT, one

KEY = json.loads((ROOT / "data" / "raw" / "answer_key.json").read_text(encoding="utf-8"))


def test_germany_share_gain_is_mostly_panel_coverage(con):
    rep, cmp, surv = one(con, "select change_reported, change_comparable, share_of_change_surviving from gold.rpt_share_change where market = 'DE' and category = 'All'")
    assert rep > 0.06 and 0 < cmp < rep / 2 and surv < 0.4
    others = con.execute("select share_of_change_surviving from gold.rpt_share_change where category = 'All' and market not in ('DE', 'All')").fetchall()
    assert all(abs(o[0] - 1) < 1e-9 for o in others if o[0] is not None)


def test_comparable_share_jump_is_absent_in_the_join_week(con):
    jump, jump_cmp = one(con, f"""select max(value_share) filter (where week_start >= '{KEY['panel_join']['from']}') - max(value_share) filter (where week_start < '{KEY['panel_join']['from']}'),
                                         max(value_share_comparable) filter (where week_start >= '{KEY['panel_join']['from']}') - max(value_share_comparable) filter (where week_start < '{KEY['panel_join']['from']}')
                                  from gold.rpt_share_weekly where market = 'DE' and category = 'All'
                                    and week_start between date '{KEY['panel_join']['from']}' - interval 28 day and date '{KEY['panel_join']['from']}' + interval 21 day""")
    assert jump > 0.05 and abs(jump_cmp) < 0.02


def test_uk_earbuds_lose_share_after_the_competitor_price_cut(con):
    rows = dict(con.execute("select market, change_comparable from gold.rpt_share_change where category = 'Earbuds'").fetchall())
    assert rows["UK"] < 0 and all(rows[m] > 0.04 for m in ("US", "FR", "JP"))
    before, after = one(con, f"""select avg(price_gap) filter (where week_start < '{KEY['uk_price_cut']['from']}' and week_start >= '2026-01-01'),
                                        avg(price_gap) filter (where week_start >= '{KEY['uk_price_cut']['from']}')
                                 from gold.rpt_price_gap_weekly where market = 'UK' and pair_id = 'PAIR-E'""")
    assert after - before > 0.12


def test_japan_launch_ramps_slower_where_listing_was_late(con):
    def ratio(market):
        arc, pulse = one(con, f"""select sum(units) filter (where sku = 'CV-E400'), sum(units) filter (where sku = 'CV-E300')
                                  from gold.rpt_launch_cohort where market = '{market}' and weeks_since_launch between 0 and 11""")
        return arc / pulse
    assert ratio("JP") < 0.8 * min(ratio(m) for m in ("US", "UK", "DE", "FR"))
    (late,) = one(con, "select max(retailers_selling) from gold.rpt_launch_cohort where sku = 'CV-E400' and market = 'JP' and weeks_since_launch < 10")
    assert late == 2


def test_overlap_handling_brings_the_estimate_back_to_the_truth(con):
    truth = KEY["promo_truth"]
    rows = con.execute("select promo_id, lift_units, lift_units_attributed from gold.rpt_promo_eval where overlaps_event and method = 'pre8'").fetchall()
    assert len(rows) == 3
    for pid, naive, attributed in rows:
        t = truth[pid]["incremental_units"]
        assert naive > 1.4 * t and abs(attributed / t - 1) < 0.15


def test_lift_intervals_cover_the_truth(con):
    truth = KEY["promo_truth"]
    rows = con.execute("select promo_id, lift_units, ci_half_width_units from gold.rpt_promo_eval where method = 'pre8' and is_eligible").fetchall()
    covered = sum(abs(l - truth[p]["incremental_units"]) <= h for p, l, h in rows) / len(rows)
    assert covered >= 0.8
    wape = sum(abs(l - truth[p]["incremental_units"]) for p, l, _ in rows) / sum(truth[p]["incremental_units"] for p, _, _ in rows)
    assert wape < 0.2


def test_deeper_promotions_lift_more(con):
    rows = dict(con.execute("select depth_band, avg_lift_pct from gold.rpt_promo_depth").fetchall())
    assert rows["Shallow (<15%)"] < rows["Medium (15-24%)"] < rows["Deep (25%+)"]


def test_monthly_revision_is_the_only_reconciliation_break(con):
    rows = con.execute("select month_start, market, category, brand from gold.rpt_reconciliation_monthly where not within_tolerance").fetchall()
    r = KEY["monthly_revision"]
    assert [(str(x[0]), x[1], x[2], x[3]) for x in rows] == [(r["month"], r["market"], r["category"], r["brand"])]


def test_panel_revision_and_missing_week_are_detected(con):
    (rev,) = one(con, "select count(distinct week_start) from silver.stg_panel_weekly where was_revised")
    assert rev == 4
    (miss,) = one(con, "select records from gold.rpt_data_checks where check_name = 'Panel retailer-weeks missing from the feed'")
    assert miss == 1
    bad = con.execute("select market, month_start from gold.rpt_panel_vs_sales where outside_2pct").fetchall()
    assert all(m == "US" and str(d) == "2026-05-01" for m, d in bad) and bad
