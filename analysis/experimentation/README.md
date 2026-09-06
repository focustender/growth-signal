# Experimentation feasibility check

A reusable power-analysis tool (`power_analysis.py`, generic two-proportion sample-size/MDE math, no Fireclay-specific assumptions), applied to check whether the experimentation backlog's Hypothesis 1 (`docs/measurement-foundation.md`) can actually be tested as specified.

**Real, not simulated:** every number here comes from `trade_signal.db`'s actual historical volume and email-engagement records, computed by `run_feasibility_check.py`. Read `feasibility_findings.md` for the numbers and `decision_memo.md` for what to do about them.

**The short version:** the backlog's proposed test (90-day randomized holdout on trade-show leads) needs 623 leads to detect its own "scale" threshold; the channel produces ~10/month, meaning ~62 months to get there. The fix isn't a bigger test window or a different metric (checked, doesn't help) — it's recognizing this channel can't support a formal RCT at all, and switching to a full rollout with directional monitoring and an explicit reversal bar instead.

## Running it yourself

```bash
cd analysis/experimentation
python3 run_feasibility_check.py
python3 -m pytest tests/
```

## Adapting this to a different hypothesis or channel

`power_analysis.py`'s three functions (`sample_size_two_prop`, `mde_two_prop`, `project_volume`) take plain baseline rates and volume as arguments — no dependency on this project's schema. Point `run_feasibility_check.py`'s two query functions at a different table/segment to check any other experiment's feasibility before committing runway to it.
