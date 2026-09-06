# Salesforce — configuration and seeding log

## The auth path, and why it looks the way it does

Getting a live connection took three attempts, each blocked by a different Salesforce platform default rather than a credential mistake — worth documenting honestly since it's real operational knowledge, not noise:

1. **Plain SOAP `login()`** (username + password + security token) — the textbook `simple-salesforce` setup. Failed: `INVALID_OPERATION: SOAP API login() is disabled by default in this org`. Salesforce disables this by default on new orgs as part of its phased retirement (full cutoff Summer '27).
2. **OAuth 2.0 username-password flow** via a Connected App (consumer key/secret) — the commonly-recommended replacement. Failed with `invalid_grant`: this flow is *also* blocked by default on orgs created Summer '23 or later, and the org-level toggle to re-enable it (Setup → OAuth and OpenID Connect Settings → "Allow OAuth Username-Password Flows") was itself locked/greyed out in this org.
3. **OAuth 2.0 JWT Bearer flow** (a self-signed certificate, no password grant at all) — this worked, after two more specific fixes: the running user had to be explicitly pre-authorized for the Connected App (Setup → the app → Manage → Edit Policies → "Admin approved users are pre-authorized" → Manage Profiles → add System Administrator), and the Connected App's OAuth scopes had to include "Perform requests at any time (refresh_token, offline_access)" in addition to "api" — without it, JWT auth fails with `invalid_request: refresh_token scope is required`.

Net result: `analysis/crm-reconciliation/salesforce_client.py` authenticates via JWT Bearer (`salesforce_jwt.key`/`.crt`, both gitignored and regenerable via `openssl req -x509 -sha256 -nodes -days 3650 -newkey rsa:2048 -keyout salesforce_jwt.key -out salesforce_jwt.crt -subj "/CN=growth-signal-integration"`). This isn't a workaround adopted under time pressure — it's the flow Salesforce itself now recommends over both alternatives, and it's the only one of the three not on a deprecation path.

## Object model choice

Seeded as **Lead** records, not Contact+Account+Opportunity. A real early-stage trade lead first appears in Salesforce as a Lead before qualification; modeling the full Account/Contact/Opportunity object graph would add complexity without adding to what this exercise demonstrates (cross-system identity matching and lifecycle-stage reconciliation), so Lead alone was the right scope call.

## Seeding approach

385 Lead records, derived from `data/generate_salesforce_seed.py`'s deterministic 3-way split of the same 769 trade/commercial customers already analyzed in `data/trade_signal.db`:

| Bucket | Count | Salesforce action |
|---|---|---|
| `salesforce_only` | 300 | New Lead, fabricated identity, no HubSpot presence |
| `cross_system` | 85 | New Lead, deliberately drifted from an already-live HubSpot contact (same email, varied name/company/phone, `Status` fixed to `Closed - Converted`) |
| `hubspot_only` | 103 | No Salesforce action — these stay real, live HubSpot-only contacts by design |

All emails use the `@example.com` domain (RFC 2606), the same convention as the rest of this project — including so that querying real seeded data can cleanly exclude the org's own pre-loaded sample Leads (Edna Frank, Rose Gonzalez, etc. — 22 of them in this org) via `WHERE Email LIKE '%@example.com'`.

## Verification

Read back live through the org, not assumed from the ingest script's return value:

```
SELECT COUNT() FROM Lead WHERE Email LIKE '%@example.com'  -->  385
```

Status breakdown (live-verified): 111 `Open - Not Contacted`, 86 `Working - Contacted`, 188 `Closed - Converted`. The 188 figure includes all 85 `cross_system` entries (fixed to `Closed - Converted` by design — see `docs/measurement-foundation.md`'s sibling reconciliation doc for why) plus roughly a third of the 300 `salesforce_only` entries, which land on each of the three stages by uniform random draw.

## What's still local, deliberately

`data/salesforce_seed.json` is the full local record of what was generated and intended for ingest, including the 103 `hubspot_only` entries that were never sent to Salesforce at all. Keeping it alongside the live org's actual state makes the reconciliation step's "what should match" and "what does match" independently checkable.
