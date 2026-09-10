# Cohort Analysis: Repeat-Purchase Retention

**Analyst:** Ian Castorillo, using the vendored `cohort-analysis` Claude Code skill
**Date:** 2026-09-06
**Cohort definition:** Customers grouped by the calendar month of their *first* `purchase` or `repeat_purchase` funnel event (23 monthly cohorts, 2024-01 through 2025-11)
**Retention event:** A second (or later) `purchase`/`repeat_purchase` event, N months after the first
**Granularity:** Monthly
**Base population:** 1,433 customers with at least one purchase event

## A note on cohort definition — and a real dead end this analysis avoided

The first attempt at this analysis anchored cohorts on **signup date**, matching the pattern in every vendored template. That produced nonsensical retention rates above 100% (some cells over 1,000%): because tile is a considered purchase, almost no customer's *first* purchase happens in their signup month, so "period 0" (customers who bought in their signup month) was a tiny, unrepresentative base that later months' larger purchaser counts trivially exceeded. Re-anchoring cohorts on each customer's **first purchase month** instead — a standard, more appropriate framing for repeat-purchase analysis specifically — fixed this and is what the numbers below reflect. See `run_cohort_analysis.py`'s docstring and the Known Limitations section below.

---

## Summary

**Only 15.4% of first-time purchasers (221 of 1,433) ever make a second purchase within the ~22-month observation window** — and the timing of that repeat purchase has a hard floor: **zero repeat purchases happen in the first month after a customer's initial purchase, in every one of the 20 cohorts old enough to observe it.** Repeat-purchase behavior only starts appearing at month 2 and continues at a low, roughly flat rate through month 10.

| Metric | Value |
|---|---|
| Cohorts analyzed | 23 monthly cohorts, 2024-01 to 2025-11 |
| Total first-time purchasers in scope | 1,433 |
| Customers who ever repeat-purchase | 221 (15.4%) |
| Repeat-purchase rate at month 1 (P1) | **0.0%**, every mature cohort |
| Repeat-purchase rate at month 2 (P2) | ~2.0% of that cohort's first-time purchasers |
| Repeat-purchase rate, months 3–9 | 1.3%–2.5% per month, gradually tapering |

## Retention Matrix

Full interactive heatmap: `output/retention_heatmap.html` (a filled copy of the vendored `assets/retention_matrix.html` template). CSV: `output/retention_matrix_all.csv`. The heatmap makes the month-1 dead zone visually obvious — the entire P1 column reads 0.0% down every row.

| Cohort | Size | P0 | P1 | P2 | P3 | P6 | P9 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2024-01 | 8 | 100% | 0.0% | 0.0% | 0.0% | 0.0% | 12.5% |
| 2024-06 | 62 | 100% | 0.0% | 8.1% | 1.6% | 0.0% | 1.6% |
| 2024-12 | 81 | 100% | 0.0% | 1.2% | 2.5% | 2.5% | 0.0% |
| 2025-01 | 71 | 100% | 0.0% | 0.0% | 1.4% | 8.5% | — |

(Full 23-row table in the CSV/HTML; small early cohorts like 2024-01 (n=8) produce noisy single-customer swings — e.g. that 12.5% at P9 is exactly 1 person.)

## Key Findings

### Finding 1: A real month-1 floor, not a data gap
- **What:** 0 of 221 total repeat-purchase events, across every cohort with at least one month of observed history, happen exactly one calendar month after the first purchase. Repeat purchases begin appearing at month 2.
- **Why (hypothesis):** Fireclay's own funnel already frames tile as a considered purchase (interest → sample → project → purchase). A repeat purchase plausibly requires a *new* project to materialize — sourcing more tile for a second room, a follow-on phase — and that planning cycle apparently doesn't complete within 30 days of the first purchase, even for customers who do eventually reorder.
- **Recommended action:** Any post-purchase "reorder" or cross-sell email timed at 30 days is targeting a window with zero historical repeat-purchase demand. A month-2-or-later send would at least be timed against when the behavior actually starts.

