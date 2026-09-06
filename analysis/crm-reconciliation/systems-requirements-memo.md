# Systems Requirements Memo — HubSpot ↔ Salesforce Lifecycle Sync

**Purpose:** the Lifecycle Growth & Analytics Manager JD asks for a partner on "HubSpot–Salesforce data quality, lifecycle-stage alignment, and the systems requirements needed for better growth decisions." This memo answers that literally, grounded in the real reconciliation run (`output/reconciliation_findings.md`) rather than generic CRM-integration advice.

## The finding this memo is built on

Of 85 real contacts that exist in both live systems, 100% show HubSpot's `lifecyclestage` reading `"lead"` while Salesforce's `Lead.Status` reads `"Closed - Converted"`. This is not a scattered assortment of mismatches needing case-by-case triage — it is one mechanism, failing the same way every single time: **HubSpot's `lifecyclestage` field is never written to after initial contact creation.** The original import set five custom properties and left HubSpot's own standard lifecycle field untouched; nothing since has updated it either. Salesforce's `Lead.Status`, meanwhile, is the only place in either system where a contact's real progression is currently visible. A dashboard, a segment, or an automation built on HubSpot's `lifecyclestage` today is reading a field that has been effectively frozen since import — for these 85 records, always at "lead," never once reflecting what Sales already knows happened.

## What would actually need to change

Not "buy an integration platform." The gap is specific — one field, one direction, one trigger point — so the fix should be too:

1. **A Salesforce-side Flow (or Process Builder equivalent) on `Lead.Status` change**, firing whenever a Lead's `Status` transitions to `Working - Contacted` or `Closed - Converted`. This is a native, no-code Salesforce automation — no new platform, no new vendor.
2. **The Flow calls HubSpot's Contacts API** (`PATCH /crm/v3/objects/contacts/{id}`) to set `lifecyclestage` on the matching HubSpot contact, using email as the join key — the same field `reconcile.py` already uses for exact matching in this project, so the join logic doesn't need to be invented, only operationalized as a live webhook instead of a batch script.
3. **The mapping is exactly `config.yaml`'s `lifecycle_stage_map`, inverted for one direction of travel**: `Working - Contacted` → `marketingqualifiedlead`/`salesqualifiedlead` (pick one canonical HubSpot value as the outbound target — `salesqualifiedlead` is the more accurate one, since by this point a human, not a marketing score, has qualified the lead), `Closed - Converted` → `customer`. No `opportunity` write-back is needed from Lead-level automation, since — per `lifecycle_stage_taxonomy.md` — a plain Lead never reaches that state; if Fireclay's real org tracks Opportunities, a second, near-identical Flow on `Opportunity.StageName` would cover that stage instead.
4. **This is one-directional by design, not an oversight.** The taxonomy memo already establishes that Salesforce becomes system-of-record once a lead is being actively worked — so the sync should overwrite HubSpot's `lifecyclestage`, not merge or flag a conflict. A bidirectional sync here would just recreate the ambiguity this reconciliation exists to resolve. HubSpot should keep writing the fields it owns (segment, source channel, signup date); Salesforce should own writing this one field going forward.

## Why this, not a platform purchase

A generic "buy an integration tool" (Zapier, Workato, a native AppExchange connector) would solve this too, eventually — but it would also solve problems this data doesn't show exist yet (bidirectional company-name reconciliation, multi-object sync, real-time two-way conflict resolution). The actual failure mode found here is narrow: one field, one direction, updated at exactly two trigger points. A native Salesforce Flow plus one HubSpot API call handles 100% of the observed gap with no new recurring vendor cost and no new system to maintain access/auth for. If a broader sync need surfaces later (e.g., once Opportunities are in scope, or once HubSpot-side changes need to flow back to Salesforce), that is the point to reconsider a platform — not before there's a second failure mode to justify one.

## Rollout note

Before turning this on for all 385 seeded + any real future Leads, backfill the 85 already-mismatched contacts once, manually or via a one-time script using this project's own `reconcile.py` output (`output/reconciliation_report.json`'s `stage_mismatches` list already contains the exact HubSpot ID → correct target stage for each) — otherwise the Flow only fixes the drift going forward and this reconciliation's own 85 findings would remain permanently stale.
