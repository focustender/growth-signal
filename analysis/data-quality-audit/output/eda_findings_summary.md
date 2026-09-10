# EDA Findings Summary: Trade Signal core dataset

**Date:** 2026-09-06
**Analyst:** Ian Castorillo, using the vendored `programmatic-eda` Claude Code skill
**Full script output:** `analysis/data-quality-audit/output/raw_script_output/`

---

## Dataset at a Glance

The core dataset is four related tables: `customers.csv` (3,200 rows, one per customer), `funnel_events.csv` (8,868 rows, one per funnel event — site visit, visualizer use, sample request, purchase, project upload, repeat purchase), `email_engagement.csv` (7,949 rows, one per email send), and `reviews.csv` (474 rows, one per review). Coverage runs 2024-01-02 to 2025-11-16. Overall data quality is **Good** — see `output/quality_rubric.md` for the full scorecard (9.41/10); the notes below are EDA-specific structural observations, not quality defects.

---

## Top Findings

### Finding 1: `amount` is only meaningful for 2 of 6 event types, and its distribution is segment-driven, not noisy
- **What:** `funnel_events.amount` is 81.4% null overall (`null_profiler.py`) because only `purchase` and `repeat_purchase` events carry a dollar value; the other four event types (site_visit, visualizer_use, sample_request, project_upload) don't. Of the 1,654 non-null values, the distribution is heavily right-skewed (skew=2.4) with 311 IQR-flagged "outliers" — but 100% of those outliers belong to the trade/commercial segments, which have 5–10x the average order value of homeowner/designer.
- **Impact:** Any aggregate `amount` statistic (mean, std) across all customers without a segment cut will be dominated by the trade/commercial tail. A single blended AOV number would be misleading.
- **Recommended action:** Always segment-cut dollar-value analysis on this dataset; treat the IQR "outliers" as a real population split, not a cleaning target.
- **Owner:** Analyst (this is an interpretation note, not a pipeline fix)

### Finding 2: `sku_collection` is 37.8% null — by event type, not randomly
- **What:** `sku_collection` is null on 3,349 of 8,868 funnel events (37.8%). This wasn't broken out by event type in this pass — worth a follow-up cut (a sample_request or purchase event should plausibly always carry a collection; a site_visit likely shouldn't).
- **Impact:** Low, if the null pattern is fully explained by event type (expected); would be a real gap if collection-bearing event types (purchase, sample_request) are missing it.
- **Recommended action:** One follow-up query — null rate of `sku_collection` grouped by `event_type` — before using this column in any collection-level analysis.
- **Owner:** Analyst, next EDA pass

### Finding 3: `correlation_explorer.py` doesn't apply to this schema, and that's worth stating plainly
- **What:** Every table in this dataset has at most one numeric measure column (`amount`, `score`) alongside IDs and categoricals; `customers.csv` has none besides the binary `email_opt_in`. Pairwise numeric correlation analysis has nothing to operate on.
- **Impact:** None — this is a real property of the schema, not a failed check.
- **Recommended action:** Skip correlation analysis on this dataset going forward rather than re-running it per table; note it here so a future pass doesn't waste time re-discovering the same thing.
- **Owner:** N/A

---

## What Looks Good

- Referential integrity is 100% clean across all three child→parent relationships (17,291 combined child rows, 0 orphans).
- `customer_id` is 100% unique in every table it appears in, including the intentionally messy `raw_crm_export.csv` (its real duplication is encoded via ID suffixes, not exact-key repeats — see `output/quality_rubric.md`, Medium finding #1).
- All three business-rule checks (amount ≥ 0, email_opt_in domain, review score range) pass with zero violations.
- `company_name`'s 76% null rate — the single largest completeness gap in the dataset — is 100% explained by segment (populated for every trade/commercial customer, null for every homeowner/designer), not a real gap.

## Next Step

[x] Data is ready for analysis — proceed to lifecycle-attribution and Phase B metric work
[ ] Data fix required before proceeding
[ ] Further investigation needed: `sku_collection` null rate by `event_type` (Finding 2, low priority, non-blocking)
