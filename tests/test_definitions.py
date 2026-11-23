"""Measure definitions behave as documented: non-additive shares, FX policy, restatement, incomplete weeks."""
from conftest import one


def test_share_is_a_ratio_of_sums_not_an_average_of_shares(con):
    total, avg_of_cats = one(con, """select max(value_share) filter (where category = 'All'), avg(value_share) filter (where category <> 'All')
                                     from gold.rpt_share_weekly where market = 'US' and week_start = '2026-06-01'""")
    (recomputed,) = one(con, """select sum(value_usd) filter (where brand = 'Corvane') / sum(value_usd) from gold.fct_panel_weekly
                               where market = 'US' and week_start = '2026-06-01'""")
    assert abs(total - recomputed) < 1e-9 and abs(total - avg_of_cats) > 1e-4


def test_all_markets_share_uses_usd(con):
    (a,) = one(con, "select value_share from gold.rpt_share_weekly where market = 'All' and category = 'All' and week_start = '2026-06-01'")
    (b,) = one(con, "select sum(corvane_value_usd) / sum(market_value_usd) from gold.rpt_share_weekly where market <> 'All' and category = 'All' and week_start = '2026-06-01'")
    assert abs(a - b) < 1e-9


def test_incomplete_week_is_excluded_from_shares(con):
    (n,) = one(con, "select count(*) from gold.rpt_share_weekly s join gold.dim_week w using (week_start) where not w.is_complete")
    assert n == 0


def test_reclassified_sku_is_restated_everywhere(con):
    (cats,) = one(con, "select count(distinct category) from gold.fct_sales_weekly where sku = 'CV-H400'")
    (src,) = one(con, "select count(distinct category_at_sale) from gold.fct_sales_weekly where sku = 'CV-H400'")
    assert cats == 1 and src == 2


def test_restatement_removes_the_false_jump_in_earbuds(con):
    # Under source categories, Earbuds "grow" in January 2026 when the neckband moves in; restated, they do not jump.
    def growth(col):
        a, b = one(con, f"""select sum(units) filter (where week_start between '2026-01-05' and '2026-02-01'),
                                   sum(units) filter (where week_start between '2025-12-01' and '2025-12-28')
                            from gold.fct_sales_weekly where {col} = 'Earbuds' and market = 'FR'""")
        return a / b
    assert growth("category_at_sale") > growth("category") + 0.1


def test_scorecard_totals_reconcile_to_the_fact(con):
    a, b = one(con, """select (select sum(corvane_value_usd) from gold.rpt_share_weekly where market = 'All' and category = 'All'),
                              (select sum(value_usd) from gold.fct_panel_weekly where brand = 'Corvane' and is_complete)""")
    assert abs(a - b) < 0.01
