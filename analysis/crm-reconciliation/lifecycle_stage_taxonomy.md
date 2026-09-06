# Unified Lifecycle-Stage Taxonomy

`config.yaml`'s `lifecycle_stage_map` is the single source of truth for this mapping — this doc is a readable rendering of it, not a separate definition. Any change to the taxonomy belongs in `config.yaml`, not here.

## Canonical stage → raw system values

| Canonical stage | HubSpot `lifecyclestage` (raw) | Salesforce `Lead.Status` (raw) |
|---|---|---|
| `lead` | `subscriber`, `lead` | `Open - Not Contacted` |
| `qualified` | `marketingqualifiedlead`, `salesqualifiedlead` | `Working - Contacted` |
| `opportunity` | `opportunity` | *(none — see gap below)* |
| `customer` | `customer` | `Closed - Converted` |

HubSpot's full standard `lifecyclestage` picklist also includes `evangelist` and `other`, neither of which maps to a canonical stage here — they're out of scope for this taxonomy because no live trade/commercial contact in this project's HubSpot account has ever been set to either value (every one currently reads `lead`, per the reconciliation findings).

## A real system-model gap, not a config gap

Salesforce's `Lead` object has no `Status` value between "being worked" (`Working - Contacted`) and "won" (`Closed - Converted`) — there is no Lead-level equivalent of HubSpot's `opportunity` stage. This isn't an oversight in `config.yaml`; it's how Salesforce's own data model works: a Lead is *converted* into an Account + Contact + Opportunity, at which point stage tracking moves onto the Opportunity object's own `StageName` picklist (`Prospecting`, `Qualification`, `Proposal/Price Quote`, `Negotiation/Review`, `Closed Won`, `Closed Lost`, in a default org). Because this project seeded Leads only (`docs/salesforce-setup.md` explains why), that finer-grained in-between state simply doesn't exist anywhere in the current Salesforce data to map to. The taxonomy reflects that honestly — `opportunity`'s Salesforce column is empty — rather than inventing a `Status` value that isn't a real picklist option in the org. If Fireclay's actual Salesforce implementation does use the Opportunity object (likely, for a real sales team), the real mapping would add a fifth canonical-stage row keyed off `Opportunity.StageName` rather than trying to force it into `Lead.Status`.

## System-of-record by stage transition

- **`lead` → `qualified`**: HubSpot is system-of-record. This transition is driven by marketing engagement signals (form fills, email activity, sample requests) that live natively in HubSpot; Salesforce has no visibility into *why* a lead should be considered "working" until a rep manually updates `Status`, which lags the actual signal.
- **`qualified` → `opportunity`/`customer`**: Salesforce becomes system-of-record from this point on. Once a rep is actively working a lead, the next state change (a call logged, a deal closed) happens inside Salesforce first, and — per this project's real data — HubSpot's `lifecyclestage` is not being updated to reflect it at all. Any lifecycle reporting that trusts HubSpot past this point is reporting stale state, as the findings doc's 100%-mismatch-rate result shows directly.
- **Ownership should flip at the handoff, not be split indefinitely.** The practical rule this data supports: HubSpot owns the record up through marketing-qualification, and the moment a Lead status changes in Salesforce, Salesforce's value should overwrite (not merely coexist with) HubSpot's `lifecyclestage` for that contact — see `systems-requirements-memo.md` for the specific sync mechanism this implies.
