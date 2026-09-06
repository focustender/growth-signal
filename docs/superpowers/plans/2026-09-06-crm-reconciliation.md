# HubSpot <-> Salesforce Lifecycle Data-Quality Reconciliation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a portable, config-driven tool that pulls contact/account records from a live HubSpot account and a live Salesforce Developer Edition org, flags cross-system duplicates and lifecycle-stage mismatches, and produces a data-quality audit + a proposed unified lifecycle-stage taxonomy — directly demonstrating the JD's "Partner with Technology on HubSpot–Salesforce data quality, lifecycle-stage alignment" bullet.

**Architecture:** `reconcile.py` is a pure function library (normalize -> match -> flag) that takes two lists of generically-shaped dicts plus a YAML field-mapping config — it never references Fireclay-specific field names, so it reads as a methodology, not glue code. Two thin extractor scripts (`extract_hubspot.py`, `extract_salesforce.py`) populate those lists from live accounts and are independently runnable by anyone with their own credentials. A seed generator (`generate_salesforce_seed.py`) derives a realistic, deliberately messy 3-way data split from the project's existing `trade_signal.db` so the "messiness" being reconciled is deterministic and explainable, not random noise.

**Tech Stack:** Python 3, `simple-salesforce` (Salesforce REST), `requests` (HubSpot REST v3), `rapidfuzz` (fuzzy name/company matching), `PyYAML`, `pytest`, `python-dotenv`.

**Spec:** `/Users/iancastorillo/.claude/plans/i-m-realizing-i-would-clever-canyon.md` (see "Build A" section). This plan implements that spec's technical decisions, with one correction: extractor scripts use REST APIs directly (not Claude Code's MCP tools, which aren't callable from a standalone script) — see Task 5's note.

## Global Constraints

- Working directory: `/Users/iancastorillo/fireclayTile/trade-signal` (standalone git repo, pushed to `https://github.com/focustender/growth-signal`).
- No Fireclay-specific field names hardcoded inside `reconcile.py` itself — all field mapping lives in `config.yaml`.
- Every real credential is read from `.env` (never committed; `.env.example` already exists as the template).
- Deterministic seeding: reuse `random.seed(42)` convention already established in `data/generate_dataset.py`.
- Every doc/output labels itself real/live vs. synthetic vs. simulated, per the project's existing honesty convention (see `visualizer/README.md` and `docs/hubspot-setup.md` for tone reference).
- Commit after each task passes its tests.

---

### Task 1: Reconciliation engine core — normalize, match, flag (TDD)

**Files:**
- Create: `analysis/crm-reconciliation/config.example.yaml`
- Create: `analysis/crm-reconciliation/reconcile.py`
- Create: `analysis/crm-reconciliation/tests/fixtures/hubspot_sample.json`
- Create: `analysis/crm-reconciliation/tests/fixtures/salesforce_sample.json`
- Test: `analysis/crm-reconciliation/tests/test_reconcile.py`

**Interfaces:**
- Produces: `normalize_record(record: dict, field_map: dict) -> dict` returning `{email, full_name, company, lifecycle_stage, created_date, source_system, source_id}`.
- Produces: `reconcile(hubspot_records: list[dict], salesforce_records: list[dict], config: dict) -> dict` returning `{"matched": [...], "hubspot_only": [...], "salesforce_only": [...], "stage_mismatches": [...], "summary": {...}}`. Each matched entry: `{"hubspot_id", "salesforce_id", "match_method": "email"|"fuzzy", "confidence": float, "field_diffs": {...}}`.

- [ ] **Step 1: Write `config.example.yaml`**

