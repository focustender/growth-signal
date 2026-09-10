# Claude Code skills in this project

## Original to this project

- **`lifecycle-pulse/`** — built for Trade Signal specifically: a week-over-week lifecycle/funnel digest by segment with anomaly flags and an optional live HubSpot/Salesforce cross-reference. See its own `README.md`.

## Vendored, third-party

The following 13 skills are vendored, unmodified, from [nimrodfisher/data-analytics-skills](https://github.com/nimrodfisher/data-analytics-skills) (as of 2026-09; that repo has no LICENSE file, so this is used here for personal workflow purposes on a work-sample project, not represented as this project's own IP):

- `data-quality-audit`
- `metric-reconciliation`
- `programmatic-eda`
- `semantic-model-builder`
- `business-metrics-calculator`
- `cohort-analysis`
- `time-series-analysis`
- `root-cause-investigation`
- `analysis-qa-checklist`
- `visualization-builder`
- `dashboard-specification`
- `data-narrative-builder`
- `insight-synthesis`

Each folder is copied as-is (its numeric category-prefix directory stripped) from its source path in that repo. They aren't edited in place — where a vendored skill's script has a real limitation discovered while using it on this project's data (for example, `business-metrics-calculator`'s shipped script only covers SaaS metrics, not e-commerce, despite its description mentioning both), that limitation is noted in whichever analysis folder used it, not patched into the vendored file itself.

This project's actual differentiators — the CRM reconciliation engine, the power-analysis tool, the lifecycle-attribution engine, the Lifecycle Pulse skill, and the live Shopify fix — are original work documented under `analysis/` and `docs/`, separate from this vendored set.
