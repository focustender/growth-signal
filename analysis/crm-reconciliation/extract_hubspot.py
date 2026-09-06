"""Pulls trade + commercial HubSpot contacts and writes them to
data/hubspot_extract.json in the shape reconcile.py expects."""
import json
from pathlib import Path
from hubspot_client import search_contacts

PROPERTIES = ["email", "firstname", "lastname", "company",
              "lifecyclestage", "trade_signal_signup_date"]


def extract() -> list[dict]:
    records = []
    for segment in ("trade", "commercial"):
        records.extend(search_contacts(segment, PROPERTIES))
    return records


if __name__ == "__main__":
    records = extract()
    out_path = Path(__file__).parent / "data" / "hubspot_extract.json"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(records, f, indent=2)
    print(f"Wrote {len(records)} records to {out_path}")
