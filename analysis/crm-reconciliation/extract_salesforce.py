"""Pulls the seeded Lead records and writes them to
data/salesforce_extract.json in the shape reconcile.py expects."""
import json
from pathlib import Path
from salesforce_client import get_client


def extract() -> list[dict]:
    sf = get_client()
    # A fresh Developer Edition org ships with ~15-20 pre-loaded sample Leads
    # (e.g. "Edna Frank", "Rose Gonzalez"). Filter to only the synthetic data
    # this project seeded, using the same @example.com convention (RFC 2606)
    # already established throughout the rest of the project.
    result = sf.query_all(
        "SELECT Id, Email, Name, Company, Status, CreatedDate FROM Lead "
        "WHERE Email LIKE '%@example.com'"
    )
    return [{k: v for k, v in r.items() if k != "attributes"} for r in result["records"]]


if __name__ == "__main__":
    records = extract()
    out_path = Path(__file__).parent / "data" / "salesforce_extract.json"
    with open(out_path, "w") as f:
        json.dump(records, f, indent=2)
    print(f"Wrote {len(records)} records to {out_path}")
