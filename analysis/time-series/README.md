# Time Series Analysis: Trade-Show Stall Rate Trend

## What this is

A trend/anomaly check on the trade-show single-sample stall rate over time, using the vendored `time-series-analysis` Claude Code skill, answering a question the original headline finding (a single 73% average) didn't: is this getting better, worse, or staying flat? Real result: a modest downward drift (74.2% in 2024 → 71.7% through August 2025, weighted), concentrated in the most recent few months, with one statistically-flagged anomaly that's almost certainly small-sample noise rather than a real event. Full write-up: `output/ts_findings.md`.

## What this isn't

Not a claim that anything caused the drift — no intervention targeting this channel existed when this dataset was generated. Not a confident seasonality analysis — see the Caveats/Seasonality section in the findings doc for why 20 monthly points at 4–11 leads each isn't enough to trust a seasonal pattern.

## How it works

1. **`trade_show_stall_monthly.csv`** — built directly from `trade_signal.db`: trade-segment, trade-show-acquired customers who requested exactly one sample, grouped by signup month, with the stall rate (never reaching `project_upload`/`purchase`) per month. The full-period weighted average (73.97%) independently reproduces `docs/measurement-foundation.md`'s published 73% figure.
2. **`run_ts_analysis.py`** — imports the vendored `ts_analyzer.py`'s functions directly and runs them against that series.

**A real bug, worked around, not patched:** `ts_analyzer.py`'s `if __name__ == "__main__":` block unconditionally calls `_demo()`, ignoring `sys.argv` entirely — the script's own `main()` function (which does real `--csv` argument parsing) is unreachable code; running it from the command line with any arguments, including `--help`, silently prints demo output instead. `run_ts_analysis.py` imports `load_csv`, `compute_growth_rates`, `rolling_average`, `detect_trend`, `detect_anomalies`, `summary_stats`, and `format_report` directly, bypassing the broken entry point rather than editing the vendored file.

## Adapting this to your own data

Any CSV with a date column and a numeric metric column works with `ts_analyzer.py`'s functions directly (see `run_ts_analysis.py` for the calling pattern) — nothing in the engine is Fireclay-specific.

## Known limitation

20 monthly points at single-digit-to-low-double-digit volume per month is thin for trend/anomaly detection — every conclusion in the findings doc is stated as directional, and the recommendations section says explicitly how much more data would be needed before trusting a monthly-level read.

## Running it yourself

```bash
cd analysis/time-series
python3 run_ts_analysis.py
```
