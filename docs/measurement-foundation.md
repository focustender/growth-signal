# Trade Signal — Lifecycle Measurement Foundation

Synthetic dataset: 3,200 customers, Jan 2024–Aug 2025, segmented into homeowner / designer / trade / commercial per Fireclay's own customer-journey language. Generated with `data/generate_dataset.py` (seeded, reproducible). Analysis run directly against `data/trade_signal.db` via Claude Code.

## Conversion definitions

| Stage | Definition |
|---|---|
| Interest | `site_visit` or `visualizer_use` event recorded |
| Sample | At least one `sample_request` event |
| Project | `project_upload` event (trade/commercial only — architects/contractors submit project scope) |
| Purchase | At least one `purchase` event |
| Repeat | A second `purchase`/`repeat_purchase` event within the window |
| Advocacy | A `reviews` record tied to the customer |

## Funnel by segment (customers, not events)

| Segment | Customers | Sampled | % Sampled | Purchased | % of Sampled → Purchased | Repeat buyers |
|---|---|---|---|---|---|---|
| Homeowner | 1,769 | 1,252 | 70.8% | 768 | 61.3% | 83 |
| Designer | 662 | 498 | 75.2% | 402 | 80.7% | 80 |
| Trade | 558 | 352 | 63.1% | 191 | 54.3% | 45 |
| Commercial | 211 | 88 | 41.7% | 72 | 81.8% | 13 |

Designer and commercial convert best once sampled. Trade converts worst of the three non-homeowner segments — 54.3% of trade leads who request a sample never purchase, the largest sample-to-purchase gap outside commercial's small-n outlier.

## The finding

Breaking trade-segment single-sample requesters down by acquisition channel surfaces a clean, actionable pattern:

| Acquisition channel | Single-sample trade leads | Never advanced to project/purchase | % stalled |
|---|---|---|---|
| **Trade show** | 115 | 84 | **73.0%** |
| Showroom walk-in | 20 | 13 | 65.0% |
| Architect referral | 39 | 23 | 59.0% |
| Paid social | 12 | 7 | 58.3% |
| Direct | 19 | 11 | 57.9% |
| Organic search | 44 | 24 | 54.5% |
| Referral | 33 | 17 | 51.5% |
| Email capture | 9 | 3 | 33.3% |

**73% of trade leads acquired at trade shows who request exactly one sample never advance to a project upload or purchase** — more than double the stall rate of leads who came in through email capture (33.3%). Trade-show leads are also disproportionately unlikely to request a *second* sample or kit (11% do, versus 22% of trade leads overall and 46% of designers) — the single point where the Trade Portal redesign should intervene, since a second sample request is the strongest observed predictor of eventual purchase in this segment.

A separate, secondary pattern: customers who use the on-site visualizer but don't request a sample within 14 days ranges from 32% (designer) to 64% (commercial) with trade at 42.6% — real signal, but the trade-show stall above is the sharper, more directly actionable one and is what the Trade Portal / Sample Kit Builder redesign (see `design/`) targets first. The visualizer drop-off feeds the second intervention: an AI-personalized nurture triggered off visualizer-use-without-follow-up (see `visualizer/README.md`).

## Why this is plausible as a real operating problem, not just a data artifact

Trade shows generate a burst of business-card-style leads with lower initial intent-signal than a referral or an architect actively researching a spec. The JD itself distinguishes "lifecycle side of the Trade Program: activation, education, nurture, reactivation" as its own owned surface — this is exactly the kind of channel-level stall a Lifecycle Growth & Analytics Manager would be expected to catch in a data-quality pass, not something Trade sales reps would notice on their own since each rep only sees their own leads, not the channel-level aggregate.

## Experimentation backlog (hypothesis → test → decision threshold)

1. **Trade-show second-sample nudge.** Hypothesis: a targeted follow-up (day 5 and day 12 post-first-sample) offering a curated "pair with" second sample specifically to trade-show-acquired leads lifts second-sample-request rate from 11% toward the referral-channel baseline (~30%+). Test: holdout vs. treatment on next 90 days of trade-show sign-ups. Decision threshold: roll out fully if second-sample rate improves ≥8pp with no drop in email opt-out rate; iterate on offer/timing if 3–8pp; kill if <3pp.
2. **Trade Portal single-sample re-entry flow.** Hypothesis: a portal prompt shown when a trade account has exactly one sample on file and no activity in 21 days (the Sample Kit Builder — see `design/`) recovers a meaningful share of stalled leads without added sales-rep effort. Decision threshold: ≥5% of prompted accounts request a second sample within 30 days to justify keeping it live.
3. **Visualizer-no-follow-up nurture.** Hypothesis: an AI-personalized email referencing the specific tile/room a visitor visualized, sent 3 days after a no-follow-up visualizer session, outperforms a generic "did you see our new arrivals" send on sample-request rate. Decision threshold: statistically significant lift (95% CI) in sample-request rate within 14 days of send, measured against the generic-send control group.

## Data-quality note

`data/raw_crm_export.csv` simulates an unreconciled CRM export for 600 customers, deliberately messy: inconsistent segment casing, mixed date formats, and duplicate-ish rows split across multiple partial records per customer. Running `data/reconcile_crm_export.py` against it (grouping raw rows by customer and coalescing fields rather than naively dropping every row after the first) takes 669 raw rows down to 600 distinct customers, merges 68 customers who had multiple partial records, and recovers `source_channel` for 34 customers by pulling the value from a sibling row instead of leaving it blank — versus 0 recoverable under a naive first-row-wins dedupe. That gap is the actual point: a naive reconciliation pass would have reported those 34 as unattributed, wrongly darkening the channel-level friction analysis above. This is the kind of imperfect-data reconciliation the role's "About You" section names directly, not just an assumption that analysis starts from clean tables.