### Finding 2: Repeat-purchase propensity is a segmentation story, not a uniform rate
- **What:** Ever-repeat rate by segment: **trade 23.6%**, **designer 19.9%**, **commercial 18.1%**, **homeowner 10.8%** — trade and designer customers repeat-purchase at roughly double the homeowner rate.
- **Why (hypothesis):** Trade and design professionals plausibly run multiple client projects over time, each needing its own tile order; a homeowner's renovation is more often a single, complete-and-done purchase.
- **Recommended action:** If a repeat-purchase or reorder nurture program gets built, prioritize the trade and designer segments first — that's where the underlying behavior already exists at a meaningfully higher base rate, not a behavior being asked to appear from nothing.

### Finding 3: Overall repeat-purchase rate is low in absolute terms, and that's a real ceiling on this lever
- **What:** 84.6% of first-time purchasers never repeat-purchase at all within the observation window.
- **Why (hypothesis):** Consistent with the "considered purchase, not a subscription" framing already established elsewhere in this project (see the experimentation section's trade-show findings) — most tile purchases may simply be one-project, one-time events for most customers.
- **Recommended action:** Treat repeat-purchase rate as a real but secondary lever next to acquisition and first-purchase-conversion work, not the primary growth mechanism — the ceiling here (15.4% even among people who already bought once) is structurally low.

## Segment Breakdown

| Segment | First-time purchasers | Ever repeat-purchase | Rate |
|---|---:|---:|---:|
| Trade | 191 | 45 | 23.6% |
| Designer | 402 | 80 | 19.9% |
| Commercial | 72 | 13 | 18.1% |
| Homeowner | 768 | 83 | 10.8% |

Per-segment retention matrices: `output/retention_matrix_{homeowner,designer,trade,commercial}.csv`.

## Cross-check against the original published funnel table

`docs/measurement-foundation.md`'s funnel-by-segment table independently published "repeat buyer" counts per segment before this analysis existed: homeowner 83, designer 80, trade 45, commercial 13. This analysis's "ever repeat-purchase" counts (see Segment Breakdown above) match exactly — a second, independent confirmation (alongside the 669→600 CRM-export cross-check in `analysis/data-quality-audit/`) that this project's headline numbers hold up under a different computation method, not just the one that originally produced them.

## Known Limitations

- **Cohort sizes for individual monthly cells are small** (many cohorts have 1–3 repeat-purchasers in a given period), so any single cell's percentage is noisy — the month-1-is-always-zero finding is robust *because* it holds across all 20 mature cohorts and 221 total repeat events, not because any one cohort's number is precise.
- **Right-censoring:** cohorts from 2025 haven't had time to reach later periods yet (e.g. the 2025-11 cohort has only observed P0). `output/retention_heatmap.html` marks these cells "—" rather than 0%, distinguishing "not yet observed" from "observed and zero" — the vendored `retention_matrix.py`'s own CSV output cannot make this distinction (its pivot step silently produces the same blank/NaN for both cases), which is why `build_heatmap.py` computes cell values directly against an explicit "months elapsed since cohort start" check rather than trusting the vendored script's matrix output as-is. Documented here rather than patched into the vendored file.
- **A second upstream bug, worked around, not patched:** `cohort_builder.py`'s `FREQ_MAP` maps `"monthly"` to `"MS"`, which the installed pandas version (3.0.5) rejects for `Series.dt.to_period()` ("please use 'M' instead of 'MS'"). Patched in `run_cohort_analysis.py` by overriding `cohort_builder.FREQ_MAP["monthly"]` after import, not by editing the vendored file — see that script's comment.
- This is synthetic data; the specific percentages are properties of the generated dataset, not real Fireclay statistics, per the root README's labeling convention.

## Recommended Next Steps

1. If a reorder/cross-sell email program is built, start it no earlier than month 2 post-purchase, and prioritize trade/designer segments in initial targeting.
2. Revisit this analysis once a live dataset accumulates enough 12+-month-old cohorts to see whether repeat-purchase rate keeps climbing past month 10 or plateaus (this dataset's cohorts are all under 23 months old).
3. Pair with the reactivation-flow work already in this project (`docs/reactivation-flow.md`) — repeat-purchase and reactivation are adjacent lifecycle stages and a combined view may reveal a single underlying "return to the site" behavior worth measuring directly.
