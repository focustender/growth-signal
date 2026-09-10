# Analysis QA Sign-off

**Analysis title:** Trade Signal — Round 4 (skills library adoption, lifecycle-attribution, data-quality audit, cohort/time-series/root-cause/business-metrics analyses)
**Reviewer:** Ian Castorillo, using the vendored `analysis-qa-checklist` skill
**Author:** Ian Castorillo
**Date reviewed:** 2026-09-06
**Intended audience:** Fireclay Tile hiring manager (Samantha Grow, Lifecycle Growth & Analytics Manager role)
**Delivery format:** `site/case-study.html`, linking to `analysis/*/README.md` and `analysis/*/output/*.md`

---

## Automated QA Results

| Check | Status | Notes |
|---|---|---|
| `qa_runner.py` against `data/customers.csv`, `data/funnel_events.csv`, `data/raw_crm_export.csv` | PASS | 0 FAIL, 0 WARN on all three |
| `qa_runner.py` against `analysis/cohort-analysis/output/retention_matrix_all.csv` | PASS (1 WARN) | Non-standard column names (`Period 0`, `Cohort Size`, etc.) — expected, matches the vendored template's own human-readable header convention; not a real issue |
| `qa_runner.py` against `analysis/time-series/trade_show_stall_monthly.csv`, `analysis/root-cause/trade_show_stall_by_dimension.csv` | PASS | 0 FAIL, 0 WARN on both |
| Full pytest suite (`analysis/`, `.claude/skills/`) | PASS | 39/39, including 4 new tests for `ecommerce_metrics.py` |
| Fresh-venv install check | PASS | `pip install -r requirements.txt` into a genuinely new venv, all scripts import cleanly (verifies the `scipy`/`pandas` gap is actually fixed, not just working by local accident) |

---

## Manual Checklist Summary

| Section | Status | Issues found |
|---|---|---|
| 1. Question framing | PASS | — |
| 2. Data sourcing | PASS | — |
| 3. Transformations & calculations | PASS | — |
| 4. Statistical validity | PASS (with caveats) | See Issues #2, #3 below — both already documented in their respective findings docs, not newly discovered here |
| 5. Findings & conclusions | PASS | — |
| 6. Presentation | PASS | See Issue #1 |

---

## Issues Found

| # | Severity | Description | Resolution | Status |
|---|---|---|---|---|
| 1 | MINOR | The whole page (pre-existing, not introduced this round) shows mojibake (`â€"`) for em-dashes and smart quotes when served via `python3 -m http.server` without an explicit charset header | Confirmed pre-existing, not something this round's edits caused or worsened; out of scope for this round's changes | Deferred — a `<meta charset="utf-8">` tag or server config fix, not a content issue |
| 2 | SHOULD FIX (already addressed at authoring time) | Several new analyses (root-cause, time-series) work with small per-cell sample sizes (n as low as 2–11) | Every affected finding is explicitly labeled directional/noisy in its own findings doc rather than stated with false confidence — see each analysis's "Known Limitations" section | Accepted, with caveats stated in the deliverable itself |
| 3 | SHOULD FIX (already addressed at authoring time) | The attribution and business-metrics findings report correlational patterns (engaged-vs-unengaged value gaps, conversion-rate-vs-revenue mismatches) that could be misread as causal | Explicit selection-effect / non-causal caveats included in both findings docs | Accepted, with caveats stated in the deliverable itself |
| 4 | MUST FIX | None identified | — | N/A |

**Cross-checks performed (strengthens confidence beyond the checklist items above):**
- `analysis/data-quality-audit/`'s independent base-ID duplicate re-derivation exactly reproduces the already-published "669→600, 68 merged" figure.
- `analysis/time-series/`'s full-period weighted stall rate (73.97%) exactly matches the already-published 73% headline stat.
- `analysis/cohort-analysis/`'s independently-computed "ever repeat-purchase" counts by segment (83/80/45/13) exactly match `docs/measurement-foundation.md`'s originally-published "Repeat buyers" column.

Three independent numbers, computed by three different methods across two different rounds of work, all agree with what was already published — the strongest form of the "trustworthy reporting" claim this round is meant to demonstrate.

---

## Delivery Decision

- [x] **Approved for delivery** — all must-fix items resolved (none identified)

**Caveat statement for delivery:**
> All customer data is synthetic; every specific percentage and dollar figure in this round is a property of the generated dataset, not a real Fireclay statistic (see `site/case-study.html`'s existing footer disclaimer, unchanged by this round). Small-sample findings (root-cause, time-series) are explicitly labeled directional in their own write-ups, not stated with false precision.

**Reviewer:** Ian Castorillo
**Date:** 2026-09-06
