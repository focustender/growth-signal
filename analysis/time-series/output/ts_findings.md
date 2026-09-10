# Time Series Analysis: Trade-Show Single-Sample Stall Rate

**Metric:** % of single-sample trade-show trade leads who never advance to project/purchase, by signup month
**Period:** 2024-01 to 2025-08 (20 monthly points)
**Frequency:** Monthly
**Analyst:** Ian Castorillo, using the vendored `time-series-analysis` Claude Code skill
**Real, not simulated:** every number computed directly from `trade_signal.db`; underlying data is synthetic (see root README's Real/Synthetic/Simulated labeling).

---

## Summary

**Trend:** Downward — the linear fit is –0.77%/month over the full window, and the weighted stall rate falls from 74.2% in 2024 to 71.7% in the eight 2025 months observed so far.
**Overall change:** 40.0% (2024-01) → 57.1% (2025-08), though the series is noisy month to month (single points range from 25% to 100%).
**Notable anomalies:** 1 detected (2024-11: 25.0%, z=–2.53) — see caveat below; this is very likely small-sample noise, not a real event.
**Seasonal pattern:** Not assessable with confidence — see Caveats.

This confirms the headline 73% stall-rate finding already published in `docs/measurement-foundation.md` is a stable full-period average (the time-weighted mean here is 73.97%, matching it almost exactly), and adds a new layer: the rate has drifted modestly downward over the observed window rather than staying flat or worsening. It has **not** disappeared or reversed — every single month in the dataset still shows a stall rate at or above 25%, with most months well above 50%.

---

## Statistical summary

| Statistic | Value |
|---|---|
| Periods | 20 |
| Mean | 73.97% |
| Median | 75.00% |
| Min | 25.00% (2024-11) |
| Max | 100.00% (2024-04, 2024-06, 2024-09, 2025-02 — each a small-n month) |
| Std deviation | 19.37 |

---

## Trend analysis

**Direction:** Downward
**Slope:** –0.77%/month (linear least-squares fit across all 20 points)
**Consistency:** Volatile month to month (std dev 19.4 against a mean of 74%), but the second half of the series is directionally lower than the first: 2024 weighted average 74.2%, 2025-through-August weighted average 71.7%. The most recent three months (June–August 2025) are the lowest sustained stretch in the series (62.5%, 60.0%, 57.1%).

**Interpretation:** The trade-show stall problem is real and persistent, not a one-time artifact — but it is not static either. A ~2.5-point year-over-year improvement, concentrated in the most recent months, is worth monitoring rather than dismissing, though at this volume (4–11 leads/month) it's too early to credit any specific cause. No intervention targeting this channel had shipped as of this dataset's generation, so this drift should be read as a property of the underlying (synthetic) generator, not evidence of an improvement already in motion.

---

## Seasonality

Not assessable with confidence: the skill's own guidance recommends at least 2 full seasonal cycles for reliable decomposition, and this series has under 2 years of monthly points with only 4–11 leads per month. Any apparent "trade-show calendar" seasonality in a series this short and this noisy would not be distinguishable from random monthly variation. Treat any seasonal-looking pattern in the raw table as directional at most.

---

## Anomalies

| Date | Value | Direction | Z-score | Likely explanation |
|---|---|---|---|---|
| 2024-11 | 25.0% | Dip | –2.53 | Base of only 4 leads that month (1 stalled, 3 advanced) — a single lead's outcome moves this rate by 25 points. Flagged by the statistical test, but not treated as a real event given the sample size. |

---

## Period-over-period growth rates

Full month-by-month table (value, growth vs. prior month, 3-month rolling average) is in `output/ts_report.txt`, generated directly by the vendored `ts_analyzer.py` functions. Not reproduced in full here — the aggregate trend and the 2024-vs-2025 comparison above are the load-bearing numbers; individual month-over-month swings are dominated by small-sample noise (see table above).

---

## Recommendations

1. Treat the 74%→72% year-over-year drift as a real but small, unconfirmed signal — worth re-checking once another 6–12 months of leads accumulate (at ~6/month average, that's roughly 40–70 more leads before the monthly rate stabilizes enough to trust individual points).
2. Don't over-interpret single-month swings (the 2024-11 dip and the four 100%-stall months) — with n as low as 2–11 leads/month, a monthly view alone will mislead; the quarterly or half-year weighted average is the more trustworthy unit for this specific channel.
3. If this were a live pipeline, the natural next step is exactly what `analysis/experimentation/` already recommends for this same channel: full rollout plus directional monitoring, not a formal test — the volume constraint that made a randomized test infeasible there applies just as much to trusting a monthly trend line here.

---

*Underlying data: `analysis/time-series/trade_show_stall_monthly.csv`. Full computed report: `output/ts_report.txt`.*
