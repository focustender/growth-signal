import csv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "data"))
import generate_salesforce_seed as gss

DB_PATH = str(Path(__file__).resolve().parents[3] / "data" / "trade_signal.db")
HUBSPOT_CSV_PATH = str(Path(__file__).resolve().parents[3] / "data" / "hubspot_contacts_import.csv")

def test_seed_only_includes_trade_and_commercial():
    seed = gss.generate_salesforce_seed(DB_PATH, HUBSPOT_CSV_PATH, seed=42)
    # salesforce_only draws from customers.db, which does carry a segment column
    all_segments = {entry["segment"] for entry in seed["salesforce_only"]}
    assert all_segments <= {"trade", "commercial"}

def test_seed_counts_match_design():
    seed = gss.generate_salesforce_seed(DB_PATH, HUBSPOT_CSV_PATH, seed=42)
    assert len(seed["salesforce_only"]) == 300
    assert len(seed["hubspot_only"]) == 103
    assert len(seed["cross_system"]) == 85

def test_seed_is_deterministic():
    seed_a = gss.generate_salesforce_seed(DB_PATH, HUBSPOT_CSV_PATH, seed=42)
    seed_b = gss.generate_salesforce_seed(DB_PATH, HUBSPOT_CSV_PATH, seed=42)
    assert seed_a == seed_b

def test_hubspot_only_entries_are_real_hubspot_rows():
    seed = gss.generate_salesforce_seed(DB_PATH, HUBSPOT_CSV_PATH, seed=42)
    with open(HUBSPOT_CSV_PATH) as f:
        real_emails = {row["Email"] for row in csv.DictReader(f)}
    for entry in seed["hubspot_only"]:
        assert entry["email"] in real_emails

def test_cross_system_entries_have_injected_drift():
    seed = gss.generate_salesforce_seed(DB_PATH, HUBSPOT_CSV_PATH, seed=42)
    assert len(seed["cross_system"]) > 0
    entry = seed["cross_system"][0]
    assert "hubspot_record" in entry and "salesforce_record" in entry
    assert entry["salesforce_record"]["Status"] == "Closed - Converted"
    # every cross-system entry's Salesforce Name should trace back to its
    # real HubSpot row's name, but at least one entry must actually differ
    # (drift was injected, not just copied through)
    drifted = [e for e in seed["cross_system"]
               if e["salesforce_record"]["Name"] !=
                  f"{e['hubspot_record']['First Name']} {e['hubspot_record']['Last Name']}"]
    assert len(drifted) > 0