```yaml
# Generic field-mapping config. Copy to config.yaml and adjust the right-hand
# side to match your own CRMs' actual field/property names.
hubspot:
  email: "email"
  full_name: "firstname+lastname"   # special token: concatenate two properties
  company: "company"
  lifecycle_stage: "trade_signal_segment_stage"   # your own lifecycle property
  created_date: "trade_signal_signup_date"
salesforce:
  email: "Email"
  full_name: "Name"
  company: "Company"
  lifecycle_stage: "Status"      # Lead.Status — Task 3 ingests as Leads, not Opportunities
  created_date: "CreatedDate"
matching:
  fuzzy_threshold: 85   # rapidfuzz token_sort_ratio, 0-100
lifecycle_stage_map:
  # Canonical stage -> [HubSpot values], [Salesforce values]
  # Salesforce values here are Lead.Status's real default picklist values
  # (Developer Edition, uncustomized) since Task 3 ingests as Leads, not
  # Opportunities. Verify with sf.Lead.describe() before relying on these.
  "lead":        {hubspot: ["subscriber", "lead"], salesforce: ["Open - Not Contacted"]}
  "qualified":   {hubspot: ["marketingqualifiedlead", "salesqualifiedlead"], salesforce: ["Working - Contacted"]}
  "opportunity": {hubspot: ["opportunity"], salesforce: []}
  "customer":    {hubspot: ["customer"], salesforce: ["Closed - Converted"]}
  # Note: a plain Lead object cannot distinguish "opportunity" from
  # "customer" (Salesforce's own data model converts a Lead into an
  # Account+Contact+Opportunity rather than tracking finer-grained status)
  # -- this is a real system limitation, not a config gap, and belongs in
  # systems-requirements-memo.md (Task 5, Step 7), not something to paper
  # over by inventing a Status value that doesn't exist in the org.
```

- [ ] **Step 2: Write test fixtures**

`analysis/crm-reconciliation/tests/fixtures/hubspot_sample.json`:
```json
[
  {"id": "hs-1", "email": "jon.smith@example.com", "firstname": "Jon", "lastname": "Smith", "company": "Smith Tile Co", "trade_signal_segment_stage": "opportunity", "trade_signal_signup_date": "2025-03-01"},
  {"id": "hs-2", "email": "no.match@example.com", "firstname": "Pat", "lastname": "Nguyen", "company": "Nguyen Design", "trade_signal_segment_stage": "lead", "trade_signal_signup_date": "2025-05-10"},
  {"id": "hs-3", "email": "", "firstname": "Alexandra", "lastname": "Reyes-Park", "company": "Reyes Park Studio", "trade_signal_segment_stage": "qualified", "trade_signal_signup_date": "2025-06-02"}
]
```

`analysis/crm-reconciliation/tests/fixtures/salesforce_sample.json`:
```json
[
  {"Id": "sf-1", "Email": "jon.smith@example.com", "Name": "John Smith", "Company": "Smith Tile Co.", "Status": "Closed - Converted", "CreatedDate": "2025-03-04"},
  {"Id": "sf-2", "Email": "only.sf@example.com", "Name": "Priya Raman", "Company": "Raman Contracting", "Status": "Working - Contacted", "CreatedDate": "2025-04-11"},
  {"Id": "sf-3", "Email": "", "Name": "Alex Reyes-Park", "Company": "Reyes-Park Studio", "Status": "Working - Contacted", "CreatedDate": "2025-06-05"}
]
```

