# analysis/crm-reconciliation/tests/test_reconcile.py
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import reconcile as rc

FIXTURES = Path(__file__).parent / "fixtures"

def load_config():
    import yaml
    with open(Path(__file__).resolve().parents[1] / "config.example.yaml") as f:
        return yaml.safe_load(f)

def load_fixtures():
    with open(FIXTURES / "hubspot_sample.json") as f:
        hs = json.load(f)
    with open(FIXTURES / "salesforce_sample.json") as f:
        sf = json.load(f)
    return hs, sf

def test_normalize_hubspot_concatenates_full_name():
    config = load_config()
    hs, _ = load_fixtures()
    normalized = rc.normalize_record(hs[0], config["hubspot"], "hubspot")
    assert normalized["full_name"] == "Jon Smith"
    assert normalized["email"] == "jon.smith@example.com"
    assert normalized["source_system"] == "hubspot"

def test_exact_email_match_found():
    config = load_config()
    hs, sf = load_fixtures()
    result = rc.reconcile(hs, sf, config)
    matched_ids = {(m["hubspot_id"], m["salesforce_id"]) for m in result["matched"]}
    assert ("hs-1", "sf-1") in matched_ids

def test_exact_email_match_flags_stage_mismatch():
    config = load_config()
    hs, sf = load_fixtures()
    result = rc.reconcile(hs, sf, config)
    mismatch = next(m for m in result["stage_mismatches"] if m["hubspot_id"] == "hs-1")
    assert mismatch["hubspot_canonical_stage"] == "opportunity"
    assert mismatch["salesforce_canonical_stage"] == "customer"

def test_hubspot_only_orphan_detected():
    config = load_config()
    hs, sf = load_fixtures()
    result = rc.reconcile(hs, sf, config)
    orphan_ids = {o["id"] for o in result["hubspot_only"]}
    assert "hs-2" in orphan_ids

def test_salesforce_only_orphan_detected():
    config = load_config()
    hs, sf = load_fixtures()
    result = rc.reconcile(hs, sf, config)
    orphan_ids = {o["id"] for o in result["salesforce_only"]}
    assert "sf-2" in orphan_ids

def test_fuzzy_match_without_email():
    config = load_config()
    hs, sf = load_fixtures()
    result = rc.reconcile(hs, sf, config)
    matched_ids = {(m["hubspot_id"], m["salesforce_id"]) for m in result["matched"]}
    assert ("hs-3", "sf-3") in matched_ids
    fuzzy = next(m for m in result["matched"] if m["hubspot_id"] == "hs-3")
    assert fuzzy["match_method"] == "fuzzy"

def test_summary_counts_are_consistent():
    config = load_config()
    hs, sf = load_fixtures()
    result = rc.reconcile(hs, sf, config)
    s = result["summary"]
    assert s["matched_count"] == len(result["matched"])
    assert s["hubspot_only_count"] == len(result["hubspot_only"])
    assert s["salesforce_only_count"] == len(result["salesforce_only"])
    assert s["stage_mismatch_count"] == len(result["stage_mismatches"])
