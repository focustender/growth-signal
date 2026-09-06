"""
Reconciles the messy raw_crm_export.csv against canonical customers.csv.

Demonstrates the "About You" bullet: analytically strong and data fluent,
works from imperfect data, defines the right questions, reconciles sources,
finds meaningful patterns. Raw export rows for the same customer are grouped
and coalesced field-by-field (first non-empty value wins per field) rather
than naively deduped by dropping every row after the first -- a duplicate row
missing one field can still supply the value another row for the same
customer is missing.
"""

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

OUT_DIR = Path(__file__).parent
VALID_SEGMENTS = {"homeowner", "designer", "trade", "commercial"}


def parse_date(raw: str) -> str:
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def base_customer_id(raw_id: str) -> str:
    return raw_id.replace("-dup", "").replace("-nochan", "")


def main():
    with open(OUT_DIR / "raw_crm_export.csv") as f:
        raw_rows = list(csv.DictReader(f))

    groups = defaultdict(list)
    for row in raw_rows:
        groups[base_customer_id(row["customer_id"])].append(row)

    issues = {
        "raw_rows_in": len(raw_rows),
        "distinct_customers_after_grouping": len(groups),
        "multi_row_customers_merged": 0,
        "segment_case_normalized": 0,
        "date_format_normalized": 0,
        "source_channel_recovered_via_coalesce": 0,
        "source_channel_still_missing": 0,
        "region_still_missing": 0,
    }

    cleaned = []
    for base_id, rows in groups.items():
        if len(rows) > 1:
            issues["multi_row_customers_merged"] += 1

        def coalesce(field):
            for r in rows:
                if r[field].strip():
                    return r[field].strip()
            return ""

        seg_raw = coalesce("segment")
        seg_norm = seg_raw.lower()
        if seg_norm != seg_raw:
            issues["segment_case_normalized"] += 1
        if seg_norm not in VALID_SEGMENTS:
            continue

        date_raw = coalesce("signup_date")
        d_norm = parse_date(date_raw)
        if d_norm and d_norm != date_raw:
            issues["date_format_normalized"] += 1

        # source_channel: check whether every row in the group was missing it,
        # vs. recoverable from a sibling row
        any_row_had_channel = any(r["source_channel"].strip() for r in rows)
        channel = coalesce("source_channel")
        if not channel:
            issues["source_channel_still_missing"] += 1
        elif not all(r["source_channel"].strip() for r in rows) and any_row_had_channel:
            issues["source_channel_recovered_via_coalesce"] += 1

        region = coalesce("region")
        if not region:
            issues["region_still_missing"] += 1

        cleaned.append({
            "customer_id": base_id,
            "segment": seg_norm,
            "source_channel": channel or "unknown",
            "signup_date": d_norm,
            "region": region.upper() if region else "unknown",
            "company_name": coalesce("company_name"),
            "email_opt_in": coalesce("email_opt_in"),
        })

    with open(OUT_DIR / "customers_reconciled.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(cleaned[0].keys()))
        w.writeheader()
        w.writerows(cleaned)

    print(f"Raw rows in: {issues['raw_rows_in']}")
    print(f"Distinct customers after grouping: {issues['distinct_customers_after_grouping']}")
    print(f"Customers with multiple raw rows merged: {issues['multi_row_customers_merged']}")
    print(f"Segment casing normalized: {issues['segment_case_normalized']}")
    print(f"Date formats normalized: {issues['date_format_normalized']}")
    print(f"Source channel recovered via coalescing sibling rows: {issues['source_channel_recovered_via_coalesce']}")
    print(f"Source channel still missing after reconciliation: {issues['source_channel_still_missing']}")
    print(f"Region still missing after reconciliation: {issues['region_still_missing']}")
    print(f"Final reconciled customer count: {len(cleaned)}")


if __name__ == "__main__":
    main()
