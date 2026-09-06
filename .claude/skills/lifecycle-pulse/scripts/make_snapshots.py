"""Builds a lifecycle funnel snapshot as of a given cutoff date by
querying trade_signal.db directly. Also provides three_weekly_cutoffs,
used to generate backdated demonstration snapshots without waiting
real weeks."""
import sqlite3
from datetime import date, timedelta

STAGE_EVENT_TYPES = {
    "interest": ("site_visit", "visualizer_use"),
    "sample": ("sample_request",),
    "project": ("project_upload",),
    "purchase": ("purchase",),
    "repeat": ("repeat_purchase",),
}
SEGMENTS = ("homeowner", "designer", "trade", "commercial")


def build_snapshot(db_path: str, cutoff_date: str) -> dict:
    conn = sqlite3.connect(db_path)
    segments = {}
    for segment in SEGMENTS:
        stages = {}
        for stage, event_types in STAGE_EVENT_TYPES.items():
            placeholders = ",".join("?" for _ in event_types)
            query = f"""
                SELECT COUNT(DISTINCT fe.customer_id)
                FROM funnel_events fe
                JOIN customers c ON c.customer_id = fe.customer_id
                WHERE c.segment = ? AND fe.event_type IN ({placeholders})
                  AND fe.event_date <= ?
            """
            cur = conn.execute(query, (segment, *event_types, cutoff_date))
            stages[stage] = cur.fetchone()[0]
        cur = conn.execute("""
            SELECT COUNT(DISTINCT r.customer_id)
            FROM reviews r
            JOIN customers c ON c.customer_id = r.customer_id
            WHERE c.segment = ? AND r.date <= ?
        """, (segment, cutoff_date))
        stages["advocacy"] = cur.fetchone()[0]
        segments[segment] = stages
    conn.close()
    return {"date": cutoff_date, "segments": segments}


def three_weekly_cutoffs(end_date: str) -> list:
    end = date.fromisoformat(end_date)
    return [(end - timedelta(days=14)).isoformat(),
            (end - timedelta(days=7)).isoformat(),
            end.isoformat()]


if __name__ == "__main__":
    import json
    from pathlib import Path
    db_path = str(Path(__file__).resolve().parents[4] / "data" / "trade_signal.db")
    out_dir = Path(__file__).resolve().parents[1] / "snapshots"
    out_dir.mkdir(exist_ok=True)
    for cutoff in three_weekly_cutoffs("2025-11-11"):
        snapshot = build_snapshot(db_path, cutoff)
        with open(out_dir / f"{cutoff}.json", "w") as f:
            json.dump(snapshot, f, indent=2)
        print(f"Wrote {cutoff}.json — {snapshot}")
