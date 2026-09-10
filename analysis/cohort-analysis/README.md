# Cohort Analysis: Repeat-Purchase Retention

## What this is

A retention-cohort analysis using the vendored `cohort-analysis` Claude Code skill (see `.claude/skills/README.md`), run against this project's real purchase/repeat-purchase data. Real result: **only 15.4% of first-time purchasers ever repeat-purchase, and zero of them do it within their first month** — a hard timing floor, consistent across all 20 cohorts old enough to observe it, plus a clear segmentation gap (trade customers repeat-purchase at more than 2x the homeowner rate). Full write-up: `output/cohort_findings.md`.

## What this isn't

Not a signup-based retention analysis — see the "note on cohort definition" in the findings doc for why that framing produced nonsensical (&gt;100%) numbers here and was abandoned in favor of first-purchase-anchored cohorts, a real methodology correction made mid-analysis rather than a starting assumption.

## How it works

1. **`cohort_input_*.csv`** — extracted from `trade_signal.db`: each customer's first `purchase`/`repeat_purchase` event date as `cohort_date`, every such event (including the first) as an `activity_date` row. One file overall, one per segment.
2. **`run_cohort_analysis.py`** — Fireclay-shaped wiring (same role as `run_attribution.py`/`run_feasibility_check.py` play for their sibling engines) that imports the vendored `cohort_builder.build_cohort_table` and `retention_matrix.compute_retention_matrix` directly and runs them overall and per segment.
3. **`build_heatmap.py`** — fills a copy of the vendored `assets/retention_matrix.html` template with real data, computing each cell directly against elapsed time since cohort start so a genuine 0% is never confused with "not yet observed" (a distinction the vendored CSV pipeline can't make — see Known Limitations in the findings doc).

**Two necessary workarounds, neither touching the vendored files:**
- `.claude/skills/cohort-analysis/scripts/retention_matrix.py` crashes on any invocation under Python 3.14 (the same argparse `%`-in-help-string bug documented in `analysis/data-quality-audit/README.md`) — its `compute_retention_matrix` function is imported directly instead.
- `cohort_builder.py`'s `FREQ_MAP["monthly"]` value (`"MS"`) is rejected by the installed pandas version's `Series.dt.to_period()`. `run_cohort_analysis.py` patches the imported module's `FREQ_MAP` dict at runtime rather than editing the vendored file.
- `cohort_visualizer.py`'s matplotlib/seaborn dependency isn't installed (and isn't part of this skill library's stated pandas/numpy/stdlib-only convention) — used the vendored HTML template asset directly instead of installing extra plotting dependencies for one chart.

## Adapting this to your own data

Point the extraction query at any table with a customer ID, a "first qualifying event" date, and repeat-event dates — `cohort_builder.py` and `retention_matrix.py` have no Fireclay-specific assumptions once fed the right columns (`user_id`, `cohort_date`, `activity_date`).

## Known limitation

Small per-cell cohort sizes make individual matrix cells noisy (see the findings doc); the headline month-1 finding is trustworthy because it holds across all 20 mature cohorts and 221 total repeat events, not because of any single cell's precision.

## Running it yourself

```bash
cd analysis/cohort-analysis
python3 run_cohort_analysis.py
python3 build_heatmap.py
```
