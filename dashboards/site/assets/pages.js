/* Page renderers. Data: window.DASH (data.js, written by dashboards/build.py). */
(function () {
  "use strict";
  const D = window.DASH;
  const { line, bar, heatmap, forest, card, table, fmt, esc } = window.Viz;
  const sum = (a) => a.reduce((x, y) => x + (y || 0), 0);
  const uniq = (a) => [...new Set(a)];
  const avg = (a) => { const v = a.filter((x) => x != null); return v.length ? sum(v) / v.length : null; };
  const mon = (s) => new Date(s + "T00:00:00").toLocaleDateString("en-GB", { month: "short", year: "2-digit" });
  const usdK = (v) => v == null ? "–" : (v < 0 ? "-$" : "$") + (Math.abs(v) >= 1e6 ? (Math.abs(v) / 1e6).toFixed(2) + "M" : Math.abs(v / 1e3).toFixed(0) + "k");
  const pts = (v) => v == null ? "–" : (v >= 0 ? "+" : "") + (100 * v).toFixed(1) + " pts";
  const MK = { All: "All markets", US: "United States", UK: "United Kingdom", DE: "Germany", FR: "France", JP: "Japan" };
  const MKS = ["US", "UK", "DE", "FR", "JP"];
  const PROD = Object.fromEntries(D.products.map((p) => [p.sku, p.product_name.replace(/^Corvane /, "")]));
  const RET = Object.fromEntries(D.retailers.map((r) => [r.retailer_id, r.retailer_name]));
  const weeks = uniq(D.share.map((r) => r.w)).sort();
  const ch = (m, c = "All") => D.change.find((r) => r.market === m && r.category === c) || {};
  const state = { market: "DE" };

  function tiles(list) {
    const el = document.getElementById("tiles");
    if (!el) return;
    el.replaceChildren(...list.map((t) => {
      const d = document.createElement("div"); d.className = "tile";
      const k = document.createElement("div"); k.className = "k"; k.textContent = t.k;
      const v = document.createElement("div"); v.className = "v"; v.textContent = t.v;
      d.append(k, v);
      if (t.d) { const s = document.createElement("div"); s.className = "d"; s.textContent = t.d; d.append(s); }
      return d;
    }));
  }
  const series = (m, c, k) => weeks.map((w) => (D.share.find((r) => r.w === w && r.m === m && r.c === c) || {})[k] ?? null);

  function facts() {
    const f = {};
    f.de = ch("DE"); f.all = ch("All"); f.uk = ch("UK", "Earbuds");
    f.otherEarbuds = avg(["US", "FR", "JP"].map((m) => ch(m, "Earbuds").change_comparable));
    const g = (m, from, to) => avg(D.gap.filter((r) => r.m === m && r.p === "PAIR-E" && r.w >= from && r.w < to).map((r) => r.g));
    f.ukGapBefore = g("UK", "2026-01-01", "2026-06-01"); f.ukGapAfter = g("UK", "2026-06-01", "2099-01-01");
    const coh = (sku, m) => sum(D.cohort.filter((r) => r.sku === sku && r.market === m && r.weeks_since_launch < 12).map((r) => r.units));
    f.launch = MKS.map((m) => ({ m, idx: coh("CV-E400", m) / coh("CV-E300", m) }));
    f.jp = f.launch.find((r) => r.m === "JP").idx; f.restLaunch = avg(f.launch.filter((r) => r.m !== "JP").map((r) => r.idx));
    const ov = D.promo.filter((r) => r.overlaps_event && r.method === "pre8");
    f.ovNaive = sum(ov.map((r) => r.lift_units)); f.ovAttr = sum(ov.map((r) => r.lift_units_attributed));
    f.depth = Object.fromEntries(D.depth.map((r) => [r.depth_band, r]));
    f.scen = sum(D.scenario.map((r) => r.expected_incremental_margin_usd));
    f.breaks = D.breaks;
    return f;
  }

  /* ---------- Executive brief ---------- */
  function brief() {
    const F = facts();
    tiles([
      { k: "Corvane value share, all markets", v: fmt.pct(1)(F.all.share_latest), d: `${pts(F.all.change_reported)} reported, ${pts(F.all.change_comparable)} comparable` },
      { k: "Germany share change", v: pts(F.de.change_reported), d: `${pts(F.de.change_comparable)} on a comparable panel` },
      { k: "Of Germany's gain, real", v: fmt.pct(0)(F.de.share_of_change_surviving), d: "the rest is a retailer joining the panel" },
      { k: "UK earbuds share", v: pts(F.uk.change_comparable), d: `other markets ${pts(F.otherEarbuds)}` },
      { k: "Medium promotions, margin", v: usdK(F.depth["Medium (15-24%)"].incremental_margin_usd), d: "deep: " + usdK(F.depth["Deep (25%+)"].incremental_margin_usd) },
    ]);
    const items = [
      ["serious", "Read with care", `<b>Germany's reported share gain of ${pts(F.de.change_reported)} is mostly the panel, not the market.</b> Elektra Markt joined the panel in April and Corvane is strong there. On the retailers covered in both periods the gain is ${pts(F.de.change_comparable)}: ${fmt.pct(0)(F.de.share_of_change_surviving)} of it survives.`, "share.html", "Market &amp; share"],
      ["critical", "Act", `<b>UK earbuds lost share (${pts(F.uk.change_comparable)}) while other markets gained ${pts(F.otherEarbuds)}.</b> Askel cut Pods 3 by 15% in June: Corvane Buds went from ${fmt.rel(0)(F.ukGapBefore)} to ${fmt.rel(0)(F.ukGapAfter)} dearer. Respond on price or value in the UK, not everywhere.`, "pricing.html", "Price gaps"],
      ["warning", "Act", `<b>Arc Buds sold ${fmt.pct(0)(F.jp)} of Pulse Buds' first 12 weeks in Japan</b>, against ${fmt.pct(0)(F.restLaunch)} elsewhere. Two of four Japanese retailers listed Arc ten weeks late. Fix listing before the next launch, not the product.`, "launch.html", "Launches"],
      ["warning", "Decide", `<b>Medium-depth promotions (15-24%) earned ${usdK(F.depth["Medium (15-24%)"].incremental_margin_usd)} of margin after the dip; deep ones ${usdK(F.depth["Deep (25%+)"].incremental_margin_usd)} and shallow ones ${usdK(F.depth["Shallow (<15%)"].incremental_margin_usd)}.</b> Estimates carry wide intervals: see the ranges before cutting the calendar.`, "promotions.html", "Promotions"],
      ["warning", "Read with care", `<b>Three Black Friday SKU promotions ran inside a store-wide event.</b> Crediting them with everything gives ${fmt.int(F.ovNaive)} extra units; splitting the joint lift by depth gives ${fmt.int(F.ovAttr)}. Do not plan next year's SKU promotions on the naive figure.`, "promotions.html", "Promotions"],
    ];
    if (F.breaks.length) items.push(["good", "Checked", `<b>The weekly panel and the independent monthly series agree within 2% in every cell but one</b> (${esc(F.breaks[0].market)} ${esc(F.breaks[0].category)}, ${esc(F.breaks[0].brand)}, ${mon(F.breaks[0].month_start)}: ${fmt.rel(1)(F.breaks[0].value_diff_pct)}), flagged to the provider.`, "checks.html", "Data checks"]);
    document.getElementById("insights").innerHTML = items.map(([cls, label, text, href, where]) =>
      `<li><span class="status ${cls}"><i aria-hidden="true">${cls === "good" ? "✓" : "!"}</i>${label}</span><span>${text} <a class="where" href="${href}">${where} →</a></span></li>`).join("");
    const ms = ["All"].concat(MKS);
    card("br-change", (el) => bar(el, { horizontal: true, x: ms.map((m) => MK[m]), yFmt: pts, series: [{ name: "Reported", data: ms.map((m) => ch(m).change_reported), color: 0 }, { name: "Comparable panel", data: ms.map((m) => ch(m).change_comparable), color: 1 }] }),
      { cols: [{ key: "market", label: "Market", fmt: (m) => MK[m] }, { key: "share_year_ago", label: "Year ago", fmt: fmt.pct(1) }, { key: "share_latest", label: "Latest", fmt: fmt.pct(1) }, { key: "change_reported", label: "Reported", fmt: pts }, { key: "change_comparable", label: "Comparable", fmt: pts }, { key: "share_of_change_surviving", label: "Survives", fmt: fmt.pct(0) }], rows: D.change.filter((r) => r.category === "All") });
    card("br-share", (el) => line(el, { x: weeks, xFmt: mon, yFmt: fmt.pct(0), endLabels: false, series: [{ name: "Reported", data: series("All", "All", "s"), color: 0 }, { name: "Comparable panel", data: series("All", "All", "sc"), color: 1, dashed: true }] }),
      { cols: [{ key: "w", label: "Week" }, { key: "s", label: "Reported", fmt: fmt.pct(2) }, { key: "sc", label: "Comparable", fmt: fmt.pct(2) }], rows: D.share.filter((r) => r.m === "All" && r.c === "All") });
  }

  /* ---------- Market & share ---------- */
  function share() {
    const m = state.market, c = ch(m);
    const r = D.retailers.filter((x) => (m === "All" || x.market === m) && !x.is_constant_panel);
    document.getElementById("f-scope").textContent = r.length ? `${r.map((x) => x.retailer_name).join(", ")} joined the panel on ${fmt.date(r[0].panel_from)} ${r[0].panel_from.slice(0, 4)}: excluded from the comparable panel` : "Panel unchanged over the period: reported and comparable agree";
    tiles([
      { k: `Value share, ${MK[m]}`, v: fmt.pct(1)(c.share_latest), d: "latest 13 weeks" },
      { k: "Reported change", v: pts(c.change_reported), d: "against a year earlier" },
      { k: "Comparable change", v: pts(c.change_comparable), d: "same retailers both periods" },
      { k: "Market value growth", v: fmt.rel(1)(c.market_value_growth), d: "panel, USD" },
    ]);
    card("sh-line", (el) => line(el, { x: weeks, xFmt: mon, yFmt: fmt.pct(0), endLabels: false, series: [{ name: "Reported", data: series(m, "All", "s"), color: 0 }, { name: "Comparable panel", data: series(m, "All", "sc"), color: 1, dashed: true }] }),
      { cols: [{ key: "w", label: "Week" }, { key: "s", label: "Reported", fmt: fmt.pct(2) }, { key: "sc", label: "Comparable", fmt: fmt.pct(2) }, { key: "mv", label: "Market value USD", fmt: fmt.int }], rows: D.share.filter((x) => x.m === m && x.c === "All") });
    const steps = [{ s: "Year ago", v: c.share_year_ago }, { s: "Panel coverage", v: c.change_from_panel_coverage }, { s: "Comparable change", v: c.change_comparable }, { s: "Latest", v: c.share_latest }];
    card("sh-bridge", (el) => bar(el, { x: steps.map((x) => x.s), yFmt: (v) => (100 * v).toFixed(1), series: [{ name: "Value share, points", data: steps.map((x) => x.v), colors: [1, 0, 1, 1], labels: true }] }),
      { cols: [{ key: "s", label: "Step" }, { key: "v", label: "Points", fmt: (v) => (100 * v).toFixed(2) }], rows: steps });
    const cats = ["Headphones", "Earbuds", "Speakers"];
    card("sh-cat", (el) => bar(el, { horizontal: true, x: cats, yFmt: pts, series: [{ name: "Reported", data: cats.map((k) => ch(m, k).change_reported), color: 0 }, { name: "Comparable panel", data: cats.map((k) => ch(m, k).change_comparable), color: 1 }] }),
      { cols: [{ key: "category", label: "Category" }, { key: "change_reported", label: "Reported", fmt: pts }, { key: "change_comparable", label: "Comparable", fmt: pts }], rows: D.change.filter((x) => x.market === m && x.category !== "All") });
    const rc = D.recon.filter((x) => m === "All" ? false : x.market === m);
    if (m === "All") {
      card("sh-recon", (el) => { el.innerHTML = '<p class="callout">Pick a market: the two series are in local currency.</p>'; }, null);
    } else {
      card("sh-recon", (el) => line(el, { x: rc.map((x) => x.month), xFmt: mon, yFmt: fmt.compact, endLabels: false, series: [{ name: "Monthly provider", data: rc.map((x) => x.monthly), color: 0 }, { name: "Weekly panel, by day", data: rc.map((x) => x.weekly), color: 1, dashed: true }] }),
        { cols: [{ key: "month", label: "Month", fmt: mon }, { key: "monthly", label: "Monthly", fmt: fmt.int }, { key: "weekly", label: "From weekly", fmt: fmt.int }, { key: "diff", label: "Difference", fmt: fmt.rel(2) }, { key: "breaks", label: "Cells outside 2%" }], rows: rc });
    }
  }

  /* ---------- Price gaps ---------- */
  function pricing() {
    const F = facts();
    const gw = uniq(D.gap.map((r) => r.w)).sort();
    const gs = (m, p) => gw.map((w) => (D.gap.find((r) => r.w === w && r.m === m && r.p === p) || {}).g ?? null);
    tiles([
      { k: "UK earbuds gap, Jan to May", v: fmt.rel(0)(F.ukGapBefore), d: "Corvane Buds against Askel Pods 3" },
      { k: "UK earbuds gap since June", v: fmt.rel(0)(F.ukGapAfter), d: "after Askel's 15% cut" },
      { k: "UK earbuds share change", v: pts(F.uk.change_comparable), d: `other markets ${pts(F.otherEarbuds)}` },
    ]);
    card("pg-earbuds", (el) => line(el, { x: gw, xFmt: mon, yFmt: fmt.rel(0), endLabels: false, series: MKS.map((m, i) => ({ name: MK[m], data: gs(m, "PAIR-E"), color: i })) }),
      { cols: [{ key: "w", label: "Week" }, { key: "m", label: "Market" }, { key: "comp", label: "Competitor product" }, { key: "g", label: "Gap", fmt: fmt.rel(1) }], rows: D.gap.filter((r) => r.p === "PAIR-E") });
    const sw = weeks.filter((w) => w >= "2025-06-01");
    const se = (m) => sw.map((w) => (D.share.find((r) => r.w === w && r.m === m && r.c === "Earbuds") || {}).sc ?? null);
    const others = sw.map((w, i) => avg(["US", "FR", "JP"].map((m) => se(m)[i])));
    card("pg-uk", (el) => line(el, { x: sw, xFmt: mon, yFmt: fmt.pct(0), endLabels: false, series: [{ name: "UK", data: se("UK"), color: 0, markArea: { from: "2026-06-01", to: sw[sw.length - 1], label: "Askel price cut" } }, { name: "US, France, Japan (average)", data: others, color: 1 }] }),
      { cols: [{ key: "w", label: "Week" }, { key: "uk", label: "UK", fmt: fmt.pct(1) }, { key: "o", label: "Others", fmt: fmt.pct(1) }], rows: sw.map((w, i) => ({ w, uk: se("UK")[i], o: others[i] })) });
    const l13 = gw.slice(-13);
    const pairs = uniq(D.gap.map((r) => r.p)).sort();
    const pv = (m, p) => avg(D.gap.filter((r) => r.m === m && r.p === p && l13.includes(r.w)).map((r) => r.g));
    card("pg-pairs", (el) => bar(el, { x: MKS.map((m) => MK[m]), yFmt: fmt.rel(0), series: pairs.map((p, i) => ({ name: (D.gap.find((r) => r.p === p) || {}).c, data: MKS.map((m) => pv(m, p)), color: i })) }),
      { cols: [{ key: "m", label: "Market" }, { key: "p", label: "Pair" }, { key: "v", label: "Gap", fmt: fmt.rel(1) }], rows: MKS.flatMap((m) => pairs.map((p) => ({ m, p, v: pv(m, p) }))) });
  }

  /* ---------- Launches ---------- */
  function launch() {
    const F = facts();
    const wk = [...Array(31).keys()];
    const cu = (sku, m) => wk.map((w) => { const r = D.cohort.filter((x) => x.sku === sku && (!m || x.market === m) && x.weeks_since_launch === w); return r.length ? sum(r.map((x) => x.units)) : null; });
    tiles([
      { k: "Arc against Pulse, first 12 weeks", v: fmt.pct(0)(F.restLaunch), d: "average outside Japan" },
      { k: "Japan", v: fmt.pct(0)(F.jp), d: "two retailers listed Arc ten weeks late" },
    ]);
    card("ln-curve", (el) => line(el, { x: wk, xFmt: (w) => "wk " + w, yFmt: fmt.compact, yMin: 0, series: [{ name: "Arc Buds (2026)", data: cu("CV-E400"), color: 0 }, { name: "Pulse Buds (2025)", data: cu("CV-E300"), color: 1, dashed: true }] }),
      { cols: [{ key: "w", label: "Week since launch" }, { key: "a", label: "Arc Buds", fmt: fmt.int }, { key: "p", label: "Pulse Buds", fmt: fmt.int }], rows: wk.map((w, i) => ({ w, a: cu("CV-E400")[i], p: cu("CV-E300")[i] })) });
    card("ln-index", (el) => bar(el, { x: F.launch.map((r) => MK[r.m]), yFmt: fmt.pct(0), series: [{ name: "Arc / Pulse", data: F.launch.map((r) => r.idx), colors: F.launch.map((r) => (r.m === "JP" ? 0 : 1)), labels: true }] }),
      { cols: [{ key: "m", label: "Market", fmt: (m) => MK[m] }, { key: "idx", label: "Arc / Pulse, weeks 0-11", fmt: fmt.pct(1) }], rows: F.launch });
    const jp = wk.map((w) => (D.cohort.find((x) => x.sku === "CV-E400" && x.market === "JP" && x.weeks_since_launch === w) || {}).retailers_selling ?? null);
    card("ln-jp", (el) => bar(el, { x: wk, xFmt: (w) => "wk " + w, yFmt: fmt.int, yMax: 4, series: [{ name: "Retailers selling", data: jp, color: 0 }] }),
      { cols: [{ key: "w", label: "Week since launch" }, { key: "n", label: "Retailers selling" }], rows: wk.map((w, i) => ({ w, n: jp[i] })) });
    card("ln-mkt", (el) => line(el, { x: wk, xFmt: (w) => "wk " + w, yFmt: fmt.compact, yMin: 0, endLabels: false, series: MKS.map((m, i) => ({ name: MK[m], data: cu("CV-E400", m), color: i })) }),
      { cols: [{ key: "market", label: "Market" }, { key: "weeks_since_launch", label: "Week" }, { key: "units", label: "Units", fmt: fmt.int }, { key: "retailers_selling", label: "Retailers" }], rows: D.cohort.filter((r) => r.sku === "CV-E400") });
  }

  /* ---------- Promotions ---------- */
  function promo() {
    const F = facts();
    const P8 = D.promo.filter((r) => r.method === "pre8");
    const el8 = P8.filter((r) => r.is_eligible);
    const bands = D.depth.map((r) => r.depth_band);
    tiles([
      { k: "Promotions evaluated", v: fmt.int(el8.length), d: `of ${P8.length}; ${P8.length - el8.length} overlap an event` },
      { k: "Medium depth, incremental margin", v: usdK(F.depth["Medium (15-24%)"].incremental_margin_usd), d: fmt.int(F.depth["Medium (15-24%)"].promotions) + " promotions" },
      { k: "Deep, incremental margin", v: usdK(F.depth["Deep (25%+)"].incremental_margin_usd), d: "the dip after eats the lift" },
      { k: "Planned promotions, expected", v: usdK(F.scen), d: `${D.scenario.length} in the calendar` },
    ]);
    card("pm-depth", (el) => bar(el, { x: bands, yFmt: fmt.rel(0), series: [{ name: "Average lift", data: D.depth.map((r) => r.avg_lift_pct), color: 0, labels: true }] }),
      { cols: [{ key: "depth_band", label: "Depth" }, { key: "promotions", label: "Promotions" }, { key: "avg_lift_pct", label: "Lift", fmt: fmt.rel(0) }, { key: "p10_lift_pct", label: "p10", fmt: fmt.rel(0) }, { key: "p90_lift_pct", label: "p90", fmt: fmt.rel(0) }, { key: "avg_dip_pct", label: "Dip after", fmt: fmt.rel(0) }, { key: "incremental_margin_usd", label: "Incremental margin", fmt: usdK }], rows: D.depth });
    card("pm-margin", (el) => bar(el, { x: bands, yFmt: usdK, series: [{ name: "Incremental margin", data: D.depth.map((r) => r.incremental_margin_usd), colors: D.depth.map((r) => (r.incremental_margin_usd < 0 ? 0 : 1)), labels: true }] }),
      { cols: [{ key: "depth_band", label: "Depth" }, { key: "incremental_margin_usd", label: "Total", fmt: usdK }, { key: "avg_incremental_margin_usd", label: "Per promotion", fmt: usdK }], rows: D.depth });
    const top = el8.slice().sort((a, b) => b.baseline_units * b.promo_weeks - a.baseline_units * a.promo_weeks).slice(0, 18);
    const rows = top.map((r) => { const b = r.baseline_units * r.promo_weeks; return { name: `${PROD[r.sku]}, ${RET[r.retailer_id]}, ${mon(r.start_week)}, ${Math.round(r.depth * 100)}%`, est: r.lift_units / b, low: (r.lift_units - r.ci_half_width_units) / b, high: (r.lift_units + r.ci_half_width_units) / b, fmt: fmt.rel(0), color: 0 }; });
    card("pm-forest", (el) => forest(el, { rows }),
      { cols: [{ key: "name", label: "Promotion" }, { key: "est", label: "Lift", fmt: fmt.rel(0) }, { key: "low", label: "Low", fmt: fmt.rel(0) }, { key: "high", label: "High", fmt: fmt.rel(0) }], rows });
    const ov = P8.filter((r) => r.overlaps_event);
    card("pm-overlap", (el) => bar(el, { x: ov.map((r) => PROD[r.sku]), yFmt: fmt.int, series: [{ name: "Naive", data: ov.map((r) => r.lift_units), color: 0 }, { name: "Attributed by depth", data: ov.map((r) => r.lift_units_attributed), color: 1 }] }),
      { cols: [{ key: "promo_id", label: "Promotion" }, { key: "sku", label: "SKU", fmt: (s) => PROD[s] }, { key: "lift_units", label: "Naive extra units", fmt: fmt.int }, { key: "lift_units_attributed", label: "Attributed", fmt: fmt.int }, { key: "ci_half_width_units", label: "± (95%)", fmt: fmt.int }], rows: ov });
    const methods = ["pre4", "pre8", "pre13", "ly"], ML = { pre4: "4 weeks before", pre8: "8 weeks before", pre13: "13 weeks before", ly: "Same weeks last year" };
    const common = uniq(D.promo.filter((r) => r.method === "ly" && r.is_eligible).map((r) => r.promo_id));
    const sens = methods.map((m) => ({ m: ML[m], v: avg(D.promo.filter((r) => r.method === m && common.includes(r.promo_id)).map((r) => r.lift_pct)) }));
    card("pm-sens", (el) => bar(el, { x: sens.map((r) => r.m), yFmt: fmt.rel(0), series: [{ name: "Average lift", data: sens.map((r) => r.v), color: 0, labels: true }] }),
      { cols: [{ key: "m", label: "Baseline" }, { key: "v", label: "Average lift", fmt: fmt.rel(1) }], rows: sens });
    const sub = document.querySelector("#pm-sens .sub"); if (sub) sub.textContent = `Average estimated lift on the same ${common.length} promotions (those with a year-earlier baseline), by baseline method`;
    const sc = D.scenario;
    card("pm-scenario", (el) => bar(el, { horizontal: true, x: sc.map((r) => `${PROD[r.sku]}, ${RET[r.retailer_id]}, ${Math.round(r.depth * 100)}%`), yFmt: usdK, series: [{ name: "Low (p10)", data: sc.map((r) => r.low_incremental_margin_usd), color: 1 }, { name: "Expected", data: sc.map((r) => r.expected_incremental_margin_usd), color: 0 }, { name: "High (p90)", data: sc.map((r) => r.high_incremental_margin_usd), color: 2 }] }),
      { cols: [{ key: "promo_id", label: "Plan" }, { key: "product_name", label: "Product" }, { key: "retailer_id", label: "Retailer", fmt: (r) => RET[r] }, { key: "start_week", label: "Starts" }, { key: "depth", label: "Depth", fmt: fmt.pct(0) }, { key: "baseline_units", label: "Baseline / week", fmt: fmt.int }, { key: "expected_incremental_units", label: "Extra units", fmt: fmt.int }, { key: "low_incremental_margin_usd", label: "Low", fmt: usdK }, { key: "expected_incremental_margin_usd", label: "Expected", fmt: usdK }, { key: "high_incremental_margin_usd", label: "High", fmt: usdK }], rows: sc });
  }

  /* ---------- Product portfolio ---------- */
  function portfolio() {
    const P = D.portfolio.filter((r) => r.net_sales_usd != null);
    tiles([
      { k: "Net sales, last 13 weeks", v: usdK(sum(P.map((r) => r.net_sales_usd))), d: "all markets" },
      { k: "Growth", v: fmt.rel(1)(sum(P.map((r) => r.net_sales_usd)) / sum(P.map((r) => r.net_sales_usd_year_ago || 0)) - 1), d: "against a year earlier" },
      { k: "Top product", v: PROD[P[0].sku], d: fmt.pct(0)(P[0].share_of_brand) + " of net sales" },
    ]);
    card("pf-sales", (el) => bar(el, { horizontal: true, x: P.map((r) => PROD[r.sku]), yFmt: usdK, series: [{ name: "Net sales", data: P.map((r) => r.net_sales_usd), color: 0, labels: true }] }), null);
    const G = P.filter((r) => r.growth != null).sort((a, b) => b.growth - a.growth);
    card("pf-growth", (el) => bar(el, { horizontal: true, x: G.map((r) => PROD[r.sku]), yFmt: fmt.rel(0), series: [{ name: "Growth", data: G.map((r) => r.growth), color: 0, labels: true }] }), null);
    const t = document.getElementById("product-table");
    table(t, [{ key: "product_name", label: "Product" }, { key: "category", label: "Category" }, { key: "launch_date", label: "Launched" }, { key: "units", label: "Units", fmt: fmt.int }, { key: "net_sales_usd", label: "Net sales", fmt: usdK }, { key: "asp_usd", label: "ASP", fmt: fmt.usd(0) }, { key: "discount_rate", label: "Discount", fmt: fmt.pct(1) }, { key: "margin_pct", label: "Margin", fmt: fmt.pct(1) }, { key: "growth", label: "Growth", fmt: fmt.rel(1) }, { key: "was_reclassified", label: "Reclassified", fmt: (v) => (v ? "yes" : "") }], D.portfolio);
    t.hidden = false;
  }

  /* ---------- Data checks ---------- */
  function checks() {
    tiles([
      { k: "dbt models and tests", v: D.dbt ? `${D.dbt.passed} / ${D.dbt.nodes}` : "–", d: "passing" },
      { k: "Latest complete week", v: D.as_of, d: "the week after is partial and excluded" },
      { k: "Monthly cells outside 2%", v: String(D.breaks.length), d: "of " + fmt.int((D.checks.find((r) => r.check_name === "Monthly cells checked") || {}).records) },
    ]);
    document.getElementById("checks").innerHTML = `<ul class="insights">${D.checks.filter((r) => r.check_name !== "Monthly cells checked").map((r) => {
      const warn = /missing|outside|differ/.test(r.check_name) && r.records > 0;
      return `<li><span class="status ${warn ? "warning" : "good"}"><i aria-hidden="true">${warn ? "!" : "✓"}</i>${warn ? "Flagged" : "Handled"}</span><span><b>${esc(r.check_name)}:</b> ${fmt.int(r.records)} in <code>${esc(r.source)}</code>, ${esc(r.action)}.</span></li>`;
    }).join("")}</ul>`;
    const months = uniq(D.recon.map((r) => r.month)).sort();
    const cells = [];
    MKS.forEach((m, yi) => months.forEach((mo, xi) => { const r = D.recon.find((x) => x.market === m && x.month === mo); cells.push([xi, yi, r ? r.worst_cell : null]); }));
    card("ck-recon", (el) => heatmap(el, { x: months, y: MKS, cells, min: 0, max: 0.03, fmt: fmt.pct(2), xLabel: mon, yLabel: (v) => MK[v] }),
      { cols: [{ key: "month_start", label: "Month", fmt: mon }, { key: "market", label: "Market" }, { key: "category", label: "Category" }, { key: "brand", label: "Brand" }, { key: "value_diff_pct", label: "Difference", fmt: fmt.rel(2) }], rows: D.breaks });
    const pm = uniq(D.panel_vs_sales.map((r) => r.month_start)).sort();
    card("ck-panel", (el) => line(el, { x: pm, xFmt: mon, yFmt: fmt.rel(1), endLabels: false, series: MKS.map((m, i) => ({ name: MK[m], data: pm.map((mo) => (D.panel_vs_sales.find((r) => r.market === m && r.month_start === mo) || {}).diff_pct ?? null), color: i })) }),
      { cols: [{ key: "month_start", label: "Month", fmt: mon }, { key: "market", label: "Market" }, { key: "panel_units", label: "Panel", fmt: fmt.int }, { key: "own_units", label: "Own sales", fmt: fmt.int }, { key: "diff_pct", label: "Difference", fmt: fmt.rel(2) }, { key: "has_revision", label: "Revised", fmt: (v) => (v ? "yes" : "") }], rows: D.panel_vs_sales });
    const rules = [
      ["Share is a ratio of summed values, never an average of shares", "test_share_is_a_ratio_of_sums_not_an_average_of_shares"],
      ["All-markets share is computed in USD at the weekly average rate", "assert_weekly_fx_policy; test_all_markets_share_uses_usd"],
      ["Comparable panel: retailers covered for the whole period", "dim_retailer.is_constant_panel; rpt_share_change"],
      ["Weeks crossing months are split by day through a date bridge", "int_week_month_bridge; assert_bridge_shares_sum_to_one"],
      ["Incomplete weeks are left out of trends and shares", "test_incomplete_week_is_excluded_from_shares"],
      ["Reclassified products are restated; units are preserved", "assert_restatement_preserves_units"],
      ["The latest panel delivery wins", "stg_panel_weekly; test_panel_revision_and_missing_week_are_detected"],
      ["Rebuilding from the same seed reproduces every mart", "make rebuild (analysis/fingerprint.py)"],
    ];
    document.getElementById("rules").innerHTML = `<ul class="insights">${rules.map(([r, w]) => `<li><span class="status good"><i aria-hidden="true">✓</i>Tested</span><span><b>${esc(r)}.</b> <code>${esc(w)}</code></span></li>`).join("")}</ul>`;
  }

  const PAGES = { brief, share, pricing, launch, promo, portfolio, checks };
  document.addEventListener("DOMContentLoaded", () => {
    const page = document.body.dataset.page;
    if (!window.echarts) { document.querySelector("main").insertAdjacentHTML("afterbegin", '<p class="callout critical">Charts could not load (no network to the chart library). Tables still work.</p>'); }
    if (page === "share") {
      const seg = document.getElementById("f-market");
      seg.addEventListener("click", (e) => {
        const b = e.target.closest("button"); if (!b) return;
        seg.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
        state.market = b.dataset.v; window.Viz.clear(); share();
      });
    }
    PAGES[page]();
  });
})();
