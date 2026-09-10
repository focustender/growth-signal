"""Fills a copy of the vendored retention_matrix.html template with real
first-purchase-cohort retention data, distinguishing a genuinely-observed
0% (the period happened and nobody repeated) from a not-yet-observed
period (the cohort isn't old enough yet) -- the vendored CSV output
doesn't make that distinction, but it matters here: Period 1 is 0% for
every mature cohort, not merely unpopulated. See README.md."""
import json
import sqlite3
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "data" / "trade_signal.db"
AS_OF = pd.Timestamp("2025-11-11")  # last observed purchase/repeat_purchase event
N_PERIODS = 11


def load(segment=None):
    con = sqlite3.connect(DB_PATH)
    q = """
        SELECT fe.customer_id AS user_id, c.segment, fe.event_date AS activity_date
        FROM funnel_events fe JOIN customers c ON c.customer_id = fe.customer_id
        WHERE fe.event_type IN ('purchase','repeat_purchase')
    """
    df = pd.read_sql(q, con, parse_dates=["activity_date"])
    con.close()
    if segment:
        df = df[df.segment == segment]
    first = df.groupby("user_id")["activity_date"].min().rename("cohort_date")
    df = df.merge(first, on="user_id")
    df["m"] = (df.activity_date.dt.year - df.cohort_date.dt.year) * 12 + (
        df.activity_date.dt.month - df.cohort_date.dt.month
    )
    return df


def build_cohorts(df):
    cohorts = []
    df["cohort_month"] = df["cohort_date"].dt.to_period("M")
    for period, g in df.groupby("cohort_month"):
        size = g["user_id"].nunique()
        months_elapsed = (AS_OF.year - period.year) * 12 + (AS_OF.month - period.month)
        rates = []
        for p in range(N_PERIODS):
            if p > months_elapsed:
                rates.append(None)
            elif p == 0:
                rates.append(100.0)
            else:
                n = g[g.m == p]["user_id"].nunique()
                rates.append(round(100 * n / size, 1))
        cohorts.append({"label": str(period), "size": int(size), "rates": rates})
    return cohorts


def render(cohorts, title, retention_event, out_path):
    template = (
        REPO_ROOT / ".claude/skills/cohort-analysis/assets/retention_matrix.html"
    ).read_text()
    data = {
        "title": title,
        "product": "Trade Signal — Fireclay Tile (synthetic)",
        "retentionEvent": retention_event,
        "asOf": str(AS_OF.date()),
        "periods": [f"P{p}" for p in range(N_PERIODS)],
        "cohorts": cohorts,
    }
    old_block_start = template.index("const cohortData = {")
    old_block_end = template.index("};", old_block_start) + 2
    new_block = "const cohortData = " + json.dumps(data, indent=2) + ";"
    filled = template[:old_block_start] + new_block + template[old_block_end:]
    out_path.write_text(filled)


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent / "output"
    df_all = load()
    render(
        build_cohorts(df_all),
        "Repeat-Purchase Retention by First-Purchase Cohort",
        "Made a repeat purchase (month N after first purchase)",
        out_dir / "retention_heatmap.html",
    )
    print(f"Wrote {out_dir / 'retention_heatmap.html'}")
