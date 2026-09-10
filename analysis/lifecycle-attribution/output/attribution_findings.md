# Lifecycle Attribution: Platform Metric vs. Commercial Outcome

**Real analysis, synthetic underlying data** (see root `README.md`'s Real/Synthetic/Simulated labeling) — every number below comes from `trade_signal.db`'s actual email-engagement and funnel-event records, run through `attribution.py` (generic, reusable, no Fireclay-specific assumptions — see `tests/test_attribution.py`, 6/6 passing) via `run_attribution.py`. Full computed output: `output/attribution_report.json`.

## The JD line this answers

> "You understand attribution, experimentation, segmentation, deliverability, and measurement — and know the difference between a platform metric and a commercial outcome."

## Metric definitions

- **Platform metric** — open rate / click rate per email program (`campaign_type`), the numbers a marketing platform surfaces natively, computed directly from `email_engagement`.
- **Commercial outcome** — for each program's recipients, split into *engaged* (ever opened that program) and *unengaged* (never opened), the mean $ value of `purchase`/`repeat_purchase` funnel events occurring on or after each recipient's first send of that program, optionally capped at a window. Customers with no qualifying event count as $0, not excluded — a program's real value includes the people it failed to move.
- **Divergence** — for each program, its rank by open rate vs. its rank by the engaged-vs-unengaged value gap. A large rank shift means the platform metric and the commercial outcome disagree about which program matters.
- **Window** — how many days after the send a value event still counts. Tested at no cap, 30 days, and 90 days, because (see Finding 1) the choice of window changes the answer for at least one program here.

## Results: six programs, 90-day window

| Program | Sent | Open rate | Engaged mean value | Unengaged mean value | Value gap | Rank shift (open → value) |
|---|---:|---:|---:|---:|---:|---:|
| `welcome` | 3,200 | 51.4% | $1,698 | $1,455 | **+$242** | +1 |
| `sample_followup` | 2,190 | 43.1% | $1,673 | $1,786 | **–$114** | –2 |
| `post_purchase` | 1,433 | 58.1% (highest of any program) | $90 | $116 | **–$26** | –3 |
| `project_nurture` | 149 | 38.9% | $6,265 | $7,355 | **–$1,090** | –2 |
| `reactivation` | 725 | 26.5% | $0 | $0 | $0 (tie) | n/a — see Finding 3 |
| `trade_engagement` | 252 | 25.4% | $0 | $0 | $0 (tie) | n/a — see Finding 3 |

## Finding 1: the sign of the commercial signal depends on the window, for at least one program

| Program | No window | 30-day window | 90-day window |
|---|---:|---:|---:|
| `welcome` | **+$320** | **–$56** | **+$242** |
| `sample_followup` | –$228 | –$70 | –$114 |
| `post_purchase` | –$143 | $0 / $0 (tie) | –$26 |
| `project_nurture` | –$1,706 | –$2,264 | –$1,090 |

`welcome` is the only program where the conclusion flips depending on the window: a 30-day look says opening the welcome series is associated with *less* spend afterward; a 90-day or unbounded look says the opposite. Fireclay tile is already framed in this project as a considered-purchase category (see the JD-mapping table above), and a considered purchase plausibly takes longer than 30 days to convert — so a 30-day welcome-series report would have reached the wrong conclusion here. The practical takeaway: **for this program, the reporting window itself needs to be chosen deliberately, not defaulted to whatever an ESP dashboard ships with.**

The direction holds across all four segments at the 90-day window — homeowner +$33, designer +$52, trade +$1,105, commercial +$720 — so this isn't an artifact of one segment dominating the overall number.

## Finding 2: two programs are negatively associated with commercial value at every window tested

`sample_followup` and `project_nurture` show a negative engaged-vs-unengaged gap at every window (no cap, 30 days, 90 days) — the only two programs where the sign never flips. `sample_followup`'s direction also holds in 3 of 4 segments (homeowner –$75, trade –$300, commercial –$1,324; designer is the one exception, +$101).

**This is a correlation, not evidence that opening the email causes people to spend less.** Recipients weren't randomly assigned to open or not open — customers who already feel confident enough to skip a follow-up email plausibly convert at least as well as (or better than) customers who needed to open it for reassurance. That's a selection effect, the same category of caveat this project already applies elsewhere (see the fuzzy-match false-positive rate called out honestly in `analysis/crm-reconciliation/output/reconciliation_findings.md`). The right next step is a designed test on send/content, not a platform-metric-driven decision to change these programs based on this analysis alone.

## Finding 3: for two programs, open/click isn't a noisy proxy — it's disconnected from any outcome this dataset can observe

None of the 725 `reactivation` recipients or 252 `trade_engagement` recipients — engaged or unengaged, 977 people combined — have *any* `purchase` or `repeat_purchase` event on record, at any date, in the full ~20-month window. This isn't a window-length artifact (it's $0/$0 at every window tested); it's that these two programs' entire recipient pools never convert in this dataset at all.

That means an open-rate or click-rate report on these two programs isn't measuring a weak proxy for revenue — it's measuring engagement in a population where the "commercial outcome" side of the comparison structurally cannot move. Reporting an open rate for `reactivation` without that caveat would silently imply it's a growth lever it structurally can't be evaluated as here.

## Applying the insight-synthesis framework (So What → Why → Now What)

*(Using the `insight-synthesis` skill's prioritization framing — vendored from [nimrodfisher/data-analytics-skills](https://github.com/nimrodfisher/data-analytics-skills), see `.claude/skills/README.md`.)*

**1. Welcome's window instability** — *So what:* a 30-day report and a 90-day report on the same program reach opposite conclusions. *Why:* plausibly the purchase-consideration cycle for tile exceeds 30 days. *Now what:* standardize welcome-series reporting on a 90-day-minimum window, and flag any dashboard defaulting to 30 days as a false-negative risk, not just an inconvenience.

**2. sample_followup / project_nurture's stable negative gap** — *So what:* two programs where the platform metric and commercial outcome disagree at every window tested. *Why:* most plausibly a selection effect (already-convinced customers skip the email), not a causal harm from the email itself. *Now what:* don't use open/click as a success metric for these two programs going forward; if they're worth optimizing, that requires a randomized send/content test, not a re-read of this observational data.

**3. reactivation / trade_engagement's zero observed outcomes** — *So what:* the standard commercial yardstick (purchase/repeat-purchase) can't evaluate these two programs at all in this dataset. *Why:* their recipient pools may be genuinely lapsed/never-converted, or the downstream signal that would show impact (e.g. a return site visit, a second sample request) isn't a "purchase" event and so isn't being counted. *Now what:* this is a systems-requirements-style gap, the same category as the reconciliation section's HubSpot/Salesforce memo — define and start capturing a lighter-weight downstream event for reactivation-style programs before reporting an open rate on them as if it were a proxy for value.
