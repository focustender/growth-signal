# HubSpot ↔ Salesforce Lifecycle Reconciliation

## What this is

A small, config-driven tool that pulls contact/lead records from two live CRMs, matches them across systems, and flags where their lifecycle stages disagree. It was built against a real HubSpot account and a real Salesforce Developer Edition org (both free-tier), not mock data — see `docs/hubspot-setup.md` and `docs/salesforce-setup.md` for exactly what was seeded and how.

Real results from this project's own org pair: **92 matched records** (85 by exact email, 7 by fuzzy name+company — see `output/reconciliation_findings.md` for why the fuzzy-match count isn't exactly 0), **293 Salesforce-only** and **96 HubSpot-only** orphans, and — the actual finding — **100% of the 85 genuine cross-system matches show a lifecycle-stage mismatch**, every one the same pattern: HubSpot's `lifecyclestage` frozen at `"lead"` since import, Salesforce's `Lead.Status` already at `"Closed - Converted"`. Full write-up in `output/reconciliation_findings.md`; the taxonomy behind the matching in `lifecycle_stage_taxonomy.md`; what to actually do about it in `systems-requirements-memo.md`.

## What this isn't

Not a Fireclay-specific script. `reconcile.py` contains zero hardcoded Fireclay field names — every field name it touches comes from `config.yaml` at call time. Not a generic ETL/sync product either: it doesn't write anything back to either CRM (see the systems-requirements memo for what a real sync would need). It reads two record lists and a config, and returns a match/orphan/mismatch report — that's the whole scope.

## How it works

Three pieces, in order:

1. **`config.yaml`** (copy of `config.example.yaml`, filled in for this project's own field names — see below) tells `reconcile.py` which raw property/field name on each side maps to each of five normalized concepts (`email`, `full_name`, `company`, `lifecycle_stage`, `created_date`), plus a `lifecycle_stage_map` that collapses each system's own raw picklist values down to a shared set of canonical stages (`lead`, `qualified`, `opportunity`, `customer`).
2. **`reconcile.py`** takes two lists of raw record dicts (whatever shape your CRM's API actually returns) plus the parsed config. It normalizes both sides through `config.yaml`'s field map, matches records first by exact (lowercased) email, then — for whatever's left unmatched on both sides — by fuzzy name+company similarity (`rapidfuzz.token_sort_ratio`, threshold configurable under `matching.fuzzy_threshold`). For every matched pair it also compares canonical lifecycle stage on each side and records a mismatch if they disagree. Returns `{"matched", "hubspot_only", "salesforce_only", "stage_mismatches", "summary"}`. No I/O, no side effects — it's a pure function over two lists and a dict, which is what makes it trivially unit-testable (`tests/test_reconcile.py`) and portable.
3. **Two extractor scripts**, `extract_hubspot.py` and `extract_salesforce.py`, are the only Fireclay-shaped part of this repo — thin scripts that call each CRM's own API and write a JSON list in the shape `reconcile.py` expects. They're deliberately separate from `reconcile.py` so that adapting this to a different pair of CRMs (or even a different pair of exports — two CSVs would work identically) only means rewriting the extractors, never the engine.

## Adapting this to your own HubSpot + Salesforce org

1. **Copy the config.** `cp config.example.yaml config.yaml`. Fill in the right-hand side of `hubspot:`/`salesforce:` with your own CRMs' actual property/field API names (not display labels — e.g. HubSpot's internal name, not what shows in the UI). `full_name` supports a `"firstname+lastname"`-style `+`-joined token if your CRM splits name into two properties; leave it as a single field name otherwise. Rewrite `lifecycle_stage_map` to your own systems' real picklist values — don't reuse this project's values as-is; they're this org's `Lead.Status` and HubSpot's default `lifecyclestage` picklist, and yours will likely differ (custom stages, an Opportunity-based pipeline instead of Lead-only, etc.). Verify against your own CRM's field describe/schema output before trusting the config — this project caught a real field-name mistake (`Opportunity.StageName` values accidentally mixed into a `Lead.Status` config) during planning exactly this way.
2. **Skip the seed generator.** `data/generate_salesforce_seed.py` exists only to manufacture this project's own deliberately-messy demo data from a synthetic dataset that doesn't exist anywhere else. A real adopter reconciling their own live org has real data already and has no use for it.
3. **Get your own credentials.** `salesforce_client.py` needs a Salesforce Connected App configured for the JWT Bearer OAuth flow (see its module docstring and `docs/salesforce-setup.md` for exactly why — plain SOAP login and the OAuth username-password flow are both disabled by default on new orgs). A HubSpot extractor needs a Private App token with `crm.objects.contacts.read` scope (see `hubspot_client.py`'s docstring). Put both in `.env`, following `.env.example`.
4. **Run the extractors.** `python3 extract_hubspot.py` and `python3 extract_salesforce.py`, each writing to `data/`.

   **Honest caveat on the HubSpot side:** `extract_hubspot.py` was written to be the reusable, portable path (REST v3, a Private App token, runnable with no Claude Code dependency) — but it was never actually executed in this project. The live `data/hubspot_extract.json` checked into this repo was captured a different way: directly through Claude Code's HubSpot MCP connector, interactively, in the same session that built this tool (documented in the Task 4 commit, `6de5658`). That was a deliberate scoping call for this project specifically, not a discovery that the REST path doesn't work — but it does mean `extract_hubspot.py`'s first real-world test, against a live Private App token, would be yours. Read it before you trust it; it's a short, unexercised script.
5. **Run the reconciliation.**
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
6. **Read `result["summary"]` and `result["stage_mismatches"]` first.** The mismatch list is where the actual data-quality signal lives — every entry names both raw stage values and both canonical stages, so you can see immediately whether your org has one dominant mismatch pattern (as this one does) or a scattered mix that needs more granular triage.

## Known limitation, from this project's own real run

Fuzzy name+company matching without a third identifying field (phone, address, an external customer ID) will occasionally produce false-positive matches between two genuinely different people who happen to share a last name or a common company-name template — this project's own run hit exactly that, 7 times out of 403 candidate pairs (1.7%). See `output/reconciliation_findings.md` for the full breakdown. Raising `matching.fuzzy_threshold` trades this off against missing genuine no-email matches; there's no threshold that eliminates both failure modes at once. If your data has a better join key than name+company (a shared external ID, a phone number both systems capture), match on that first and treat fuzzy name+company as the last resort it is here.

## Running the tests

```bash
cd analysis/crm-reconciliation
python3 -m pytest tests/ -v
```
`tests/test_reconcile.py` covers `reconcile.py`'s matching/mismatch logic against the fixtures in `tests/fixtures/`; `tests/test_generate_salesforce_seed.py` covers this project's own seed generator (not relevant to a real adopter, per the note above).
