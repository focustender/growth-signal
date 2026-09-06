"""Live-writes the seed produced by generate_salesforce_seed.py into a real
Salesforce Developer Edition org. Creates Lead records for salesforce_only
and cross_system entries (Leads, not Contacts+Opportunities, to keep the
object model simple and match how a real early-stage trade lead would
first appear in Salesforce)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from salesforce_client import get_client


def ingest(seed_path: str = "../../data/salesforce_seed.json") -> dict:
    with open(Path(__file__).resolve().parent / seed_path) as f:
        seed = json.load(f)

    sf = get_client()
    created_ids = []

    for entry in seed["salesforce_only"]:
        rec = sf.Lead.create({
            "LastName": entry["last_name"] or "Unknown",
            "FirstName": entry.get("first_name", ""),
            "Company": entry["company"] or "Unknown",
            "Email": entry["email"],
            "Status": entry["salesforce_stage"],
        })
        created_ids.append(rec["id"])

    for entry in seed["cross_system"]:
        sf_rec = entry["salesforce_record"]
        rec = sf.Lead.create({
            "LastName": sf_rec["Name"].split()[-1],
            "FirstName": " ".join(sf_rec["Name"].split()[:-1]),
            "Company": sf_rec["Company"],
            "Email": sf_rec["Email"],
            "Status": sf_rec["Status"],
        })
        created_ids.append(rec["id"])

    return {"created_count": len(created_ids), "created_ids": created_ids}


if __name__ == "__main__":
    result = ingest()
    print(f"Created {result['created_count']} Salesforce Lead records.")