(This fixture deliberately encodes: an exact-email match with a stage mismatch (`hs-1`/`sf-1`, HubSpot's "opportunity" vs. Salesforce's "Closed - Converted" — Sales already closed the deal, but the HubSpot record hasn't caught up, and a plain Lead object has no separate "opportunity" state to represent the in-between step — both map to different canonical stages), a HubSpot-only orphan (`hs-2`), a Salesforce-only orphan (`sf-2`), and an email-less fuzzy-match pair (`hs-3`/`sf-3`, name/company drift, no email to key on).)

- [ ] **Step 3: Write the failing tests**

```python
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
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `cd analysis/crm-reconciliation && python3 -m pytest tests/test_reconcile.py -v`
Expected: FAIL / ERROR — `reconcile.py` does not exist yet (`ModuleNotFoundError`).

- [ ] **Step 5: Implement `reconcile.py`**

```python
"""Generic two-CRM reconciliation engine.

Takes two lists of raw records plus a field-mapping config and produces a
match/orphan/mismatch report. Contains no Fireclay-specific field names —
all mapping lives in config.yaml. Intended to be adapted to any pair of
CRM exports by changing only the config.
"""
from rapidfuzz import fuzz


def normalize_record(record: dict, field_map: dict, source_system: str) -> dict:
    def get(key):
        spec = field_map.get(key, "")
        if "+" in spec:
            parts = [str(record.get(p.strip(), "")).strip() for p in spec.split("+")]
            return " ".join(p for p in parts if p)
        return str(record.get(spec, "") or "").strip()

    return {
        "email": get("email").lower(),
        "full_name": get("full_name"),
        "company": get("company"),
        "lifecycle_stage": get("lifecycle_stage"),
        "created_date": get("created_date"),
        "source_system": source_system,
        "source_id": record.get("id") or record.get("Id"),
    }


def _canonical_stage(raw_stage: str, source_system: str, stage_map: dict) -> str | None:
    for canonical, systems in stage_map.items():
        if raw_stage in systems.get(source_system, []):
            return canonical
    return None


def reconcile(hubspot_records: list, salesforce_records: list, config: dict) -> dict:
    hs_norm = [normalize_record(r, config["hubspot"], "hubspot") for r in hubspot_records]
    sf_norm = [normalize_record(r, config["salesforce"], "salesforce") for r in salesforce_records]
    threshold = config.get("matching", {}).get("fuzzy_threshold", 85)
    stage_map = config.get("lifecycle_stage_map", {})

    matched, stage_mismatches = [], []
    matched_sf_ids = set()

    # Pass 1: exact email match
    sf_by_email = {r["email"]: r for r in sf_norm if r["email"]}
    for hs in hs_norm:
        if hs["email"] and hs["email"] in sf_by_email:
            sf = sf_by_email[hs["email"]]
            matched.append({
                "hubspot_id": hs["source_id"], "salesforce_id": sf["source_id"],
                "match_method": "email", "confidence": 100.0,
                "field_diffs": _diff(hs, sf),
            })
            matched_sf_ids.add(sf["source_id"])
            _check_stage(hs, sf, stage_map, stage_mismatches)

    matched_hs_ids = {m["hubspot_id"] for m in matched}

    # Pass 2: fuzzy match on name+company for records with no email
    remaining_hs = [r for r in hs_norm if r["source_id"] not in matched_hs_ids]
    remaining_sf = [r for r in sf_norm if r["source_id"] not in matched_sf_ids]
    for hs in remaining_hs:
        if not hs["full_name"]:
            continue
        best, best_score = None, 0
        for sf in remaining_sf:
            if sf["source_id"] in matched_sf_ids or not sf["full_name"]:
                continue
            score = fuzz.token_sort_ratio(
                f"{hs['full_name']} {hs['company']}", f"{sf['full_name']} {sf['company']}"
            )
            if score > best_score:
                best, best_score = sf, score
        if best and best_score >= threshold:
            matched.append({
                "hubspot_id": hs["source_id"], "salesforce_id": best["source_id"],
                "match_method": "fuzzy", "confidence": float(best_score),
                "field_diffs": _diff(hs, best),
            })
            matched_sf_ids.add(best["source_id"])
            _check_stage(hs, best, stage_map, stage_mismatches)

    matched_hs_ids = {m["hubspot_id"] for m in matched}
    hubspot_only = [{"id": r["source_id"], "email": r["email"], "full_name": r["full_name"]}
                    for r in hs_norm if r["source_id"] not in matched_hs_ids]
    salesforce_only = [{"id": r["source_id"], "email": r["email"], "full_name": r["full_name"]}
                       for r in sf_norm if r["source_id"] not in matched_sf_ids]

    return {
        "matched": matched,
        "hubspot_only": hubspot_only,
        "salesforce_only": salesforce_only,
        "stage_mismatches": stage_mismatches,
        "summary": {
            "matched_count": len(matched),
            "hubspot_only_count": len(hubspot_only),
            "salesforce_only_count": len(salesforce_only),
            "stage_mismatch_count": len(stage_mismatches),
        },
    }


def _diff(hs: dict, sf: dict) -> dict:
    diffs = {}
    for field in ("full_name", "company"):
        if hs[field].strip().lower() != sf[field].strip().lower():
            diffs[field] = {"hubspot": hs[field], "salesforce": sf[field]}
    return diffs


def _check_stage(hs: dict, sf: dict, stage_map: dict, out: list):
    hs_canon = _canonical_stage(hs["lifecycle_stage"], "hubspot", stage_map)
    sf_canon = _canonical_stage(sf["lifecycle_stage"], "salesforce", stage_map)
    if hs_canon != sf_canon:
        out.append({
            "hubspot_id": hs["source_id"], "salesforce_id": sf["source_id"],
            "hubspot_raw_stage": hs["lifecycle_stage"], "salesforce_raw_stage": sf["lifecycle_stage"],
            "hubspot_canonical_stage": hs_canon, "salesforce_canonical_stage": sf_canon,
        })
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd analysis/crm-reconciliation && python3 -m pytest tests/test_reconcile.py -v`
Expected: 7 passed.

- [ ] **Step 7: Commit**

```bash
git add analysis/crm-reconciliation/config.example.yaml analysis/crm-reconciliation/reconcile.py analysis/crm-reconciliation/tests/
git commit -m "Add CRM reconciliation engine with passing test suite"
```

---

### Task 2: Salesforce seed generator — derive the 3-way split from `trade_signal.db`

**Files:**
- Create: `data/generate_salesforce_seed.py`
- Test: `analysis/crm-reconciliation/tests/test_generate_salesforce_seed.py`

**Interfaces:**
- Consumes: `trade_signal.db`'s `customers` table (already has `segment` column with values `homeowner|designer|trade|commercial`, and presumably `customer_id`, `full_name`/`first_name`/`last_name`, `email`, `company`, `signup_date` — confirm exact schema by running `sqlite3 data/trade_signal.db ".schema customers"` before writing this task's implementation, since prior tasks assumed but did not verify this schema).
- Produces: `generate_salesforce_seed(db_path: str, seed: int = 42) -> dict` returning `{"salesforce_only": [...], "hubspot_only_ids": [...], "cross_system": [...]}` where each `cross_system` entry has a `hubspot_record` and a `salesforce_record` with deliberately injected drift (name casing/typo, company suffix drift, missing phone, signup-date +/- a few days, and a stage mismatch consistent with `config.example.yaml`'s `lifecycle_stage_map`).

- [ ] **Step 1: Inspect the real schema first**

Run: `sqlite3 /Users/iancastorillo/fireclayTile/trade-signal/data/trade_signal.db ".schema customers"`

Use the actual column names returned here in every step below — do not assume names not confirmed by this output.

- [ ] **Step 2: Write the failing test** (adapt field names to Step 1's real schema)

```python
# analysis/crm-reconciliation/tests/test_generate_salesforce_seed.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "data"))
import generate_salesforce_seed as gss

DB_PATH = str(Path(__file__).resolve().parents[2] / "data" / "trade_signal.db")

def test_seed_only_includes_trade_and_commercial():
    seed = gss.generate_salesforce_seed(DB_PATH, seed=42)
    all_segments = set()
    for entry in seed["salesforce_only"]:
        all_segments.add(entry["segment"])
    assert all_segments <= {"trade", "commercial"}

def test_seed_is_deterministic():
    seed_a = gss.generate_salesforce_seed(DB_PATH, seed=42)
    seed_b = gss.generate_salesforce_seed(DB_PATH, seed=42)
    assert seed_a == seed_b

def test_cross_system_entries_have_injected_drift():
    seed = gss.generate_salesforce_seed(DB_PATH, seed=42)
    assert len(seed["cross_system"]) > 0
    entry = seed["cross_system"][0]
    assert "hubspot_record" in entry and "salesforce_record" in entry
    # names should differ in at least one cross-system entry (drift was injected)
    drifted = [e for e in seed["cross_system"]
               if e["hubspot_record"]["full_name"] != e["salesforce_record"]["Name"]]
    assert len(drifted) > 0
```

- [ ] **Step 3: Run to verify failure**

Run: `cd analysis/crm-reconciliation && python3 -m pytest tests/test_generate_salesforce_seed.py -v`
Expected: FAIL — module not found.

- [ ] **Step 4: Implement `data/generate_salesforce_seed.py`**

Implementer note (fill in with real column names from Step 1): read all `trade` and `commercial` rows from `customers`, `random.seed(42)`, shuffle deterministically, split ~40% Salesforce-only / ~30% HubSpot-only (matching customer IDs already in `hubspot_contacts_import.csv`) / ~30% cross-system. For cross-system entries, build a `hubspot_record` dict shaped like `hubspot_contacts_import.csv`'s columns and a `salesforce_record` dict shaped like `{Id, Email, Name, Company, Status, CreatedDate, Phone}` where `Status` is one of Salesforce Lead's real default picklist values — `"Open - Not Contacted"`, `"Working - Contacted"`, or `"Closed - Converted"` (matching `config.example.yaml`'s `lifecycle_stage_map`; do not invent values not in that list) — then apply one deterministic drift function per entry chosen from: name-casing/typo, company-suffix (add/remove "Inc"/"LLC"), drop `Phone`, shift `CreatedDate` by a random 1-5 days, and set `Status`/`trade_signal_segment_stage` to a canonical-stage pair that intentionally disagree (e.g. HubSpot still shows `"opportunity"` while Salesforce's `Status` already reads `"Closed - Converted"`), for a realistic "sales closed it before marketing's record caught up" story. `salesforce_only` entries follow the same `Status` constraint. Write the full seed to `data/salesforce_seed.json` for manual review before Task 3 ingests it live.

- [ ] **Step 5: Run to verify pass**

Run: `cd analysis/crm-reconciliation && python3 -m pytest tests/test_generate_salesforce_seed.py -v`
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add data/generate_salesforce_seed.py analysis/crm-reconciliation/tests/test_generate_salesforce_seed.py
git commit -m "Add deterministic HubSpot/Salesforce seed split generator"
```

---

### Task 3: Salesforce client + live seed ingestion

**Files:**
- Create: `analysis/crm-reconciliation/salesforce_client.py`
- Create: `analysis/crm-reconciliation/salesforce_seed_ingest.py`
- Create: `docs/salesforce-setup.md`

**Interfaces:**
- Consumes: `data/salesforce_seed.json` (Task 2's output), `.env`'s `SALESFORCE_USERNAME`/`SALESFORCE_PASSWORD`/`SALESFORCE_SECURITY_TOKEN`/`SALESFORCE_DOMAIN`.
- Produces: `get_client() -> simple_salesforce.Salesforce` in `salesforce_client.py`, used by both this task and Task 5.

**Prerequisite:** Ian's `.env` must have real Salesforce credentials filled in before Step 3 below can run for real. Steps 1-2 can be written and reviewed without live credentials.

- [ ] **Step 1: Write `salesforce_client.py`**

```python
"""Thin simple_salesforce wrapper reading credentials from environment."""
import os
from dotenv import load_dotenv
from simple_salesforce import Salesforce

load_dotenv()


def get_client() -> Salesforce:
    username = os.environ["SALESFORCE_USERNAME"]
    password = os.environ["SALESFORCE_PASSWORD"]
    token = os.environ["SALESFORCE_SECURITY_TOKEN"]
    domain = os.environ.get("SALESFORCE_DOMAIN", "login")
    return Salesforce(username=username, password=password, security_token=token, domain=domain)
```

- [ ] **Step 2: Write `salesforce_seed_ingest.py`**

```python
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
            "Status": sf_rec["StageName"],
        })
        created_ids.append(rec["id"])

    return {"created_count": len(created_ids), "created_ids": created_ids}


if __name__ == "__main__":
    result = ingest()
    print(f"Created {result['created_count']} Salesforce Lead records.")
```

- [ ] **Step 3: Run for real (requires Ian's `.env` to be filled in)**

Run: `cd analysis/crm-reconciliation && python3 salesforce_seed_ingest.py`
Expected: prints a created count matching the seed's `salesforce_only` + `cross_system` lengths. If this fails with an auth error, use `superpowers:systematic-debugging` rather than guessing — check the exact `simple_salesforce` exception message first (most common causes: security token needs to be appended to the password with no space in some auth flows — `simple_salesforce` handles this internally when passed separately, so a raw auth failure usually means the token was reset by a recent password change, requiring a fresh token from Salesforce Setup > My Personal Information > Reset My Security Token).

- [ ] **Step 4: Verify live, read back through the org** (same discipline as `docs/hubspot-setup.md`)

```python
from salesforce_client import get_client
sf = get_client()
result = sf.query("SELECT Id, Email, Status FROM Lead LIMIT 5")
print(result["records"])
```

- [ ] **Step 5: Write `docs/salesforce-setup.md`**, mirroring `docs/hubspot-setup.md`'s structure: what was seeded, exact counts (live-verified via Step 4's query, not assumed from the ingest script's return value), and any tooling gaps encountered.

- [ ] **Step 6: Commit**

```bash
git add analysis/crm-reconciliation/salesforce_client.py analysis/crm-reconciliation/salesforce_seed_ingest.py docs/salesforce-setup.md
git commit -m "Add Salesforce client and live seed ingestion, verified"
```

---

### Task 4: HubSpot extractor (portable REST path) + live extract capture

**Files:**
- Create: `analysis/crm-reconciliation/hubspot_client.py`
- Create: `analysis/crm-reconciliation/extract_hubspot.py`
- Create: `analysis/crm-reconciliation/data/hubspot_extract.json` (the actual live-captured data for this repo's demo)

**Note on architecture (correction to the original spec):** Claude Code's HubSpot MCP tools (`mcp__hubspot__query_crm_data` etc.) are only callable interactively by an agent inside a Claude Code session — they are not a library a standalone Python script can import or call via subprocess. So `extract_hubspot.py` must use HubSpot's REST API directly with a Private App token to be genuinely portable and runnable by someone without Claude Code configured. For the specific data checked into this repo, use Claude Code's own MCP connection directly (interactively, in this session) to pull the live trade/commercial contacts and write `data/hubspot_extract.json` — the same "verify live through the connector" pattern `docs/hubspot-setup.md` already established — documenting that this file's provenance is the MCP connector, while `extract_hubspot.py` remains the reusable script for a reader with their own Private App token.

- [ ] **Step 1: Write `hubspot_client.py`** (REST v3, Private App token)

```python
"""HubSpot REST v3 client using a Private App token.
Create one under HubSpot Settings > Integrations > Private Apps
with 'crm.objects.contacts.read' scope, and put it in .env as
HUBSPOT_PRIVATE_APP_TOKEN."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()
BASE_URL = "https://api.hubapi.com"


def search_contacts(segment: str, properties: list[str]) -> list[dict]:
    token = os.environ["HUBSPOT_PRIVATE_APP_TOKEN"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {
        "filterGroups": [{"filters": [
            {"propertyName": "trade_signal_segment", "operator": "EQ", "value": segment}
        ]}],
        "properties": properties,
        "limit": 100,
    }
    results, after = [], None
    while True:
        if after:
            body["after"] = after
        resp = requests.post(f"{BASE_URL}/crm/v3/objects/contacts/search", json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        results.extend(r["properties"] | {"id": r["id"]} for r in data["results"])
        after = data.get("paging", {}).get("next", {}).get("after")
        if not after:
            break
    return results
```

- [ ] **Step 2: Write `extract_hubspot.py`**

```python
"""Pulls trade + commercial HubSpot contacts and writes them to
data/hubspot_extract.json in the shape reconcile.py expects."""
import json
from pathlib import Path
from hubspot_client import search_contacts

PROPERTIES = ["email", "firstname", "lastname", "company",
              "trade_signal_segment_stage", "trade_signal_signup_date"]


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
```

- [ ] **Step 3: Capture the live extract for this repo**

In this Claude Code session (not via the script above, per the architecture note): use the `mcp__hubspot__search_crm_objects` or `mcp__hubspot__query_crm_data` tool to pull all contacts where `trade_signal_segment` is `trade` or `commercial`, with the same properties `PROPERTIES` lists above. Write the result to `analysis/crm-reconciliation/data/hubspot_extract.json`. Confirm the count matches `docs/hubspot-setup.md`'s documented 135 trade + 53 commercial = 188 (minus however many were deliberately left HubSpot-only vs. duplicated into Salesforce per Task 2's split — reconcile the exact expected count against `data/salesforce_seed.json`'s `hubspot_only_ids` length plus the cross-system count before treating a mismatch as a bug).

- [ ] **Step 4: Commit**

```bash
git add analysis/crm-reconciliation/hubspot_client.py analysis/crm-reconciliation/extract_hubspot.py analysis/crm-reconciliation/data/hubspot_extract.json
git commit -m "Add portable HubSpot extractor and capture live extract"
```

---

### Task 5: Salesforce extractor + real reconciliation run + write-ups

**Files:**
- Create: `analysis/crm-reconciliation/extract_salesforce.py`
- Create: `analysis/crm-reconciliation/config.yaml` (real, gitignored? — no, this one has no secrets, only field names, so it's fine to commit; only `.env` is secret)
- Create: `analysis/crm-reconciliation/output/reconciliation_report.json`
- Create: `analysis/crm-reconciliation/output/reconciliation_findings.md`
- Create: `analysis/crm-reconciliation/lifecycle_stage_taxonomy.md`
- Create: `analysis/crm-reconciliation/systems-requirements-memo.md`
- Create: `analysis/crm-reconciliation/README.md`

**Interfaces:**
- Consumes: `hubspot_client.py` is not needed here; uses `salesforce_client.py`'s `get_client()`.
- Produces: `extract() -> list[dict]` in `extract_salesforce.py`, same shape convention as Task 4.

- [ ] **Step 1: Write `extract_salesforce.py`**

```python
"""Pulls the seeded Lead records and writes them to
data/salesforce_extract.json in the shape reconcile.py expects."""
import json
from pathlib import Path
from salesforce_client import get_client


def extract() -> list[dict]:
    sf = get_client()
    result = sf.query_all(
        "SELECT Id, Email, Name, Company, Status, CreatedDate FROM Lead"
    )
    return [{k: v for k, v in r.items() if k != "attributes"} for r in result["records"]]


if __name__ == "__main__":
    records = extract()
    out_path = Path(__file__).parent / "data" / "salesforce_extract.json"
    with open(out_path, "w") as f:
        json.dump(records, f, indent=2)
    print(f"Wrote {len(records)} records to {out_path}")
```

- [ ] **Step 2: Run it for real**

Run: `cd analysis/crm-reconciliation && python3 extract_salesforce.py`
Expected: writes `data/salesforce_extract.json` with a count matching Task 3 Step 4's live query.

- [ ] **Step 3: Copy `config.example.yaml` to `config.yaml`** as-is — it already targets Lead's `Status` field, matching how Task 3 ingests records. Only adjust field names here if live `sf.Lead.describe()` output (Task 3, Step 4) revealed different real values than assumed.

- [ ] **Step 4: Run the real reconciliation**

```python
import json
import yaml
from reconcile import reconcile

with open("data/hubspot_extract.json") as f:
    hs = json.load(f)
with open("data/salesforce_extract.json") as f:
    sf = json.load(f)
with open("config.yaml") as f:
    config = yaml.safe_load(f)

result = reconcile(hs, sf, config)
with open("output/reconciliation_report.json", "w") as f:
    json.dump(result, f, indent=2)
print(result["summary"])
```

- [ ] **Step 5: Write `output/reconciliation_findings.md`**

Report the real `summary` counts from Step 4 in prose, in the same numbers-forward tone as `docs/measurement-foundation.md` — e.g. "Of N matched cross-system records, M had a lifecycle-stage mismatch..." Use the actual numbers produced, not placeholder text.

- [ ] **Step 6: Write `lifecycle_stage_taxonomy.md`**

A table mapping each canonical stage in `config.yaml`'s `lifecycle_stage_map` to its HubSpot and Salesforce raw values, plus one paragraph on which system should be system-of-record for which stage transition (e.g., "a Lead becomes Salesforce's system-of-record for `qualified` onward, since that's when Sales, not Marketing, drives the next action").

- [ ] **Step 7: Write `systems-requirements-memo.md`**

Answer the JD's own phrase directly: what would actually need to change operationally/technically to keep the two systems in sync going forward. Base this on the real mismatch patterns found in Step 4-5's output, not generic CRM-integration advice — e.g. if most mismatches are the same one or two canonical-stage pairs disagreeing, the memo's recommendation should target exactly that (a specific field-sync rule or webhook), not a generic "buy an integration tool."

- [ ] **Step 8: Write `analysis/crm-reconciliation/README.md`** — the reusable-methodology doc: what this tool does, how the config works, and a real "adapt this to your own HubSpot + Salesforce org" walkthrough (copy `config.example.yaml`, fill in your own field names, run the three scripts in order).

- [ ] **Step 9: Commit**

```bash
git add analysis/crm-reconciliation/
git commit -m "Run real HubSpot/Salesforce reconciliation and write up findings"
```

---

## Self-Review Notes (completed during plan authoring)

- **Spec coverage:** every Build A element from the approved spec (seed split, reconcile engine, taxonomy, systems memo, honesty labeling) has a task above.
- **Corrected assumption:** extractor architecture (REST-only, not MCP-in-script) — flagged inline in Task 4, applied consistently in Task 5.
- **Schema risk flagged explicitly:** Task 2 Step 1 requires checking `trade_signal.db`'s real schema before writing code against assumed column names — do not skip this.
- **Lead vs. Opportunity field-name risk caught during authoring, not after:** an earlier draft of this plan mixed Opportunity's `StageName` values (e.g. "Closed Won") into a Lead-object config, which would have failed at live-write time since those aren't valid `Lead.Status` picklist values. Fixed throughout — `config.example.yaml`, both fixtures, and Task 2's seed generator now consistently use Lead's real default `Status` values. Task 3, Step 4's live `sf.Lead.describe()` check still stands as the final confirmation before trusting these values against the actual org (picklists can be customized).
