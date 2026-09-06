# Task 3 report: Salesforce client + live seed ingestion

## Status: BLOCKED (authentication/org-configuration, not credential values)

## What was done

1. Read Task 3 in full from `docs/superpowers/plans/2026-09-06-crm-reconciliation.md` (lines 430-541).
2. Inspected the real `data/salesforce_seed.json` (300 `salesforce_only`, 85 `cross_system`, 103 `hubspot_only` — matches Task 2's documented output exactly). Confirmed field names against what Task 3's code expects:
   - `salesforce_only` entries: keys are `customer_id`, `first_name`, `last_name`, `company`, `email`, `segment`, `salesforce_stage` — matches the plan's assumptions exactly (`entry["last_name"]`, `entry.get("first_name")`, `entry["company"]`, `entry["email"]`, `entry["salesforce_stage"]` all present, no adaptation needed).
   - `cross_system` entries: `salesforce_record` sub-object has `Email`, `Name`, `Company`, `Status`, `CreatedDate`, `Phone` — matches the plan's assumptions exactly (`Name`, `Company`, `Email`, `Status` all present).
   - Only cosmetic observation, not a structural mismatch: `salesforce_record["Name"]` is inconsistently cased across entries (some `"nancy haddad"`, some `"Maria Johnson"`). The plan's `.split()`-based name parsing works correctly either way (LastName/FirstName still split correctly), it just carries through the seed's casing as-is. Not corrected, since it's a data-fidelity concern in Task 2's already-committed/reviewed output, not a Task 3 bug.
   - `salesforce_only.salesforce_stage` values found: `Open - Not Contacted`, `Working - Contacted`, `Closed - Converted`. `cross_system.salesforce_record.Status` values found: `Closed - Converted` only. These are exactly the standard default Salesforce Lead Status picklist values in most orgs, which was a good sign for the ingestion — but ingestion never reached the point of testing that, per below.
3. Installed `simple-salesforce` (was missing; `python-dotenv` was already present in the environment) via `pip3 install simple-salesforce python-dotenv`. Both already listed correctly in the repo's `requirements.txt`.
4. Wrote `analysis/crm-reconciliation/salesforce_client.py` exactly as specified in the plan (no adaptation needed — field-name inspection in step 2 found no mismatch).
5. Wrote `analysis/crm-reconciliation/salesforce_seed_ingest.py` exactly as specified in the plan (no adaptation needed for the same reason).
6. Ran `cd analysis/crm-reconciliation && python3 salesforce_seed_ingest.py` for real, against the live org using the credentials in `.env`.

## What happened

The run failed at the authentication step, before any `Lead.create()` call was made — so **zero Lead records were created**, no partial writes to clean up.

Exact (non-secret) error from `simple_salesforce`:

```
simple_salesforce.exceptions.SalesforceAuthenticationFailed: Authentication failed (code: INVALID_OPERATION): SOAP API login() is disabled by default in this org. Contact the org administrator to enable SOAP API login().
```

## Diagnosis

This is **not** a wrong-username/password/security-token problem — the error code (`INVALID_OPERATION`) and message are Salesforce's own, and they're distinct from the classic `INVALID_LOGIN: Invalid username, password, security token` credential-mismatch error the plan anticipated. I confirmed via research that this is a known, deliberate Salesforce platform change: newly-provisioned orgs (including fresh Developer Edition orgs, which is what this is) now ship with SOAP-based `login()` disabled by default, as part of Salesforce's broader retirement of SOAP API `login()` ahead of a hard cutoff in the Summer '27 release (already fully unavailable in API v65.0+; this environment is using v59.0 via `simple_salesforce`'s default, which is below that cutoff). `simple_salesforce`'s username/password/token authentication path (the one `salesforce_client.py` uses, per the plan) goes through this same SOAP `login()` call — there's no way to route the username/password/token flow around it.

This falls squarely under "credential/auth issue → report BLOCKED, don't guess at fixing it" per the task instructions, even though the specific defect (an org-level API-access toggle, not a wrong secret value) differs from the example given in the plan. Enabling it requires an org-admin action inside Salesforce Setup, which touches org security posture — not something to change unilaterally on the user's behalf.

## What would unblock this (for Ian, not attempted)

Two paths, in order of least to most future-proof:

1. **Quick unblock (works today, but on a deprecating path):** In Salesforce Setup, Quick Find → "User Interface" → API Settings → enable "Enable SOAP API login()", then save. This should let the existing `.env` credentials (username/password/security token) work exactly as `salesforce_client.py` and the plan assume, with no code changes.
2. **More durable path (recommended if this seeding is meant to be re-run later, given SOAP login()'s scheduled full retirement):** Set up a Connected App in Salesforce Setup with OAuth enabled, generate a Consumer Key/Secret, and switch `salesforce_client.py` to `simple_salesforce`'s OAuth 2.0 username-password flow (`consumer_key`/`consumer_secret` params) instead of raw SOAP login. This needs new credential material (consumer key/secret) added to `.env`, which only Ian can generate from Salesforce Setup.

No attempt was made to change org security settings or fabricate/guess new credential values.

## Deviations from the plan

- No code deviation: both `salesforce_client.py` and `salesforce_seed_ingest.py` were written verbatim from the plan, since the field-name inspection in Step 2 found the real seed JSON already matches the plan's assumed shape exactly.
- Execution deviation: ingestion did not run to completion. Steps 8 (live verification query), 9 (`docs/salesforce-setup.md`), and 10 (commit) were **not** performed, per the task's own instruction to stop and report rather than work around an authentication block. `docs/salesforce-setup.md` was intentionally not written, since it would need to describe live-seeded data that does not yet exist.

## Current repo state

- `analysis/crm-reconciliation/salesforce_client.py` and `analysis/crm-reconciliation/salesforce_seed_ingest.py` exist in the working tree, untracked, ready to run as-is once the org's SOAP login is enabled (or the client is switched to OAuth per path 2 above).
- Nothing was staged or committed. `.env` was not touched, not read for its values beyond what `os.environ` needed at runtime, and confirmed absent from `git status` output.
- Live Salesforce Lead count: **0** created by this task (auth failed before any writes).

## Commit hash

None — no commit was made, per the task's instruction to only commit after live verification succeeds.
