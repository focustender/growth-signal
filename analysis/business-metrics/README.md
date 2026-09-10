# Business Metrics: AOV and Revenue per Customer by Segment

## What this is

A small, original, tested e-commerce unit-economics engine (`ecommerce_metrics.py`), built because the vendored `business-metrics-calculator` skill's shipped script doesn't cover this project's business model — see "What this isn't" below. Real result: **designer customers convert at the highest rate (60.7%) of any segment but generate the second-lowest revenue per customer ($791); trade customers convert at roughly half that rate (34.2%) but generate over 7x designer's revenue per customer ($5,782)**, driven by a $13,670 average order value vs. designer's $1,086. Full write-up: `output/ecommerce_metrics_findings.md`.

## What this isn't

Not an adaptation of the vendored `business-metrics-calculator` skill's shipped script. That skill's `SKILL.md` says its script covers "SaaS: MRR, ARR... for e-commerce: GMV, AOV, conversion rate, ROAS... use `scripts/saas_metrics.py` or adapt for other models" — but `saas_metrics.py`'s actual CLI (`--mrr`, `--arpu`, `--monthly-churn`, `--cac`, `--dau`/`--mau`, `--ltv`) has no AOV or GMV path at all, and its `references/metric_definitions.md` never mentions e-commerce metrics either. Rather than force this project's purchase data into a SaaS subscription shape, `ecommerce_metrics.py` is new, original, tested code — the same "vendor what fits, build what doesn't" judgment call as choosing not to force-fit the vendored `metrics_report_template.md` (also SaaS-shaped) in the findings write-up.

## How it works

1. **`ecommerce_metrics.py`** — one function, `segment_metrics(customers, orders)`, taking plain dicts (`{customer_id, segment}` and `{customer_id, amount}`) with no Fireclay-specific field names. Computes conversion rate, AOV, total revenue, and revenue-per-customer per segment. Tested in `tests/test_ecommerce_metrics.py` (4/4 passing): AOV correctness, segment independence, zero-purchase customers still counting toward conversion/revenue-per-customer, and a zero-order segment not crashing.
2. **`run_ecommerce_metrics.py`** — the Fireclay-shaped wiring layer (same role as `run_attribution.py`/`run_feasibility_check.py` play for their sibling engines), pulling `customers`/`funnel_events` from `trade_signal.db` and writing `output/metrics_report.json`.

## Adapting this to your own data

`segment_metrics()` takes any iterable of customer/order dicts — point it at a different table or CSV with the same two field shapes and it works unchanged.

## Running it yourself

```bash
cd analysis/business-metrics
python3 run_ecommerce_metrics.py
python3 -m pytest tests/
```
