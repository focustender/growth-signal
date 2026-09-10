# Dashboard Specification: Trade Signal Lifecycle Dashboard

**Dashboard name:** Trade Signal Lifecycle Dashboard
**Owner:** Lifecycle Growth & Analytics
**Date:** 2026-09-06
**Status:** Draft — a requirements specification, not a built dashboard. This project deliberately has no BigQuery/Tableau/dbt/Looker stack (see root `README.md`); this document demonstrates dashboard-requirements thinking against real metrics already computed elsewhere in this repo, rather than standing up a BI tool for a synthetic dataset with no live pipeline behind it.

---

## Purpose

**Primary question this dashboard answers:** Where in the lifecycle funnel is friction concentrated right now, and which segment or channel should get attention next?

**Primary audience:** Lifecycle Growth & Analytics Manager (weekly self-review), Senior Manager of Integrated Marketing (monthly readout)
**Secondary audience:** Trade sales team (channel-level context for the trade-show stall finding)
**Usage frequency:** Weekly for the owner; monthly for the secondary audience

---

## Metrics

| Metric | Definition | Source table | Owner | Refresh | Acceptable lag |
|---|---|---|---|---|---|
| Funnel stage rates (interest/sample/project/purchase/repeat/advocacy) | See `analysis/semantic-model/metric_definition.yaml` — the canonical definitions this dashboard would read from | `customers`, `funnel_events`, `reviews` | Lifecycle Growth & Analytics | Daily | 24h |
| Trade-show single-sample stall rate | % of single-sample trade-show trade leads never reaching project/purchase | `customers`, `funnel_events` | Lifecycle Growth & Analytics | Weekly | 7 days |
| Repeat-purchase rate by segment | See `analysis/cohort-analysis/` — anchored on first-purchase date, not signup date | `funnel_events` | Lifecycle Growth & Analytics | Weekly | 7 days |
| Revenue per customer by segment | See `analysis/business-metrics/` | `customers`, `funnel_events` | Lifecycle Growth & Analytics | Weekly | 7 days |
| Platform-metric-vs-commercial-outcome divergence by email program | See `analysis/lifecycle-attribution/` — reported at 90-day window minimum for `welcome` specifically (see that metric's known window-sensitivity) | `email_engagement`, `funnel_events` | Lifecycle Growth & Analytics | Weekly | 7 days |
| HubSpot↔Salesforce stage-mismatch rate | See `analysis/crm-reconciliation/` | HubSpot + Salesforce (live) | Lifecycle Growth & Analytics + Technology | Daily | 24h |

---

## Layout specification

### Page 1: Funnel Health (weekly self-review)

**Primary question:** Is the funnel moving in the right direction week over week, and where's the biggest single point of friction?

| Position | Chart type | Metric | Dimensions | Filters |
|---|---|---|---|---|
| Top-left (hero) | KPI card | Overall stall rate, trade-show single-sample leads | — | Trailing 90 days |
| Top-right | KPI card | HubSpot↔Salesforce stage-mismatch rate | — | Live |
| Center | Line chart | Trade-show stall rate over time | Monthly | Date range, with the known small-n caveat (see `analysis/time-series/README.md`) surfaced as an on-chart annotation below ~10 leads/month, not hidden |
| Bottom-left | Bar chart | Conversion rate by segment | By segment | — |
| Bottom-right | Bar chart | Revenue per customer by segment | By segment | — |

**Default time range:** Trailing 90 days
**Sticky filters:** Segment, acquisition channel — apply to every chart on this page

### Page 2: Lifecycle Programs (monthly readout)

**Primary question:** Which email programs' platform metrics actually track commercial outcomes, and which repeat-purchase levers have the most leverage?

| Position | Chart type | Metric | Dimensions | Filters |
|---|---|---|---|---|
| Top-left (hero) | KPI card | % of programs where platform-metric rank and commercial-outcome rank disagree (rank shift ≠ 0) | — | 90-day window (the window `welcome`'s finding says matters) |
| Top-right | Table | Rank-shift table, all 6 programs | By program | — |
| Center | Heatmap | Repeat-purchase retention by first-purchase cohort | Cohort month × period, faceted by segment | Segment |
| Bottom | Bar chart | Ever-repeat-purchase rate by segment | By segment | — |

**Default time range:** Trailing 12 months
**Sticky filters:** None — this page is deliberately unfiltered so month-to-month comparisons stay apples-to-apples

---

## Interactivity

| Feature | Required | Notes |
|---|---|---|
| Date range filter | Yes | Default trailing 90 days (Page 1) / 12 months (Page 2) |
| Segment filter | Yes | homeowner / designer / trade / commercial |
| Drill-down | Yes | Funnel-stage KPI cards drill into the underlying customer list, filterable by the same segment/channel filters |
| Cross-filter | Yes | Selecting a segment on Page 1's bottom-left chart filters the hero KPI and the center line chart |
| Export / download | Yes | CSV, for the underlying customer-list drill-downs specifically — not the aggregate charts, which should stay read-only to avoid someone screenshotting a stale export as if it were live |
| Alerts | Yes | Trade-show stall rate crossing ±10pp week-over-week; HubSpot↔Salesforce mismatch rate exceeding 5% (currently at 100% on the 85 genuine live matches — see `analysis/crm-reconciliation/`, so this alert would fire immediately on first real deployment, which is itself informative) |

---

## Access and governance

**Access level:** Team-only (Lifecycle Growth & Analytics + Integrated Marketing leadership)
**Sensitive data present:** Yes — customer-level drill-downs include names/emails once wired to the live HubSpot/Salesforce systems this project already integrates with; the synthetic dataset itself has no real PII (RFC 2606 `@example.com` addresses throughout)
**Row-level security needed:** No — segment/channel filtering is sufficient; no sub-team needs restricted visibility within Lifecycle Growth & Analytics
**Who approves access requests:** Senior Manager, Integrated Marketing

---

## Data and infrastructure

**BI tool:** Not selected — this project intentionally has no BigQuery/Tableau/dbt stack (see root `README.md`); a real deployment would likely start with whatever BI tool Fireclay's Technology team already standardizes on, rather than this document prescribing one
**Connection:** `trade_signal.db` (SQLite) for funnel/purchase data; live HubSpot + Salesforce connections for the CRM-reconciliation page, following the same auth pattern already built and documented in `docs/salesforce-setup.md`/`docs/hubspot-setup.md`
**Refresh schedule:** Daily for CRM data, weekly for funnel/purchase metrics (matches the cadence in the Metrics table above)
**Data owner sign-off:** Not applicable — draft specification, no live stakeholder review yet

---

## Acceptance criteria

- [x] All metrics match definitions in `analysis/semantic-model/metric_definition.yaml`
- [ ] Default view loads in < [n] seconds — not testable without a real BI tool deployment
- [x] Numbers cross-checked against source query output — every number in this spec traces to a specific `analysis/*/output/` file already computed and verified elsewhere in this repo
- [ ] Stakeholder review completed — this is a draft, not a reviewed spec
- [x] Owner confirmed — Lifecycle Growth & Analytics, not "analytics team"
