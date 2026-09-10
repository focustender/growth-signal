"""Runs the vendored cohort-analysis engines (cohort_builder.py,
retention_matrix.py) against real purchase/repeat-purchase events,
overall and broken out by segment. Works around two real upstream bugs
in the vendored scripts rather than editing them -- see
analysis/cohort-analysis/README.md."""
import sys
from pathlib import Path

import pandas as pd

SKILL_SCRIPTS = Path(__file__).resolve().parents[2] / ".claude/skills/cohort-analysis/scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

import cohort_builder  # noqa: E402
import retention_matrix  # noqa: E402

# Upstream bug: FREQ_MAP maps "monthly" -> "MS", but pandas 2.2+/3.x's
# Series.dt.to_period() rejects "MS" ("for Period, please use 'M' instead
# of 'MS'"). Patched here, in our own code, not in the vendored file.
cohort_builder.FREQ_MAP["monthly"] = "M"

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent / "output"
SEGMENTS = ("homeowner", "designer", "trade", "commercial")


def run_one(input_csv: Path, label: str):
    df = pd.read_csv(input_csv)
    cohort_table = cohort_builder.build_cohort_table(df, granularity="monthly")
    cohort_table.to_csv(OUT_DIR / f"cohort_table_{label}.csv", index=False)

    # retention_matrix.compute_retention_matrix expects cohort_period as
    # datetime and the columns cohort_builder produces -- matches directly.
    matrix = retention_matrix.compute_retention_matrix(cohort_table, fmt="pct")
    matrix.to_csv(OUT_DIR / f"retention_matrix_{label}.csv")

    n_cohorts = cohort_table["cohort_period"].nunique()
    n_users = cohort_table["user_id"].nunique()
    return {"label": label, "n_cohorts": n_cohorts, "n_users_with_a_purchase_event": n_users}


if __name__ == "__main__":
    OUT_DIR.mkdir(exist_ok=True)
    summary = [run_one(Path(__file__).resolve().parent / "cohort_input_all.csv", "all")]
    for seg in SEGMENTS:
        summary.append(
            run_one(Path(__file__).resolve().parent / f"cohort_input_{seg}.csv", seg)
        )
    for row in summary:
        print(row)
