# Dashboard Specification: Trade Signal Lifecycle Dashboard

## What this is

A filled dashboard-requirements specification, using the vendored `dashboard-specification` skill's template, built entirely from real metrics already computed elsewhere in this repo — every row in the spec's Metrics table traces to a specific `analysis/*/output/` file. Full spec: `output/dashboard_spec.md`.

## What this isn't

Not a built dashboard, and not pretending to be one. This project deliberately has no BigQuery/Tableau/dbt/Looker stack (see root `README.md`) — standing one up for a synthetic dataset with no live pipeline behind it would be theater, not evidence. This document demonstrates the requirements-gathering and layout-design thinking a real dashboard build would start from, against this project's own real numbers, without claiming a tool was deployed that wasn't.

## How it works

Filled by hand against the vendored `assets/dashboard_spec_template.md`, cross-referencing every metric to the analysis folder that already computed and verified it (semantic model for definitions, cohort-analysis for retention, business-metrics for revenue-per-customer, lifecycle-attribution for the platform-vs-commercial divergence, crm-reconciliation for the live stage-mismatch alert).

## Running it yourself

There's no script here — this is a filled document, not an engine. Read `output/dashboard_spec.md` directly.
