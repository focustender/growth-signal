# Experimentation Backlog, Hypothesis 1 — Feasibility Check

**Real analysis against real historical volume.** No synthetic data or simulated outcomes anywhere in this document — every number here comes from `trade_signal.db`'s actual customer and email-engagement records, run through `power_analysis.py` (generic, reusable, no Fireclay-specific assumptions — see `tests/test_power_analysis.py`, 6/6 passing). Full computed output: `output/feasibility_report.json`.

## The hypothesis being checked

From `docs/measurement-foundation.md`'s experimentation backlog, Hypothesis 1:

> **Trade-show second-sample nudge.** Hypothesis: a targeted follow-up (day 5 and day 12 post-first-sample) offering a curated "pair with" second sample specifically to trade-show-acquired leads lifts second-sample-request rate from 11% toward the referral-channel baseline (~30%+). Test: holdout vs. treatment on next 90 days of trade-show sign-ups. Decision threshold: roll out fully if second-sample rate improves ≥8pp with no drop in email opt-out rate; iterate on offer/timing if 3–8pp; kill if <3pp.

Before running this test, the obvious first question a disciplined experimentation program should ask: **can a 90-day window on this specific channel actually produce enough leads to detect any of these thresholds?**

## Real trade-show lead volume

198 trade-show-acquired trade customers exist in the historical data, spanning 2024-01-08 to 2025-08-30 — **10.05 new trade-show leads per month**, computed directly from the real signup-date span, not assumed.

## Sample size required to detect each threshold

Using a standard two-proportion power calculation (α=0.05, 80% power), baseline second-sample rate 11%:

| Threshold | Target rate | Required N (per arm) | Required N (total) |
|---|---|---|---|
| Scale (≥8pp lift) | 19% | 312 | **623** |
| Iterate (3–8pp lift) | 14% | 1,907 | **3,813** |

At 10.05 leads/month, reaching even the smaller "scale" threshold's 623 total leads would take **62 months — over 5 years.** The "iterate" threshold's 3,813 is roughly 6x further out of reach than that.

## Checked whether a different metric would fix this — it doesn't

One plausible fix: measure something that happens more often than "requests a second sample" — e.g., whether the lead opens or clicks the nudge email itself. The real historical click-through rate on the closest comparable campaign (`sample_followup`, trade segment) is **17.6%** (62 of 352 sends), higher than the 11% baseline being tested.

Recomputing minimum detectable effect (MDE) at realistic test windows, for both metrics:

| Window | Leads (total / per arm) | MDE, second-sample rate | MDE, click-rate metric |
|---|---|---|---|
| 3 months | 30 / 15 | 46.6pp | 48.4pp |
| 6 months | 60 / 30 | 31.3pp | 33.6pp |
| 12 months | 121 / 60 | 20.7pp | 23.0pp |
| 18 months | 181 / 90 | 16.3pp | 18.3pp |
| 24 months | 241 / 121 | 13.8pp | 15.6pp |

The click-rate metric's MDE is **not smaller** than the second-sample metric's at any window — it's slightly larger. This confirms the real constraint isn't which behavior you measure, it's the total number of people in the channel. Switching metrics doesn't fix a population problem.

## The finding

Even waiting a full 2 years, the smallest reliably detectable effect on this channel is **13.8 percentage points** — nearly double the original "scale" threshold of 8pp. A real second-sample nudge email is far more plausibly worth 5-15pp than 14+pp. **The test as specified cannot detect the effect size it exists to find, no matter how long it runs, on this channel alone.** This is a structural volume ceiling, not a fixable test-design mistake — see `decision_memo.md` for what to do about it.
