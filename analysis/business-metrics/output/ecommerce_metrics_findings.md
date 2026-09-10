# Business Metrics: AOV and Revenue-per-Customer by Segment

**Real analysis, synthetic underlying data** — every number below comes from `trade_signal.db`'s actual funnel events, run through `ecommerce_metrics.py` (generic, reusable, no Fireclay-specific assumptions — see `tests/test_ecommerce_metrics.py`, 4/4 passing) via `run_ecommerce_metrics.py`. Full computed output: `output/metrics_report.json`.

**Not using the vendored template:** the `business-metrics-calculator` skill's own `assets/metrics_report_template.md` is entirely SaaS-shaped (MRR, ARR, NRR, DAU/MAU) — it doesn't have a slot for AOV, conversion rate, or revenue-per-customer. Rather than force e-commerce numbers into a SaaS template, this write-up uses this project's own established findings-doc format instead. See `README.md` for the full gap this surfaced in the vendored skill.

## Metric definitions

- **AOV (average order value):** total revenue ÷ number of purchase/repeat-purchase events, per segment.
- **Conversion rate:** customers with at least one purchase ÷ all customers in the segment.
- **Revenue per customer:** total segment revenue ÷ all customers in the segment (not just purchasers) — this is the metric that actually reflects a segment's $ opportunity, since it accounts for both how many people convert and how much they spend.

## Results

| Segment | Customers | Conversion rate | AOV | Total revenue | Revenue per customer |
|---|---:|---:|---:|---:|---:|
| Designer | 662 | **60.7%** (highest) | $1,086 | $523,685 | $791 |
| Homeowner | 1,769 | 43.4% | $1,093 | $930,453 | $526 (lowest) |
| Commercial | 211 | 34.1% (lowest) | $13,382 | $1,137,446 | $5,391 |
| Trade | 558 | 34.2% | **$13,670** (highest) | $3,226,137 (highest) | **$5,782** (highest) |

## The finding

**The segment that converts best generates the least revenue per customer, and the segment that converts worst generates the most.** Designer customers convert at 60.7% — the highest rate of any segment, nearly double homeowner's 43.4% — but designer's revenue per customer ($791) is the second-lowest of the four segments. Trade customers convert at roughly half designer's rate (34.2%) but generate over 7x designer's revenue per customer ($5,782 vs $791), driven entirely by AOV: a trade order averages $13,670 against designer's $1,086.

This is the same "platform metric vs. commercial outcome" distinction the JD names directly and the attribution analysis (`analysis/lifecycle-attribution/`) already surfaced for email programs — here it shows up in segment-level conversion rate vs. actual dollar value. **A dashboard that reports conversion rate alone would rank designer as the strongest segment and trade as one of the weakest; a dashboard that reports revenue would show the opposite for trade.** Neither number alone tells the right story; a lifecycle program optimizing purely for "get more segments converting like designer" would be optimizing away from where 34.6% of total revenue in this dataset ($3.2M of $5.8M across all four segments) actually comes from.

## Segment-specific notes

- **Homeowner** is the largest segment by customer count (1,769, 55% of all customers) but the smallest by revenue per customer ($526) — high volume, low unit value, consistent with a single-project, one-time-purchase pattern (also see `analysis/cohort-analysis/`'s finding that homeowners repeat-purchase at less than half the trade rate).
- **Commercial** and **trade** have nearly identical AOV (~$13,400–$13,700) and revenue-per-customer (~$5,400–$5,800) despite trade having over 2.5x as many customers — commercial is a smaller but equally high-value segment.
- **Designer**'s high conversion rate paired with low AOV suggests designers may be buying smaller, more frequent orders (e.g., samples or small-batch purchases for individual client projects) rather than one large project order — consistent with `analysis/cohort-analysis/`'s finding that designer has the second-highest repeat-purchase rate (19.9%) despite the lowest per-order value.

## Recommended next steps

1. If a growth initiative is framed around "increase conversion rate," specify *which segment's* conversion rate — improving homeowner or designer conversion moves a lot of customers but comparatively little revenue; improving trade or commercial conversion by the same percentage-point amount moves far more dollars.
2. Report revenue-per-customer alongside conversion rate in any segment-level dashboard, not conversion rate alone — this analysis is the concrete case for why, using this project's own data.
3. Pair this with `analysis/lifecycle-attribution/`'s findings when prioritizing which email programs to invest in per segment — a program with a strong platform metric in a low-revenue-per-customer segment (like designer) is a different priority than the same program performing well in trade or commercial.
