# Root Cause Investigation: What's Behind the 2024→2025 Stall-Rate Drift

**Metric affected:** Trade-show single-sample stall rate (never advances to `project_upload`/`purchase`)
**Movement:** Weighted stall rate down from 74.2% (2024) to 71.7% (2025 through August) — see `analysis/time-series/output/ts_findings.md`
**Detection date:** 2026-09-06 (this analysis)
**Investigation owner:** Ian Castorillo, using the vendored `root-cause-investigation` Claude Code skill
**Status:** Inconclusive — and that's the real, reportable finding (see below)

---

## Signal confirmation

- **Confirmed real:** Yes — independently reproduced in `analysis/time-series/` via a different aggregation method.
- **Data sources checked:** `data/trade_signal.db` (`customers`, `funnel_events`), filtered to trade-segment, trade-show-acquired, single-sample leads (n=115).
- **Magnitude:** –2.5 percentage points, 2024 (n=62) vs 2025-through-August (n=53).
- **Onset date:** Gradual, not a step change — see the time-series findings for the month-by-month view.

---

## Scope of impact — what could and couldn't be tested

| Dimension | Testable with this data? | Result |
|---|---|---|
| Region (collapsed to US Census region) | Yes | No consistent direction — see Hypotheses |
| SKU collection family | Yes | No consistent direction — see Hypotheses |
| Sales rep assignment | **No** | No rep/salesperson field exists anywhere in `customers`, `funnel_events`, or any other table |
| Sample inventory availability at request time | **No** | No historical stock-level field exists; only current-state inventory is modeled (and only for the Shopify store, not this SQLite dataset) |

The rep and inventory gaps aren't analysis failures — they're real, systems-requirements-shaped findings in their own right: if this were a live investigation, `customer_id` → assigned rep and a point-in-time stock snapshot are the two fields most worth adding before a rep- or inventory-driven hypothesis could ever be tested here, the same category of recommendation as the CRM reconciliation section's systems-requirements memo.

---

## Hypotheses

| # | Hypothesis | Evidence for | Evidence against | Verdict |
|---|---|---|---|---|
| 1 | The improvement is concentrated in one SKU collection family | The vendored drill-down tool's raw count comparison flags Original Ceramic as the "top driver" (16→9 stalled leads, +87.5% of the total count change) | Checked at the **rate** level, not just raw count: Original Ceramic's stall rate did fall (88.9%→64.3%, n=18→14), but Natural Press's rate *rose* (56.2%→69.2%) and Thin Brick's rate also *rose* (64.3%→81.8%) over the same window. A real driver should move consistently in one direction; this doesn't. | **Refuted** |
| 2 | The improvement is concentrated in one region | — | West declined (86.7%→66.7%) but Northeast *worsened* (60.0%→83.3%) and South declined only slightly (69.2%→60.0%); Midwest was flat. Same mixed-direction pattern as collections. | **Refuted** |
| 3 | Rep assignment or inventory availability explains the shift | — | Not testable — no such fields exist in this dataset (see Scope of impact above) | **Inconclusive — untestable, not disproven** |
| 4 | The improvement is a diffuse, population-level drift rather than a specific segment recovering | Every tested dimension shows small, inconsistent-direction movement rather than one segment moving sharply while others hold steady | — | **Most consistent with the evidence** |

---

## Root cause

**Confirmed cause:** None identified at the region or SKU-collection-family level — see hypothesis 4.

**Explanation:** A generic drill-down comparing raw stalled-lead counts between 2024 and 2025 initially points to one SKU collection family (Original Ceramic) as the "top driver," simply because it happens to have the largest absolute count change. Re-checking that same comparison as a **rate** — stalled ÷ leads in that segment, not just the raw count — shows the picture doesn't hold up: two other collection families' stall rates moved in the *opposite* direction over the same period, and the regional breakdown shows the same inconsistent pattern. At cell sizes of 11–18 leads per segment per period, this is most consistent with ordinary sampling noise spread across segments rather than one segment recovering and pulling the aggregate down with it. The two confounds that would most plausibly explain a real, segment-agnostic improvement — a rep getting better at the second-sample conversation, or an inventory fix removing friction — can't be tested at all with the fields this dataset captures.

**Impact quantification:**
- Affected leads: all 115 single-sample trade-show trade leads in the observation window, not a specific subgroup
- Revenue impact: not separately quantified here — see `analysis/experimentation/decision_memo.md` for the existing recommendation on this channel (full rollout, directional monitoring), which this finding doesn't change
- Duration: ongoing, 2024-01 through the end of the observed window (2025-08)

---

## Resolution

**Corrective action:** None indicated — there's no single lever to pull, which is itself the actionable conclusion: don't attribute the recent improvement to a specific fix, campaign, or region, because the data doesn't support one.
**Owner:** N/A
**Target resolution date:** N/A
**Status:** Closed as inconclusive, with two concrete systems-requirements gaps identified for any future rep- or inventory-driven investigation of this metric.

## Preventive measures

| Measure | Owner | Target date |
|---|---|---|
| Add a rep/salesperson ID field to lead records before attempting a rep-driven root-cause analysis on this metric | Sales Ops / Technology | Before next investigation of this kind |
| Capture point-in-time sample-kit inventory snapshots (not just current stock) before attempting an inventory-driven hypothesis | Technology | Before next investigation of this kind |
| When a drill-down tool reports a "top driver" by raw count, re-check it as a rate before trusting the claim — this investigation's own false start | Analyst | Standing practice, not a one-time fix |
