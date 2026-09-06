"""
Builds a HubSpot-import-ready CSV: a 750-row stratified sample of the same
customers already analyzed in customers.csv / trade_signal.db, so the
records HubSpot ends up holding are literally the same customers, not a
disconnected fake set.

Names and emails are fabricated for realism, but every email uses the
@example.com domain -- reserved under RFC 2606 for documentation/testing,
guaranteed to never reach a real inbox. This is going into a real, live
HubSpot account, so nothing in it should be capable of accidentally
emailing an actual person.

HubSpot's own Import UI is used to actually load this file (Contacts ->
Import) -- there is no generic create-contact tool exposed through the
connector, by HubSpot's own design.
"""

import csv
import random
from pathlib import Path

random.seed(7)
OUT_DIR = Path(__file__).parent

TARGET_TOTAL = 750
TARGET_BY_SEGMENT = {
    "homeowner": 412,
    "designer": 150,
    "trade": 135,
    "commercial": 53,
}

FIRST_NAMES = [
    "Maria", "James", "Linda", "Robert", "Patricia", "John", "Jennifer", "Michael",
    "Elizabeth", "David", "Susan", "Richard", "Jessica", "Joseph", "Sarah", "Thomas",
    "Karen", "Charles", "Nancy", "Daniel", "Lisa", "Matthew", "Betty", "Anthony",
    "Sandra", "Mark", "Ashley", "Paul", "Kimberly", "Steven", "Emily", "Andrew",
    "Donna", "Kenneth", "Michelle", "Priya", "Wei", "Fatima", "Diego", "Aisha",
    "Hiroshi", "Elena", "Carlos", "Yuki", "Amara",
]
LAST_NAMES = [
    "Garcia", "Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
    "Allen", "King", "Wright", "Nguyen", "Patel", "Kim", "Chen", "Okafor", "Haddad",
]

with open(OUT_DIR / "customers.csv") as f:
    all_customers = list(csv.DictReader(f))

by_segment = {}
for c in all_customers:
    by_segment.setdefault(c["segment"], []).append(c)

sampled = []
for segment, target_n in TARGET_BY_SEGMENT.items():
    pool = by_segment.get(segment, [])
    n = min(target_n, len(pool))
    sampled.extend(random.sample(pool, n))

random.shuffle(sampled)

rows = []
for c in sampled:
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    email = f"{c['customer_id'].lower()}@example.com"
    rows.append({
        "Email": email,
        "First Name": first,
        "Last Name": last,
        "Company Name": c["company_name"] or "",
        "Trade Signal Segment": c["segment"],
        "Trade Signal Source Channel": c["source_channel"],
        "Trade Signal Signup Date": c["signup_date"],
        "Trade Signal Region": c["region"] or "unknown",
        "Trade Signal Customer ID": c["customer_id"],
    })

out_path = OUT_DIR / "hubspot_contacts_import.csv"
with open(out_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

print(f"Wrote {len(rows)} rows to {out_path}")
for seg, target_n in TARGET_BY_SEGMENT.items():
    actual = sum(1 for r in rows if r["Trade Signal Segment"] == seg)
    print(f"  {seg}: {actual} (target {target_n})")
