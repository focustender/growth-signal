# Visualization: Chart Specs + a Real Chart

## What this is

Chart-type recommendations and JSON specs from the vendored `visualization-builder` skill, applied to this project's real findings, plus one fully-rendered chart built from those specs: `output/segment_metrics_chart.html`, putting the business-metrics section's "conversion rate vs. revenue per customer" finding side by side so the contrast is immediately visible rather than left as two numbers in a table.

## What this isn't

Not a matplotlib render — the vendored `chart_builder.py`'s `--plot` path falls back to matplotlib (not installed, and not part of this skill library's stated pandas/numpy/stdlib convention). `output/segment_metrics_chart.html` is a small hand-built inline-SVG chart instead, drawn directly to scale from the real numbers in `analysis/business-metrics/output/metrics_report.json`, styled to match the case study's own visual language (same color tokens, same fonts) so it reads as part of one deliverable rather than a bolted-on export.

## How it works

1. **`run_visualization.py`** — imports the vendored `chart_builder.py`'s `recommend_chart`/`build_spec` functions directly (its CLI has the same dead-`__main__`-block bug as `ts_analyzer.py`/`drilldown_analyzer.py` — see those READMEs) and generates chart-type recommendations + JSON specs for the business-metrics comparison and the time-series trend, written to `output/chart_specs.json`.
2. **`output/segment_metrics_chart.html`** — the one chart actually rendered, built by hand from those specs' data since no plotting library was available or desired.

## Why the cohort heatmap isn't here

`analysis/cohort-analysis/output/retention_heatmap.html` is a real chart too, but it was built directly from the `cohort-analysis` skill's own `assets/retention_matrix.html` template (a purpose-built cohort heatmap), not from this generic `chart_builder.py` (which has no heatmap chart type at all — its `CHART_RULES` cover time-series, comparison, part-to-whole, distribution, correlation, and flow, but not a matrix/heatmap shape). Using the right vendored asset for the right chart shape, rather than forcing every visual through one script, is the same judgment call as `analysis/business-metrics/`'s decision not to force AOV into a SaaS metrics template.

## Running it yourself

```bash
cd analysis/visualization
python3 run_visualization.py
```
