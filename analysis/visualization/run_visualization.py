"""Uses the vendored chart_builder.py's recommendation logic and spec
builder against this project's own real findings. Not run via
chart_builder.py's own CLI: its `if __name__ == "__main__"` block
unconditionally runs a demo, the same dead-CLI-entry-point bug as
ts_analyzer.py and drilldown_analyzer.py (see analysis/time-series and
analysis/root-cause READMEs). Worked around by importing
recommend_chart/build_spec directly."""
import json
import sys
from pathlib import Path

SKILL_SCRIPTS = Path(__file__).resolve().parents[2] / ".claude/skills/visualization-builder/scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

import chart_builder as cb  # noqa: E402

SPECS = []

# 1. Segment comparison: conversion rate vs revenue-per-customer
# (analysis/business-metrics) -- 4 categories, comparison type.
rec = cb.recommend_chart("comparison", categories=4)
SPECS.append({
    "source": "analysis/business-metrics/output/metrics_report.json",
    "recommendation": rec,
    "conversion_rate_spec": cb.build_spec(
        "bar",
        labels=["designer", "homeowner", "trade", "commercial"],
        values=[60.7, 43.4, 34.2, 34.1],
        title="Conversion Rate by Segment",
        x_label="Segment", y_label="% of customers who ever purchased",
    ),
    "revenue_per_customer_spec": cb.build_spec(
        "bar",
        labels=["designer", "homeowner", "trade", "commercial"],
        values=[791, 526, 5782, 5391],
        title="Revenue per Customer by Segment",
        x_label="Segment", y_label="$ revenue per customer",
    ),
})

# 2. Time series: trade-show stall rate trend (analysis/time-series)
rec_ts = cb.recommend_chart("time-series", categories=20)
SPECS.append({
    "source": "analysis/time-series/trade_show_stall_monthly.csv",
    "recommendation": rec_ts,
    "spec": "See analysis/time-series/output/ts_report.txt for the full 20-point series -- "
            "a 20-point monthly line is impractical to inline here; the recommendation "
            "(line chart, no pie/bar) is the load-bearing output of this step.",
})

# 3. Cohort retention: already built as a heatmap directly from the
# vendored assets/retention_matrix.html template (see
# analysis/cohort-analysis/build_heatmap.py) -- chart_builder.py has no
# heatmap chart type, so this one intentionally used a different vendored
# asset instead of forcing a bar/line chart onto a matrix.

if __name__ == "__main__":
    out_path = Path(__file__).resolve().parent / "output" / "chart_specs.json"
    out_path.write_text(json.dumps(SPECS, indent=2))
    print(json.dumps(SPECS, indent=2))
    print(f"\nWrote {out_path}")
