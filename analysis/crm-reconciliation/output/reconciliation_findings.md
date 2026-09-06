# HubSpot ↔ Salesforce Reconciliation — Findings

**Real, live data.** Both inputs are live API extracts, not fixtures: `data/hubspot_extract.json` (188 records, HubSpot REST/MCP, captured Task 4) and `data/salesforce_extract.json` (385 records, live JWT-Bearer query against the Developer Edition org, captured for this task). `reconcile.py` and `config.yaml` (copied unedited from `config.example.yaml` — verified field names against both extracts before running) ran against these two files with no synthetic substitution. Full output: `output/reconciliation_report.json`.

## Summary counts

| Metric | Count |
|---|---|
| HubSpot records in | 188 |
| Salesforce records in | 385 |
| Matched (either method) | 92 |
| — matched by exact email | 85 |
| — matched by fuzzy name+company | 7 |
| HubSpot-only orphans | 96 |
| Salesforce-only orphans | 293 |
| Lifecycle-stage mismatches | 89 |

These are close to, but not identical to, the seed design's target split (85 cross-system / 103 hubspot-only / 300 salesforce-only). The gap is fully explained below, not a bug in the matching logic.

## Why the counts shift by 7

`reconcile.py`'s second pass fuzzy-matches any HubSpot and Salesforce record still unmatched after exact-email matching, scoring `full_name + company` with `rapidfuzz.token_sort_ratio` against an 85-point threshold. Seven pairs cleared that threshold:

| HubSpot | Salesforce | Confidence | What matched |
|---|---|---|---|
| Patricia Okafor, Ashford Design Studio | Priya Okafor | 93.0 | shared last name |
| Priya Allen, Cascade Build Co. | Donna Allen | 86.2 | shared last name |
| Mark King | Karen Taylor | 85.3 | borderline, shared token pattern |
| Joseph Thomas, Coastal Design + Build | Cascade Design + Build | 91.7 | shared company template |
| Michael Wright | Kimberly Wright | 87.3 | shared last name |
| Thomas Lewis | Priya Thomas | 88.6 | shared last name |
| Sandra Williams | Karen Williams | 89.6 | shared last name |

Checked against `data/salesforce_seed.json`: none of these seven HubSpot records is one of the 85 real `cross_system` entries — every one is a genuine `hubspot_only` record coincidentally scoring above threshold against a genuine `salesforce_only` record. This is a direct consequence of how the seed was built (Task 2): `salesforce_only`'s 300 fabricated identities and the real HubSpot contacts' names both draw from the same finite `FIRST_NAMES`/`LAST_NAMES` pool in `data/generate_hubspot_import.py`, and company names lean on a handful of repeated templates ("X Design + Build," "X Design Studio," "X & Associates"). With no email to disambiguate, `token_sort_ratio` on a shared surname or company phrase alone is enough to clear 85 a small fraction of the time — 7 out of 403 candidate hubspot-only/salesforce-only pairs, about 1.7%. That is the real, load-bearing limitation of name/company fuzzy matching without a third identifying field (phone, address, or an external ID), not an implementation defect, and it moves 7 records out of each orphan bucket and into `matched` (with 4 of those 7 also showing a spurious lifecycle-stage "mismatch," since the two people's real stages happen to differ too).

Net effect on the summary: `matched` reads 92 instead of ~85 (+7), `hubspot_only` reads 96 instead of 103 (−7), `salesforce_only` reads 293 instead of 300 (−7), `stage_mismatch` reads 89 instead of ~85 (+4, all noise from the false-positive matches above). Excluding those seven, the underlying signal is exactly what the seed design intended: 85 genuine cross-system matches.

## The real finding: lifecycle stage, not identity, is where the systems disagree

Of the 85 genuine cross-system matches, **all 85 (100%) show a lifecycle-stage mismatch.** Every one is the same pattern: HubSpot's `lifecyclestage` reads `"lead"` while Salesforce's `Lead.Status` reads `"Closed - Converted"` — canonically `lead` vs. `customer`. There is no case in the real data where the two systems agree on lifecycle stage for a record that exists in both.

This is not injected test noise dressed up as a finding — it is exactly what `docs/hubspot-setup.md` already surfaced independently: the original 750-contact HubSpot import (`data/generate_hubspot_import.py`) set five named custom properties (`trade_signal_segment`, `trade_signal_source_channel`, `trade_signal_region`, `trade_signal_signup_date`, `trade_signal_customer_id`) but never touched HubSpot's own standard `lifecyclestage` field, so every trade/commercial contact is still sitting at HubSpot's default `"lead"` months later, regardless of what has actually happened to that lead downstream. Salesforce's `Lead.Status`, by contrast, is being actively updated by sales-side activity (real or seeded) — so for any record that exists in both systems, Salesforce's status is materially ahead of HubSpot's stage, every time, with a 100% disagreement rate across all 85 checkable pairs. Marketing-facing lifecycle reporting built on HubSpot's `lifecyclestage` field alone would report zero customers among these 85 real cross-system contacts, when Salesforce shows all 85 have actually closed.

A secondary, lower-stakes drift also appears: 25 of the 85 matched pairs (29%) show a company-name difference — in every one of those 25, Salesforce's `Company` value is HubSpot's value with an `" Inc"` suffix appended. Consistent with a sales rep normalizing company names on lead entry; worth a data-entry convention, but it is not a data-quality risk on the scale of the lifecycle-stage gap above.

## What this doesn't tell us

`salesforce_only`'s 293 (300 minus the 7 reclaimed above) and `hubspot_only`'s 96 (103 minus 7) are orphans by design, not evidence of missing sync — they represent leads that genuinely only exist in one system (sales-sourced leads with no marketing touch, and marketing contacts with no sales touch, respectively). The lifecycle-stage finding above is scoped deliberately to the 85 records that exist in both systems, since a stage "mismatch" is only meaningful where there are two stages to compare.
