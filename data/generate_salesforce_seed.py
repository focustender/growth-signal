"""Derives a deterministic 3-way HubSpot/Salesforce data split from the
project's real, already-live data: `hubspot_contacts_import.csv` (188
trade/commercial contacts genuinely imported into HubSpot) and
`trade_signal.db`'s `customers` table (the full trade/commercial pool).

Why the split works this way (see docs/superpowers/plans/2026-09-06-crm-
reconciliation.md, Task 2's Design note): cross-system "duplicate" records
must actually exist live in both systems, or the real reconciliation run in
Task 5 will never find them -- a record only in a local JSON file is
invisible to a live extract. HubSpot's own MCP write surface is deliberately
restricted, and re-importing more contacts isn't worth the friction anyway,
so the 188 trade/commercial contacts already live in HubSpot are reused
as-is for both `hubspot_only` and `cross_system`. Only Salesforce gets new
writes (Task 3): `cross_system` entries get a new Salesforce Lead that
intentionally drifts from its already-live HubSpot counterpart, and
`salesforce_only` entries are fabricated identities for trade/commercial
customers with no HubSpot presence at all, written only to Salesforce.

Five independent `random.Random(42)` instances are used, one per
responsibility (shuffle/split the 188 HubSpot rows, sample 300 salesforce-
only customers, fabricate salesforce-only names, assign salesforce-only
stages, and choose a drift function per cross-system row). Each gets its
own instance -- never the bare `random` module, never a shared instance --
so the streams cannot interfere with each other and each step's output is
reproducible independent of the others.
"""
import csv
import json
import random
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from generate_hubspot_import import FIRST_NAMES, LAST_NAMES  # noqa: E402

DATA_DIR = Path(__file__).parent
DEFAULT_DB_PATH = str(DATA_DIR / "trade_signal.db")
DEFAULT_HUBSPOT_CSV_PATH = str(DATA_DIR / "hubspot_contacts_import.csv")

SALESFORCE_STAGES = ["Open - Not Contacted", "Working - Contacted", "Closed - Converted"]

CROSS_SYSTEM_COUNT = 85
HUBSPOT_ONLY_COUNT = 103
SALESFORCE_ONLY_COUNT = 300


def _load_hubspot_trade_commercial_rows(hubspot_csv_path: str) -> list:
    with open(hubspot_csv_path) as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if r["Trade Signal Segment"] in ("trade", "commercial")]


def _load_customer_pool(db_path: str, exclude_customer_ids: set) -> list:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "SELECT customer_id, segment, source_channel, signup_date, region, company_name "
            "FROM customers WHERE segment IN ('trade', 'commercial')"
        )
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()
    return [r for r in rows if r["customer_id"] not in exclude_customer_ids]


def _drift_name_case(name: str) -> str:
    # e.g. "Jon Smith" -> "jon smith" (typo/casing drift)
    return name.lower()


def _drift_company_suffix(company: str) -> str:
    if not company:
        return company
    if company.endswith((" Inc", " LLC")):
        # strip the suffix
        return company.rsplit(" ", 1)[0]
    # add a suffix
    return f"{company} Inc"


def _shift_date(date_str: str, rng: random.Random) -> str:
    from datetime import datetime, timedelta
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return date_str
    delta_days = rng.randint(1, 5) * rng.choice([-1, 1])
    return (dt + timedelta(days=delta_days)).strftime("%Y-%m-%d")


def _build_drifted_salesforce_record(hs_row: dict, drift_rng: random.Random, date_rng: random.Random) -> dict:
    first_name = hs_row["First Name"]
    last_name = hs_row["Last Name"]
    name = f"{first_name} {last_name}"
    company = hs_row["Company Name"]
    phone = "555-0100"  # present by default; the "omit phone" drift removes it
    created_date = hs_row["Trade Signal Signup Date"]  # unshifted unless drift picks it

    drift_choices = ["name_case", "company_suffix", "omit_phone", "shift_date"]
    drift = drift_rng.choice(drift_choices)

    if drift == "name_case":
        name = _drift_name_case(name)
    elif drift == "company_suffix":
        company = _drift_company_suffix(company)
    elif drift == "omit_phone":
        phone = None
    elif drift == "shift_date":
        created_date = _shift_date(created_date, date_rng)

    record = {
        "Email": hs_row["Email"],
        "Name": name,
        "Company": company,
        # Live-verified during planning: every sampled trade/commercial
        # HubSpot contact's lifecyclestage still reads "lead" (the 750-
        # contact import never touched HubSpot's standard lifecyclestage
        # field). Setting every cross-system Salesforce Lead to
        # "Closed - Converted" reproduces that real, guaranteed mismatch
        # ("lead" vs. "customer" canonical stages) without per-row logic.
        # This is intentional and must not vary per entry.
        "Status": "Closed - Converted",
        "CreatedDate": created_date,
    }
    if phone is not None:
        record["Phone"] = phone
    return record


