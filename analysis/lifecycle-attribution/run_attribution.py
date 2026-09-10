"""Runs the generic attribution engine (attribution.py) against Trade
Signal's real email-engagement and funnel-event tables, at several
attribution windows and broken out by segment. Writes results to
output/attribution_report.json for the findings write-up to cite exact
numbers from, rather than restating them by hand."""
import json
import sqlite3
from pathlib import Path

import attribution as at

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "data" / "trade_signal.db"

VALUE_EVENT_TYPES = ("purchase", "repeat_purchase")
WINDOW_DAYS = (None, 30, 90)
SEGMENTS = ("homeowner", "designer", "trade", "commercial")


def _fetch_engagements(conn, segment=None):
    query = """
        SELECT ee.customer_id, ee.campaign_type AS program, ee.sent_date, ee.opened, ee.clicked
        FROM email_engagement ee JOIN customers c ON c.customer_id = ee.customer_id
    """
    params = ()
    if segment:
        query += " WHERE c.segment = ?"
        params = (segment,)
    cur = conn.execute(query, params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _fetch_value_events(conn, segment=None):
    placeholders = ",".join("?" * len(VALUE_EVENT_TYPES))
    query = f"""
        SELECT fe.customer_id, fe.event_date, fe.amount
        FROM funnel_events fe JOIN customers c ON c.customer_id = fe.customer_id
        WHERE fe.event_type IN ({placeholders})
    """
    params = list(VALUE_EVENT_TYPES)
    if segment:
        query += " AND c.segment = ?"
        params.append(segment)
    cur = conn.execute(query, params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _run_for(engagements, value_events):
    platform = at.platform_metrics(engagements)
    by_window = {}
    for window in WINDOW_DAYS:
        commercial = at.commercial_outcomes(engagements, value_events, window_days=window)
        div = at.divergence(platform, commercial)
        key = "no_window" if window is None else f"{window}d"
        by_window[key] = {
            "commercial_outcomes": commercial,
            "divergence": div,
        }
    return {"platform_metrics": platform, "by_window": by_window}


def run() -> dict:
    conn = sqlite3.connect(DB_PATH)

    overall = _run_for(_fetch_engagements(conn), _fetch_value_events(conn))

    by_segment = {}
    for segment in SEGMENTS:
        engagements = _fetch_engagements(conn, segment)
        value_events = _fetch_value_events(conn, segment)
        by_segment[segment] = _run_for(engagements, value_events)

    conn.close()
    return {"overall": overall, "by_segment": by_segment}


if __name__ == "__main__":
    result = run()
    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "attribution_report.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result["overall"]["platform_metrics"], indent=2))
    print(f"\nWrote {out_path}")
