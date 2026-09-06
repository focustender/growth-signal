# .claude/skills/lifecycle-pulse/tests/test_digest_logic.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import digest_logic as dl

CURRENT = {
    "date": "2025-11-11",
    "segments": {
        "homeowner": {"interest": 1800, "sample": 1260, "project": 0, "purchase": 780, "repeat": 85, "advocacy": 210},
        "trade": {"interest": 560, "sample": 355, "project": 210, "purchase": 195, "repeat": 46, "advocacy": 30},
    },
}
PREVIOUS = {
    "date": "2025-11-04",
    "segments": {
        "homeowner": {"interest": 1790, "sample": 1250, "project": 0, "purchase": 770, "repeat": 84, "advocacy": 205},
        "trade": {"interest": 555, "sample": 350, "project": 208, "purchase": 220, "repeat": 46, "advocacy": 30},
    },
}

def test_compute_deltas_basic():
    deltas = dl.compute_deltas(CURRENT, PREVIOUS)
    assert deltas["segments"]["homeowner"]["sample"] == 10
    assert deltas["segments"]["trade"]["purchase"] == -25

def test_compute_deltas_missing_previous_stage_treated_as_zero():
    current = {"date": "2025-11-11", "segments": {"designer": {"interest": 50}}}
    previous = {"date": "2025-11-04", "segments": {"designer": {}}}
    deltas = dl.compute_deltas(current, previous)
    assert deltas["segments"]["designer"]["interest"] == 50

def test_flag_anomalies_detects_significant_drop():
    deltas = dl.compute_deltas(CURRENT, PREVIOUS)
    anomalies = dl.flag_anomalies(deltas, CURRENT, threshold_pp=5.0)
    flagged = {(a["segment"], a["stage"]) for a in anomalies}
    # trade/purchase: 220 -> 195 is a ~11.4% drop, over the 5.0pp threshold
    assert ("trade", "purchase") in flagged

def test_flag_anomalies_ignores_small_changes():
    deltas = dl.compute_deltas(CURRENT, PREVIOUS)
    anomalies = dl.flag_anomalies(deltas, CURRENT, threshold_pp=5.0)
    flagged = {(a["segment"], a["stage"]) for a in anomalies}
    # homeowner/sample: 1250 -> 1260 is a gain, never an anomaly
    assert ("homeowner", "sample") not in flagged

def test_flag_anomalies_zero_over_zero_is_not_anomalous():
    current = {"date": "2025-11-11", "segments": {"homeowner": {"project": 0}}}
    previous = {"date": "2025-11-04", "segments": {"homeowner": {"project": 0}}}
    deltas = dl.compute_deltas(current, previous)
    anomalies = dl.flag_anomalies(deltas, current, threshold_pp=5.0)
    assert anomalies == []

def test_render_digest_markdown_includes_date_and_omits_data_quality_when_none():
    deltas = dl.compute_deltas(CURRENT, PREVIOUS)
    anomalies = dl.flag_anomalies(deltas, CURRENT, threshold_pp=5.0)
    md = dl.render_digest_markdown(CURRENT, deltas, anomalies, data_quality_section=None)
    assert "2025-11-11" in md
    assert "Data quality" not in md

def test_render_digest_markdown_includes_data_quality_when_given():
    deltas = dl.compute_deltas(CURRENT, PREVIOUS)
    anomalies = dl.flag_anomalies(deltas, CURRENT, threshold_pp=5.0)
    md = dl.render_digest_markdown(CURRENT, deltas, anomalies, data_quality_section="3 new mismatches found.")
    assert "## Data quality" in md
    assert "3 new mismatches found." in md