def generate_salesforce_seed(db_path: str = DEFAULT_DB_PATH,
                              hubspot_csv_path: str = DEFAULT_HUBSPOT_CSV_PATH,
                              seed: int = 42) -> dict:
    # Step 1: shuffle+split the 188 real HubSpot trade/commercial rows.
    hubspot_rows = _load_hubspot_trade_commercial_rows(hubspot_csv_path)
    split_rng = random.Random(seed)
    shuffled = list(hubspot_rows)
    split_rng.shuffle(shuffled)
    cross_system_hubspot_rows = shuffled[:CROSS_SYSTEM_COUNT]
    hubspot_only_rows = shuffled[CROSS_SYSTEM_COUNT:CROSS_SYSTEM_COUNT + HUBSPOT_ONLY_COUNT]

    hubspot_only = [
        {
            "customer_id": r["Trade Signal Customer ID"],
            "email": r["Email"],
            "first_name": r["First Name"],
            "last_name": r["Last Name"],
        }
        for r in hubspot_only_rows
    ]

    # Step 2: sample 300 salesforce-only customers from customers.db, using
    # a second, independently-seeded instance so it cannot interact with
    # the shuffle above.
    exclude_ids = {r["Trade Signal Customer ID"] for r in hubspot_rows}
    customer_pool = _load_customer_pool(db_path, exclude_ids)
    sample_rng = random.Random(seed)
    salesforce_only_pool = sample_rng.sample(customer_pool, SALESFORCE_ONLY_COUNT)

    # Step 3: fabricate identity (third instance) and stage (fourth instance)
    # for the 300 salesforce-only customers.
    name_rng = random.Random(seed)
    stage_rng = random.Random(seed)
    salesforce_only = []
    for c in salesforce_only_pool:
        first = name_rng.choice(FIRST_NAMES)
        last = name_rng.choice(LAST_NAMES)
        email = f"{first}.{last}.{c['customer_id'].lower()}@example.com"
        salesforce_only.append({
            "customer_id": c["customer_id"],
            "first_name": first,
            "last_name": last,
            "company": c["company_name"],
            "email": email,
            "segment": c["segment"],
            "salesforce_stage": stage_rng.choice(SALESFORCE_STAGES),
        })

    # Step 4: build drifted Salesforce records for the 85 cross-system rows
    # (fifth instance choosing the drift function; a dedicated date-shift
    # instance keeps the "shift date" behavior reproducible independent of
    # drift-function selection order).
    drift_rng = random.Random(seed)
    date_rng = random.Random(seed)
    cross_system = []
    for r in cross_system_hubspot_rows:
        salesforce_record = _build_drifted_salesforce_record(r, drift_rng, date_rng)
        cross_system.append({
            "customer_id": r["Trade Signal Customer ID"],
            "hubspot_record": dict(r),
            "salesforce_record": salesforce_record,
        })

    return {
        "salesforce_only": salesforce_only,
        "hubspot_only": hubspot_only,
        "cross_system": cross_system,
    }


if __name__ == "__main__":
    seed_data = generate_salesforce_seed()
    out_path = DATA_DIR / "salesforce_seed.json"
    with open(out_path, "w") as f:
        json.dump(seed_data, f, indent=2)
    print(
        f"Wrote seed to {out_path}: "
        f"{len(seed_data['salesforce_only'])} salesforce_only, "
        f"{len(seed_data['hubspot_only'])} hubspot_only, "
        f"{len(seed_data['cross_system'])} cross_system"
    )
