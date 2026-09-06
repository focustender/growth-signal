# Task 2 Report — Salesforce seed generator

**Commit:** `13c68f5c635ce5c37da776af0bcfa0f493e32770` — "Add deterministic HubSpot/Salesforce seed split generator"

## What was done

1. Read Task 2's full text from `docs/superpowers/plans/2026-09-06-crm-reconciliation.md` (lines 328-426), including the Design note explaining why cross-system records reuse the 188 already-live HubSpot trade/commercial contacts rather than fabricating new HubSpot-side data.
2. Ran the Step 1 sanity checks against the live repo state:
   - `sqlite3 data/trade_signal.db ".schema customers"` → `customer_id, segment, source_channel, signup_date, region, company_name, email_opt_in` — matches the plan exactly.
   - `head -3 data/hubspot_contacts_import.csv` → header `Email,First Name,Last Name,Company Name,Trade Signal Segment,Trade Signal Source Channel,Trade Signal Signup Date,Trade Signal Region,Trade Signal Customer ID` — matches the plan exactly.
   - Verified counts independently: 188 trade+commercial rows in the CSV (135 trade + 53 commercial), and 769 trade+commercial rows in `customers` (211 commercial + 558 trade), giving 769 − 188 = 581 candidates for `salesforce_only`, matching the plan's stated pool size.
3. Wrote `analysis/crm-reconciliation/tests/test_generate_salesforce_seed.py` from the plan's Step 2 code block, with `import csv` added per the plan's trailing parenthetical.
4. Ran the test file before implementing the module — confirmed it failed with `ModuleNotFoundError: No module named 'generate_salesforce_seed'`, the expected failure per Step 3.
5. Implemented `data/generate_salesforce_seed.py` per Step 4's implementer note:
   - Loads the 188 real trade/commercial HubSpot rows, shuffles with one `random.Random(42)` instance, slices `[:85]` into `cross_system_hubspot_rows` and `[85:188]` into `hubspot_only` (103 rows).
   - Loads `trade`/`commercial` rows from `customers` excluding the 188 customer_ids already in HubSpot, samples 300 with a second, independent `random.Random(42)` instance.
   - Fabricates identity for the 300 `salesforce_only` entries using `FIRST_NAMES`/`LAST_NAMES` imported from `data/generate_hubspot_import.py` via a third `random.Random(42)` instance, with email `f"{first}.{last}.{customer_id.lower()}@example.com"`.
   - Assigns each `salesforce_only` entry a `salesforce_stage` from `{"Open - Not Contacted", "Working - Contacted", "Closed - Converted"}` via a fourth `random.Random(42)` instance's `.choice(...)`.
   - For each of the 85 `cross_system` rows, builds a `salesforce_record` drifted from the real HubSpot row via one of four mutually-exclusive drift functions (name-casing, company-suffix add/remove, omit Phone, shift CreatedDate by 1-5 days) chosen by a fifth `random.Random(42)` instance (plus a dedicated date-shift RNG consumed only when that drift is selected, keeping determinism independent of draw order). `Status` is set to `"Closed - Converted"` unconditionally for every cross-system entry — never varied — per the plan's explicit, non-negotiable instruction.
   - Added a `if __name__ == "__main__":` block (not shown verbatim in the plan's Step 4 excerpt, but required by Step 5's closing instruction to "write the full seed to `data/salesforce_seed.json`") that calls `generate_salesforce_seed()` with defaults and writes the JSON.
6. Ran the tests: **5 passed** (see exact output below).
7. Ran `python3 data/generate_salesforce_seed.py` from the repo root to produce `data/salesforce_seed.json`.
8. Sanity-checked the generated JSON (see below).
9. Staged and committed exactly the three intended files (no `git add -A`).

## Exact test output

```
============================= test session starts ==============================
platform darwin -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0 -- /opt/miniconda3/bin/python3
cachedir: .pytest_cache
rootdir: /Users/iancastorillo/fireclayTile/trade-signal/analysis/crm-reconciliation
plugins: anyio-4.12.1
collecting ... collected 5 items

tests/test_generate_salesforce_seed.py::test_seed_only_includes_trade_and_commercial PASSED [ 20%]
tests/test_generate_salesforce_seed.py::test_seed_counts_match_design PASSED [ 40%]
tests/test_generate_salesforce_seed.py::test_seed_is_deterministic PASSED [ 60%]
tests/test_generate_salesforce_seed.py::test_hubspot_only_entries_are_real_hubspot_rows PASSED [ 80%]
tests/test_generate_salesforce_seed.py::test_cross_system_entries_have_injected_drift PASSED [100%]

============================== 5 passed in 0.06s ===============================
```

Full suite (Task 1 + Task 2 tests together): **12 passed**.

## Generated bucket counts (from `data/salesforce_seed.json`)

