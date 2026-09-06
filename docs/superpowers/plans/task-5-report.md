# Task 5 Report — Salesforce extractor + real reconciliation run + write-ups

**Commit:** `ca7e18995fcdb56ce8b47e0d11134cef9e57ed9a` — "Run real HubSpot/Salesforce reconciliation and write up findings"

## What was done

1. Read Task 5 in full from `docs/superpowers/plans/2026-09-06-crm-reconciliation.md` (lines 654–747).
2. Wrote `analysis/crm-reconciliation/extract_salesforce.py` verbatim from Step 1's code block, including the `WHERE Email LIKE '%@example.com'` filter (kept as-is, per instructions).
3. Ran it for real: `python3 extract_salesforce.py` → wrote `data/salesforce_extract.json` with **385 records**, matching Task 3's live-verified count exactly. Status breakdown in the extract: 111 `Open - Not Contacted`, 86 `Working - Contacted`, 188 `Closed - Converted` — identical to Task 3's live-verified numbers.
4. Copied `config.example.yaml` → `config.yaml`. Verified field names against real data first: `data/hubspot_extract.json` has `email`/`firstname`/`lastname`/`company`/`lifecyclestage`/`trade_signal_signup_date`; `data/salesforce_extract.json` has `Email`/`Name`/`Company`/`Status`/`CreatedDate`. Both match `config.example.yaml` exactly — `diff` confirmed the copy is byte-identical, no edits needed.
5. Ran the real reconciliation per Step 4's exact code (load both extracts + `config.yaml`, call `reconcile()`, write `output/reconciliation_report.json`, print summary).
6. Sanity-checked the summary against the ~85/300/103 expectation (see Deviations below) — investigated the gap before writing anything up, per instructions.
7. Wrote `output/reconciliation_findings.md` using the real summary numbers, in `docs/measurement-foundation.md`'s numbers-forward tone. Confirmed from the real data (not assumed) that the dominant mismatch is HubSpot `lifecyclestage` = `"lead"` vs. Salesforce `Lead.Status` = `"Closed - Converted"` on **100%** of the 85 genuine cross-system matches.
8. Wrote `lifecycle_stage_taxonomy.md` — a table sourced directly from `config.yaml`'s real `lifecycle_stage_map`, plus a paragraph on system-of-record ownership per stage transition and an explicit note on the real Lead-vs-Opportunity taxonomy gap.
9. Wrote `systems-requirements-memo.md` — answers the JD's "systems requirements" phrase with a specific proposal (a Salesforce Flow on `Lead.Status` change, calling HubSpot's Contacts PATCH API to update `lifecyclestage`), grounded in the real 100%-mismatch finding, not generic integration-tool advice.
10. Wrote `analysis/crm-reconciliation/README.md` after reading `visualizer/README.md` for tone. Covers what the tool does, how `config.yaml` works, and a genuine "adapt this to your own org" walkthrough — including the honest disclosure that `extract_hubspot.py` was never actually executed in this project (the live `hubspot_extract.json` came from Claude Code's MCP connector instead, per the Task 4 commit `6de5658`).
11. Staged and committed exactly the 8 files specified in Step 11 — verified via `git status --porcelain` before and after `git add` that nothing extra was included, and grepped the staged files for credential-shaped strings before committing (none found; the one hit was descriptive prose in the README, not a real secret).
12. This report.

## Real reconciliation summary (from `output/reconciliation_report.json`)

| Metric | Count |
|---|---|
| Matched (total) | 92 |
| — by exact email | 85 |
| — by fuzzy name+company | 7 |
| HubSpot-only | 96 |
| Salesforce-only | 293 |
| Stage mismatches | 89 |

Of the 85 email-matched pairs, **all 85 (100%)** show the mismatch: HubSpot canonical `lead` vs. Salesforce canonical `customer` (raw: `"lead"` vs. `"Closed - Converted"`), confirmed by reading the real `field_diffs`/`stage_mismatches` output, not assumed.

## Deviation from the ~85/300/103 expectation, and why

The plan's Step 6 explicitly anticipated this exact failure mode ("a fuzzy match fires unexpectedly for a hubspot_only/salesforce_only pair that shouldn't match") and instructed investigating before treating the real numbers as final. I did:

- Extracted the 7 fuzzy-matched pairs from the report and cross-referenced their HubSpot IDs against `data/salesforce_seed.json`'s 85 real `cross_system` entries (by email). **None of the 7 is a real cross-system record** — all 7 are coincidental matches between a genuine `hubspot_only` record and a genuine `salesforce_only` record.
- Root cause: Task 2's seed generator draws `salesforce_only`'s 300 fabricated identities from the same `FIRST_NAMES`/`LAST_NAMES` pool used to generate the real HubSpot contacts (`data/generate_hubspot_import.py`), and reuses a small set of company-name templates ("X Design + Build," "X Design Studio," "X & Associates") on both sides. With no email to disambiguate, `rapidfuzz.token_sort_ratio` on `full_name + company` alone clears the 85-point threshold for 7 of 403 candidate cross-pool pairs (1.7%) purely on a shared surname or company phrase — e.g. "Patricia Okafor, Ashford Design Studio" vs. "Priya Okafor" scoring 93.0.
- This shifted `matched` from ~85 to 92 (+7), `hubspot_only` from 103 to 96 (−7), `salesforce_only` from 300 to 293 (−7), and `stage_mismatch` from ~85 to 89 (+4, since 4 of the 7 false-positive pairs also happened to have differing real stages — noise, not signal).
- This is a modest, fully explainable difference (1.7% of candidate pairs), not a bug in `reconcile.py`'s matching logic or a wrong `config.yaml`. It is reported honestly in `output/reconciliation_findings.md` (with the full 7-row breakdown and root-cause explanation) and in `README.md`'s "Known limitation" section, rather than forced to hit the exact expected numbers. The underlying seed-design signal — exactly 85 genuine cross-system matches, 100% showing the lead/customer stage mismatch — came through completely intact once the 7 false positives were isolated and excluded from the headline finding.

No other deviations from the plan's literal text. `extract_salesforce.py` was written and run exactly as given; `config.yaml` needed no edits; all 8 specified files were committed and no others.
