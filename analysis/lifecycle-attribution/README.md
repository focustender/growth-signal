# Lifecycle Attribution: Platform Metric vs. Commercial Outcome

## What this is

A small engine that answers the JD's own line — *"know the difference between a platform metric and a commercial outcome"* — directly, against this project's real email-engagement and funnel-event data. For each email program, it compares the platform metric (open/click rate) to the commercial outcome (purchase value, engaged vs. unengaged recipients) and flags where the two disagree on which program matters most.

Real results from this project's own data: `welcome`'s commercial signal flips sign depending on the reporting window (negative at 30 days, positive at 90+ days); `sample_followup` and `project_nurture` show a negative value gap at every window tested; `reactivation` and `trade_engagement`'s combined 977 recipients show zero purchase/repeat-purchase events, ever, regardless of engagement. Full write-up in `output/attribution_findings.md`; full computed output in `output/attribution_report.json`.

## What this isn't

Not a Fireclay-specific script. `attribution.py` takes plain dicts (`{program, opened, clicked}` for engagements, `{customer_id, event_date, amount}` for value events) and contains zero hardcoded field or program names — see its own docstring and `tests/test_attribution.py`. It also isn't a causal-inference tool: it reports correlational gaps between engaged and unengaged recipients, not a randomized-experiment result. See the selection-effect caveat in `output/attribution_findings.md`.

## How it works

Two pieces:

1. **`attribution.py`** (generic, already tested, untouched by this write-up) — three pure functions: `platform_metrics` (open/click rate per program), `commercial_outcomes` (engaged-vs-unengaged purchase rate and mean value per program, with an optional attribution window), and `divergence` (ranks programs both ways and reports the rank shift).
2. **`run_attribution.py`** (the Fireclay-shaped wiring layer, same role as `extract_hubspot.py`/`extract_salesforce.py` play for the reconciliation engine) — queries `email_engagement` and `funnel_events` out of `trade_signal.db`, runs the three functions at three attribution windows (no cap, 30 days, 90 days) both overall and broken out by segment, and writes `output/attribution_report.json`.

## Adapting this to your own data

Point `run_attribution.py`'s two query functions (`_fetch_engagements`, `_fetch_value_events`) at any table or CSV that can produce the same two shapes — `attribution.py` itself has no dependency on this project's schema. The `WINDOW_DAYS` and `SEGMENTS` constants at the top of `run_attribution.py` are the only things a different project would need to change.

## Known limitation

Every comparison here is observational: recipients weren't randomly assigned to open or not open an email, so a negative value gap (see Finding 2 in the findings write-up) shows correlation, not proof that opening an email causes someone to spend less — the more likely explanation is a selection effect (already-convinced customers don't need to open a follow-up). Treat any negative gap as a hypothesis for a designed test, not a decision on its own — the same posture `analysis/experimentation/decision_memo.md` already takes toward this project's other findings.

## Running it yourself

```bash
cd analysis/lifecycle-attribution
python3 run_attribution.py
python3 -m pytest tests/
```
