"""
Synthetic Fireclay Tile customer-lifecycle dataset generator.

Builds a realistic (but entirely fictional) trade/homeowner/designer/commercial
funnel dataset for the "Trade Signal" project. Deliberately encodes a friction
pattern in the trade segment (single-sample requesters who don't return) and a
visualizer-drop-off pattern, so downstream analysis discovers real signal
rather than a pre-baked conclusion.

Also emits a deliberately messy "raw_crm_export.csv" (inconsistent casing,
duplicate-ish rows, missing fields, mixed date formats) to demonstrate
reconciling imperfect data, separate from the clean analysis-ready tables.

No third-party dependencies -- stdlib only.
"""

import csv
import random
import sqlite3
import uuid
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

OUT_DIR = Path(__file__).parent
DB_PATH = OUT_DIR / "trade_signal.db"

WINDOW_START = date(2024, 1, 1)
WINDOW_END = date(2025, 8, 31)
N_CUSTOMERS = 3200

SEGMENTS = ["homeowner", "designer", "trade", "commercial"]
SEGMENT_WEIGHTS = [0.55, 0.20, 0.18, 0.07]

CHANNELS = [
    "organic_search", "paid_social", "referral", "showroom_walkin",
    "trade_show", "architect_referral", "direct", "email_capture",
]
CHANNEL_WEIGHTS_BY_SEGMENT = {
    "homeowner": [0.30, 0.22, 0.12, 0.10, 0.02, 0.02, 0.12, 0.10],
    "designer": [0.22, 0.10, 0.18, 0.08, 0.06, 0.20, 0.10, 0.06],
    "trade": [0.12, 0.04, 0.14, 0.06, 0.34, 0.16, 0.10, 0.04],
    "commercial": [0.10, 0.02, 0.10, 0.04, 0.30, 0.30, 0.12, 0.02],
}

REGIONS = [
    "CA", "WA", "OR", "NY", "IL", "MN", "TX", "CO", "MA", "GA",
    "AZ", "NC", "FL", "PA", "OH", "MI", "VA", "NJ", "MD", "CT",
]

COLLECTIONS = [
    "Original Ceramic - Aegean", "Original Ceramic - Sage", "Original Ceramic - Clamshell",
    "Natural Press - Oatmeal", "Natural Press - Sable", "Natural Press - Fog",
    "Glass - Seaglass", "Glass - Midnight", "Glass - Champagne",
    "Thin Brick - Weathered White", "Thin Brick - Charcoal", "Thin Brick - Terracotta",
]

COMPANY_SUFFIXES = ["Design Studio", "Architecture Group", "Build Co.", "Interiors",
                    "Construction", "Design + Build", "Studio", "& Associates"]

EMAIL_CAMPAIGNS = [
    "welcome", "sample_followup", "project_nurture",
    "post_purchase", "reactivation", "trade_engagement",
]


def rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(delta, 0)))


def weighted_choice(options, weights):
    return random.choices(options, weights=weights, k=1)[0]


def make_customer(i: int) -> dict:
    segment = weighted_choice(SEGMENTS, SEGMENT_WEIGHTS)
    channel = weighted_choice(CHANNELS, CHANNEL_WEIGHTS_BY_SEGMENT[segment])
    signup = rand_date(WINDOW_START, WINDOW_END)
    region = random.choice(REGIONS)
    # ~4% of records missing region -- realistic CRM gap
    if random.random() < 0.04:
        region = ""
    company = None
    if segment in ("trade", "commercial"):
        company = f"{random.choice(['Harbor', 'Northline', 'Cascade', 'Meridian', 'Bramble', 'Ashford', 'Coastal', 'Union'])} {random.choice(COMPANY_SUFFIXES)}"
    return {
        "customer_id": f"CUST-{i:05d}",
        "segment": segment,
        "source_channel": channel,
        "signup_date": signup.isoformat(),
        "region": region,
        "company_name": company or "",
        "email_opt_in": 1 if random.random() < 0.86 else 0,
    }


