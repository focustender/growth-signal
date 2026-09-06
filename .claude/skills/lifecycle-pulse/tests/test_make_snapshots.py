# .claude/skills/lifecycle-pulse/tests/test_make_snapshots.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import make_snapshots as ms

DB_PATH = str(Path(__file__).resolve().parents[4] / "data" / "trade_signal.db")

def test_build_snapshot_has_all_segments_and_stages():
    snapshot = ms.build_snapshot(DB_PATH, "2025-11-11")
    assert snapshot["date"] == "2025-11-11"
    for segment in ("homeowner", "designer", "trade", "commercial"):
        for stage in ("interest", "sample", "project", "purchase", "repeat", "advocacy"):
            assert stage in snapshot["segments"][segment]

def test_build_snapshot_counts_grow_with_later_cutoff():
    early = ms.build_snapshot(DB_PATH, "2024-06-01")
    late = ms.build_snapshot(DB_PATH, "2025-11-11")
    # cumulative counts can only stay the same or grow with a later cutoff
    assert late["segments"]["homeowner"]["purchase"] >= early["segments"]["homeowner"]["purchase"]

def test_build_snapshot_project_stage_near_zero_outside_trade_commercial():
    snapshot = ms.build_snapshot(DB_PATH, "2025-11-11")
    # measurement-foundation.md: project_upload is a trade/commercial-only event
    assert snapshot["segments"]["homeowner"]["project"] == 0

def test_three_snapshots_are_seven_days_apart_and_distinct():
    cutoffs = ms.three_weekly_cutoffs(end_date="2025-11-11")
    assert cutoffs == ["2025-10-28", "2025-11-04", "2025-11-11"]