- `salesforce_only`: **300**
- `hubspot_only`: **103**
- `cross_system`: **85**

`salesforce_stage` distribution within `salesforce_only`: `Closed - Converted`: 103, `Open - Not Contacted`: 111, `Working - Contacted`: 86 (all three values are the real Lead.Status defaults from `config.example.yaml`, none invented).

Every `cross_system` entry's `salesforce_record["Status"]` is `"Closed - Converted"` — confirmed programmatically (`{e['salesforce_record']['Status'] for e in cross_system} == {"Closed - Converted"}`).

## Concrete drifted cross_system example

Before (real, live HubSpot row) / after (fabricated Salesforce record), customer `CUST-00460`:

```json
// hubspot_record (real, already live in HubSpot)
{
  "Email": "cust-00460@example.com",
  "First Name": "Nancy",
  "Last Name": "Haddad",
  "Company Name": "Cascade Studio",
  "Trade Signal Segment": "commercial",
  "Trade Signal Source Channel": "referral",
  "Trade Signal Signup Date": "2024-10-15",
  "Trade Signal Region": "CA",
  "Trade Signal Customer ID": "CUST-00460"
}

// salesforce_record (new, drifted, to be written in Task 3)
{
  "Email": "cust-00460@example.com",
  "Name": "nancy haddad",
  "Company": "Cascade Studio",
  "Status": "Closed - Converted",
  "CreatedDate": "2024-10-15",
  "Phone": "555-0100"
}
```

Drift: `Name` "Nancy Haddad" → "nancy haddad" (casing drift). `Email` stays identical (the join key for reconciliation), `Status` is unconditionally "Closed - Converted" against HubSpot's real lifecyclestage of "lead", producing the intended real-vs-real stage mismatch.

Two more spot-checked examples, showing the other drift types actually fire across the 85 entries:

- `CUST-01996` (phone-omission drift): HubSpot row `Maria Johnson / Northline Architecture Group`; Salesforce record has `Name: "Maria Johnson"`, `Company` unchanged, but no `Phone` key at all.
- `CUST-03059` (company-suffix drift): HubSpot `Company Name: "Ashford Design Studio"` → Salesforce `Company: "Ashford Design Studio Inc"`.
- `CUST-01561` (date-shift drift): HubSpot `Trade Signal Signup Date: "2025-08-12"` → Salesforce `CreatedDate: "2025-08-11"` (shifted by 1 day).

All four drift types (name-case, company-suffix, omit-phone, shift-date) were confirmed present across the 85 `cross_system` entries — the injected drift is real, not degenerate to a single type.

## Deviations from the plan's literal text, with justification

1. **Fixed an off-by-one bug in the test file's `parents[]` index.** The plan's Step 2 code block uses `Path(__file__).resolve().parents[2] / "data"` (and the same index for `DB_PATH`/`HUBSPOT_CSV_PATH`). For a file at `analysis/crm-reconciliation/tests/test_generate_salesforce_seed.py`, `parents[2]` resolves to `trade-signal/analysis` (three directories up: tests → crm-reconciliation → analysis), not the repo root `trade-signal`. `data/` lives at the repo root, sibling to `analysis/`, so reaching it from the test file requires `parents[3]`. I verified this by resolving both indices directly with `pathlib` before touching the test. This is not a case of "loosening a test to match an implementation bug" — the bug was in the test's own path arithmetic, and no implementation, however correct, could have satisfied the literal Step 2 text; the module and fixture files genuinely aren't at `analysis/data`. I changed both occurrences of `parents[2]` to `parents[3]`.
2. **Added a `if __name__ == "__main__":` block to `data/generate_salesforce_seed.py`.** The plan's Step 4 code excerpt doesn't show one explicitly, but Step 4's closing sentence and Step 5 both require writing the full seed to `data/salesforce_seed.json`, and the task instructions explicitly called for adding a minimal entry point if the excerpt didn't show one. Added a block that calls `generate_salesforce_seed()` with default paths and writes indented JSON, printing a summary line.
3. **Noted, not changed:** importing `generate_hubspot_import` (required by the plan to reuse its `FIRST_NAMES`/`LAST_NAMES` lists) re-executes that module's top-level code, which rewrites `data/hubspot_contacts_import.csv` as a side effect on every import (it has no `if __name__ == "__main__":` guard — pre-existing behavior, not introduced by this task). Verified via `git diff --stat` after running the generator that this rewrite is fully deterministic (`random.seed(7)`) and produced a byte-identical file, so no unintended data change occurred. Flagging this for awareness in case a future task wants to guard that module's top-level code, but did not change it since it's out of this task's scope and caused no observable harm.

No other deviations. Field shapes, bucket sizes, RNG instance separation, and the unconditional `Status = "Closed - Converted"` rule all match the plan's literal Step 4 specification.
