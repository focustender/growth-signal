# Root Cause Investigation: Trade-Show Stall Rate Drift

## What this is

A structured hypothesis rule-out for the modest 2024→2025 improvement in the trade-show stall rate (found in `analysis/time-series/`), using the vendored `root-cause-investigation` Claude Code skill. Real result: **the improvement doesn't hold up as concentrated in any single region or SKU collection family** — a naive count-based "top driver" claim from the drill-down tool (Original Ceramic) fails a rate-based recheck, since other collections' rates moved in the opposite direction over the same window. Full write-up: `output/rca_findings.md`.

## What this isn't

Not a confirmed root cause — the honest conclusion here is "inconclusive, and here's exactly what would need to exist in the data to test the two hypotheses (rep assignment, inventory availability) that can't be tested today." A structured process that ends in "no smoking gun, here's why" is still a real result, not a failed analysis.

## How it works

1. **`trade_show_stall_by_dimension.csv`** — the same single-sample trade-show trade population as the time-series analysis, with region collapsed to US Census regions and SKU collection collapsed to family (both to keep per-cell counts large enough to say anything at all — the raw 20-state, 12-collection breakdown would have cells as small as 1–2).
2. **`run_rca.py`** — imports the vendored `drilldown_analyzer.py`'s `drill_down`/`format_report` functions directly and compares 2024 vs 2025 by both dimensions.
3. The write-up **deliberately doesn't stop at the tool's own "TOP DRIVER" output** — it re-checks that claim as a rate (stalled ÷ leads in that segment, not just the raw count difference) before accepting or rejecting it, which is what actually overturns the naive result. See `output/rca_findings.md`'s Hypotheses table.

**A real bug, worked around, not patched:** `drilldown_analyzer.py`'s `if __name__ == "__main__":` block unconditionally calls `_demo()`, ignoring `sys.argv` — the same dead-CLI-entry-point bug as `ts_analyzer.py` (documented in `analysis/time-series/README.md`). Worked around the same way: `drill_down` and `format_report` are imported and called directly.

## Adapting this to your own data

`drill_down()` takes two lists of plain dicts (one per period), a metric column, and one or more dimension columns — no Fireclay-specific assumptions. Its raw-count "contribution" output is genuinely useful for spotting where to look, but per this investigation's own finding, always re-check a flagged "top driver" against the rate/denominator before trusting it, especially with a rate-style metric.

## Known limitation

Two of the most plausible confounds for this specific metric — sales rep assignment and sample-inventory availability at request time — cannot be tested with this dataset's schema at all. See the findings doc's "Scope of impact" table.

## Running it yourself

```bash
cd analysis/root-cause
python3 run_rca.py
```