def simulate_funnel(customer: dict, events: list, emails: list, reviews: list):
    cid = customer["customer_id"]
    segment = customer["segment"]
    channel = customer["source_channel"]
    signup = date.fromisoformat(customer["signup_date"])

    def add_event(event_type, d, sku=None, amount=None):
        events.append({
            "event_id": str(uuid.uuid4())[:8],
            "customer_id": cid,
            "event_type": event_type,
            "event_date": d.isoformat(),
            "sku_collection": sku or "",
            "channel": channel,
            "amount": amount if amount is not None else "",
        })

    def add_email(campaign, d, opened, clicked):
        emails.append({
            "engagement_id": str(uuid.uuid4())[:8],
            "customer_id": cid,
            "campaign_type": campaign,
            "sent_date": d.isoformat(),
            "opened": 1 if opened else 0,
            "clicked": 1 if clicked else 0,
        })

    add_event("site_visit", signup)
    add_email("welcome", signup + timedelta(days=1), opened=random.random() < 0.52, clicked=random.random() < 0.14)

    # --- Visualizer usage ---
    visualizer_prob = {"homeowner": 0.34, "designer": 0.40, "trade": 0.26, "commercial": 0.14}[segment]
    used_visualizer = random.random() < visualizer_prob
    visualizer_date = None
    if used_visualizer:
        visualizer_date = signup + timedelta(days=random.randint(0, 10))
        add_event("visualizer_use", visualizer_date, sku=random.choice(COLLECTIONS))

    # --- Sample request (first) ---
    base_sample_prob = {"homeowner": 0.62, "designer": 0.70, "trade": 0.58, "commercial": 0.40}[segment]
    sample_prob = base_sample_prob
    if used_visualizer:
        sample_prob = min(0.95, sample_prob + 0.22)
    requested_sample = random.random() < sample_prob

    sample_date = None
    if requested_sample:
        if used_visualizer:
            lag = random.randint(1, 14)
        else:
            lag = random.randint(0, 21)
        sample_date = signup + timedelta(days=lag)
        add_event("sample_request", sample_date, sku=random.choice(COLLECTIONS))
        add_email("sample_followup", sample_date + timedelta(days=3),
                   opened=random.random() < 0.44, clicked=random.random() < 0.11)
    elif used_visualizer:
        # visualizer used, no sample requested within a reasonable window -- the friction signal
        pass

    # --- Second / kit sample request ---
    # Trade segment acquired via trade_show is deliberately less likely to come back for more
    # samples or advance -- this is the encoded friction pattern for the Trade Portal redesign.
    second_sample_prob = {"homeowner": 0.30, "designer": 0.46, "trade": 0.22, "commercial": 0.20}[segment]
    if segment == "trade" and channel == "trade_show":
        second_sample_prob = 0.11
    requested_second = requested_sample and random.random() < second_sample_prob
    if requested_second:
        d2 = sample_date + timedelta(days=random.randint(5, 30))
        add_event("sample_request", d2, sku=random.choice(COLLECTIONS))

    # --- Trade/commercial project pipeline ---
    project_uploaded = False
    if segment in ("trade", "commercial") and requested_sample:
        project_prob = 0.34 if not requested_second else 0.62
        if channel == "trade_show" and not requested_second:
            project_prob *= 0.5
        project_uploaded = random.random() < project_prob
        if project_uploaded:
            add_event("project_upload", sample_date + timedelta(days=random.randint(10, 40)))
            add_email("project_nurture", sample_date + timedelta(days=random.randint(12, 42)),
                       opened=random.random() < 0.38, clicked=random.random() < 0.09)

    # --- Purchase ---
    purchase_prob = {"homeowner": 0.18, "designer": 0.28, "trade": 0.20, "commercial": 0.16}[segment]
    if requested_sample:
        purchase_prob += 0.30
    if requested_second:
        purchase_prob += 0.20
    if project_uploaded:
        purchase_prob += 0.25
    if segment == "trade" and requested_sample and not requested_second and not project_uploaded:
        purchase_prob *= 0.35  # the core friction: single-sample trade leads rarely convert
    purchase_prob = min(purchase_prob, 0.92)

    purchased = random.random() < purchase_prob
    purchase_date = None
    if purchased:
        base_date = sample_date if requested_sample else signup
        purchase_date = base_date + timedelta(days=random.randint(7, 60))
        amount = round(random.uniform(400, 1800), 2) if segment in ("homeowner", "designer") else round(random.uniform(2200, 26000), 2)
        add_event("purchase", purchase_date, sku=random.choice(COLLECTIONS), amount=amount)
        add_email("post_purchase", purchase_date + timedelta(days=5),
                   opened=random.random() < 0.58, clicked=random.random() < 0.16)

        # repeat purchase
        repeat_prob = {"homeowner": 0.16, "designer": 0.30, "trade": 0.38, "commercial": 0.34}[segment]
        if random.random() < repeat_prob:
            rd = purchase_date + timedelta(days=random.randint(60, 300))
            if rd <= WINDOW_END:
                r_amount = round(random.uniform(300, 1600), 2) if segment in ("homeowner", "designer") else round(random.uniform(1800, 20000), 2)
                add_event("repeat_purchase", rd, sku=random.choice(COLLECTIONS), amount=r_amount)

        # advocacy / review
        if random.random() < 0.34:
            score = max(1, min(10, round(random.gauss(8.2, 1.6))))
            reviews.append({
                "customer_id": cid,
                "score": score,
                "date": (purchase_date + timedelta(days=random.randint(10, 45))).isoformat(),
            })
    else:
        # reactivation attempt for non-purchasers who showed some intent
        if requested_sample or used_visualizer:
            react_date = (sample_date or visualizer_date) + timedelta(days=random.randint(30, 90))
            if react_date <= WINDOW_END:
                camp = "trade_engagement" if segment in ("trade", "commercial") else "reactivation"
                add_email(camp, react_date, opened=random.random() < 0.24, clicked=random.random() < 0.05)


