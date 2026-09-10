"""Runs the vendored drilldown_analyzer.py functions against the real
trade-show single-sample stall data, comparing 2024 vs 2025 by region
(collapsed to US Census regions) and SKU collection family. Not run via
drilldown_analyzer.py's own CLI: its `if __name__ == "__main__"` block
unconditionally calls _demo(), the same dead-CLI bug documented in
analysis/time-series/README.md. Worked around by importing the
underlying functions directly."""
import csv
import sys
from pathlib import Path

SKILL_SCRIPTS = Path(__file__).resolve().parents[2] / ".claude/skills/root-cause-investigation/scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

import drilldown_analyzer as rca  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_CSV = Path(__file__).resolve().parent / "trade_show_stall_by_dimension.csv"


def run():
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    rows_a = [r for r in rows if r["period"] == "2024"]
    rows_b = [r for r in rows if r["period"] == "2025"]

    breakdown = rca.drill_down(rows_a, rows_b, ["region_bucket", "collection_family"], "stalled")
    report = rca.format_report(breakdown, "stalled_lead_count", "2024", "2025")
    return report, breakdown


if __name__ == "__main__":
    report, breakdown = run()
    out_path = Path(__file__).resolve().parent / "output" / "rca_report.txt"
    out_path.write_text(report)
    print(report)
    print(f"\nWrote {out_path}")
