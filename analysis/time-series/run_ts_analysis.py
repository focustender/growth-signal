"""Runs the vendored ts_analyzer.py functions against the real monthly
trade-show single-sample stall-rate series. Not run via ts_analyzer.py's
own CLI: its `if __name__ == "__main__"` block unconditionally calls
_demo(), ignoring sys.argv entirely, so `main()` (the real --csv path)
is dead code and can never run from the command line as shipped. Worked
around here by importing the underlying functions directly -- see
README.md."""
import sys
from pathlib import Path

SKILL_SCRIPTS = Path(__file__).resolve().parents[2] / ".claude/skills/time-series-analysis/scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

import ts_analyzer as ts  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_CSV = Path(__file__).resolve().parent / "trade_show_stall_monthly.csv"


def run():
    rows = ts.load_csv(str(INPUT_CSV), date_col="month", metric_col="stall_pct")
    rows = ts.compute_growth_rates(rows, period=1)
    rows = ts.rolling_average(rows, window=3)
    values = [r["value"] for r in rows]
    trend = ts.detect_trend(values)
    anomalies = ts.detect_anomalies(rows, z_threshold=2.0)
    stats = ts.summary_stats(values)
    report = ts.format_report(rows, trend, anomalies, stats, "trade_show_stall_pct", "monthly")
    return report, trend, anomalies, stats


if __name__ == "__main__":
    report, trend, anomalies, stats = run()
    out_path = Path(__file__).resolve().parent / "output" / "ts_report.txt"
    out_path.write_text(report)
    print(report)
    print(f"\nWrote {out_path}")
