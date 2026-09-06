"""Checks whether the experimentation backlog's Hypothesis 1 (trade-show
second-sample nudge) can actually be tested as originally specified,
given real historical channel volume. Writes results to
output/feasibility_report.json for the findings/decision write-ups to
cite exact numbers from, rather than restating them by hand."""
import json
import sqlite3
from pathlib import Path

import power_analysis as pa

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "data" / "trade_signal.db"

BASELINE_SECOND_SAMPLE_RATE = 0.11  # trade-show trade leads, per measurement-foundation.md
SCALE_THRESHOLD_PP = 0.08
ITERATE_THRESHOLD_PP = 0.03


def get_trade_show_monthly_rate(conn) -> float:
    cur = conn.execute(
        "SELECT COUNT(*), (julianday(MAX(signup_date)) - julianday(MIN(signup_date))) / 30.44 "
        "FROM customers WHERE segment='trade' AND source_channel='trade_show'"
    )
    count, months_span = cur.fetchone()
    return count / months_span


def get_sample_followup_click_rate(conn) -> float:
    cur = conn.execute(
        """
        SELECT SUM(ee.clicked), COUNT(*)
        FROM email_engagement ee JOIN customers c ON c.customer_id = ee.customer_id
        WHERE c.segment='trade' AND ee.campaign_type='sample_followup'
        """
    )
    clicked, sent = cur.fetchone()
    return clicked / sent


def run() -> dict:
    conn = sqlite3.connect(DB_PATH)
    monthly_rate = get_trade_show_monthly_rate(conn)
    click_rate = get_sample_followup_click_rate(conn)
    conn.close()

    scale_n_per_arm = pa.sample_size_two_prop(
        BASELINE_SECOND_SAMPLE_RATE, BASELINE_SECOND_SAMPLE_RATE + SCALE_THRESHOLD_PP
    )
    iterate_n_per_arm = pa.sample_size_two_prop(
        BASELINE_SECOND_SAMPLE_RATE, BASELINE_SECOND_SAMPLE_RATE + ITERATE_THRESHOLD_PP
    )

    windows = {}
    for months in (3, 6, 12, 18, 24):
        total, per_arm = pa.project_volume(monthly_rate, months)
        mde = pa.mde_two_prop(per_arm, BASELINE_SECOND_SAMPLE_RATE)
        # Same volume, tested against the higher-baseline click-through metric instead,
        # to check whether switching metrics (not population) solves the problem.
        mde_click_metric = pa.mde_two_prop(per_arm, click_rate)
        windows[months] = {
            "total_leads": round(total, 1),
            "per_arm": round(per_arm, 1),
            "mde_second_sample_pp": round(mde * 100, 1),
            "mde_click_metric_pp": round(mde_click_metric * 100, 1),
        }

    result = {
        "baseline_second_sample_rate": BASELINE_SECOND_SAMPLE_RATE,
        "baseline_click_rate_sample_followup": round(click_rate, 4),
        "trade_show_monthly_rate": round(monthly_rate, 2),
        "scale_threshold_pp": SCALE_THRESHOLD_PP * 100,
        "iterate_threshold_pp": ITERATE_THRESHOLD_PP * 100,
        "scale_threshold_n_per_arm": round(scale_n_per_arm),
        "scale_threshold_n_total": round(scale_n_per_arm * 2),
        "iterate_threshold_n_per_arm": round(iterate_n_per_arm),
        "iterate_threshold_n_total": round(iterate_n_per_arm * 2),
        "months_to_reach_scale_threshold": round((scale_n_per_arm * 2) / monthly_rate, 1),
        "windows": windows,
    }
    return result


if __name__ == "__main__":
    result = run()
    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "feasibility_report.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))
    print(f"\nWrote {out_path}")
