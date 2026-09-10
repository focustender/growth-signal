# Semantic Model: Funnel Metric Definitions

## What this is

The funnel-stage definitions from `docs/measurement-foundation.md` — previously a prose table — formalized into the vendored `semantic-model-builder` skill's YAML schema (dbt Semantic Layer conventions), covering all 6 funnel stages as metrics, the 4 dimensions used throughout this project's analyses, and the core entities and their relationships. All three files validate cleanly against the vendored `model_yaml_validator.py --strict`.

## Why this matters

This directly answers the JD's "clear conversion definitions" line: every metric here states its exact filter/grain, and — critically — documents the real gotchas already discovered the hard way elsewhere in this project. `project_rate` explicitly calls out that its denominator must be filtered to trade/commercial only (homeowner/designer never trigger `project_upload`). `purchase_rate` documents that this project reports it two different, both-valid ways (share of all customers vs. share of sampled customers) and that conflating them is a real risk. `repeat_purchase_rate` documents the cohort-anchoring mistake `analysis/cohort-analysis/` made and fixed (signup-date cohorting produces nonsensical >100% rates; first-purchase-date is correct).

## How it works

`metric_definition.yaml`, `dimension_definition.yaml`, and `entity_definition.yaml` follow the vendored templates in `.claude/skills/semantic-model-builder/assets/` exactly (generated via `metric_template_generator.py`, then filled by hand against this project's real data and real prior findings, not invented).

## Adapting this to your own model

Nothing here is Fireclay-specific in structure — swap the `meta.data_source`, `expr`, and `possible_values` fields for your own tables and this schema (and the vendored validator) work unchanged.

## Running it yourself

```bash
python3 .claude/skills/semantic-model-builder/scripts/model_yaml_validator.py --input analysis/semantic-model/metric_definition.yaml --strict
python3 .claude/skills/semantic-model-builder/scripts/model_yaml_validator.py --input analysis/semantic-model/dimension_definition.yaml --strict
python3 .claude/skills/semantic-model-builder/scripts/model_yaml_validator.py --input analysis/semantic-model/entity_definition.yaml --strict
```