def main():
    customers, events, emails, reviews = [], [], [], []
    for i in range(1, N_CUSTOMERS + 1):
        c = make_customer(i)
        customers.append(c)
        simulate_funnel(c, events, emails, reviews)

    # --- Write clean CSVs ---
    with open(OUT_DIR / "customers.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(customers[0].keys()))
        w.writeheader()
        w.writerows(customers)

    with open(OUT_DIR / "funnel_events.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(events[0].keys()))
        w.writeheader()
        w.writerows(events)

    with open(OUT_DIR / "email_engagement.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(emails[0].keys()))
        w.writeheader()
        w.writerows(emails)

    with open(OUT_DIR / "reviews.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(reviews[0].keys()))
        w.writeheader()
        w.writerows(reviews)

    # --- Load into SQLite ---
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE customers (
        customer_id TEXT PRIMARY KEY, segment TEXT, source_channel TEXT,
        signup_date TEXT, region TEXT, company_name TEXT, email_opt_in INTEGER)""")
    cur.execute("""CREATE TABLE funnel_events (
        event_id TEXT PRIMARY KEY, customer_id TEXT, event_type TEXT,
        event_date TEXT, sku_collection TEXT, channel TEXT, amount REAL)""")
    cur.execute("""CREATE TABLE email_engagement (
        engagement_id TEXT PRIMARY KEY, customer_id TEXT, campaign_type TEXT,
        sent_date TEXT, opened INTEGER, clicked INTEGER)""")
    cur.execute("""CREATE TABLE reviews (
        customer_id TEXT, score INTEGER, date TEXT)""")

    cur.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?,?)",
                     [tuple(c.values()) for c in customers])
    cur.executemany("INSERT INTO funnel_events VALUES (?,?,?,?,?,?,?)",
                     [(e["event_id"], e["customer_id"], e["event_type"], e["event_date"],
                       e["sku_collection"], e["channel"], e["amount"] or None) for e in events])
    cur.executemany("INSERT INTO email_engagement VALUES (?,?,?,?,?,?)",
                     [tuple(e.values()) for e in emails])
    cur.executemany("INSERT INTO reviews VALUES (?,?,?)",
                     [tuple(r.values()) for r in reviews])
    conn.commit()
    conn.close()

    # --- Emit a deliberately messy raw CRM export for the reconciliation story ---
    messy_rows = []
    for c in customers[:600]:
        row = dict(c)
        if random.random() < 0.5:
            row["segment"] = row["segment"].capitalize()
        if random.random() < 0.15:
            row["segment"] = row["segment"].upper()
        # inconsistent date formats
        if random.random() < 0.3:
            d = date.fromisoformat(row["signup_date"])
            row["signup_date"] = d.strftime("%m/%d/%Y")
        # occasional duplicate near-match row (case/whitespace variant of a real customer)
        messy_rows.append(row)
        if random.random() < 0.05:
            dup = dict(row)
            dup["customer_id"] = dup["customer_id"] + "-dup"
            dup["region"] = dup["region"].lower() if dup["region"] else ""
            messy_rows.append(dup)
        if random.random() < 0.06:
            row2 = dict(row)
            row2["customer_id"] = row2["customer_id"] + "-nochan"
            row2["source_channel"] = ""
            messy_rows.append(row2)

    with open(OUT_DIR / "raw_crm_export.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(customers[0].keys()))
        w.writeheader()
        w.writerows(messy_rows)

    print(f"Customers: {len(customers)}")
    print(f"Funnel events: {len(events)}")
    print(f"Email sends: {len(emails)}")
    print(f"Reviews: {len(reviews)}")
    print(f"Messy raw export rows: {len(messy_rows)}")
    print(f"SQLite DB written to {DB_PATH}")


if __name__ == "__main__":
    main()
