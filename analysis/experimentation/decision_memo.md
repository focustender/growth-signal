# Decision Memo — Trade-Show Second-Sample Nudge

**Answers the JD's own phrase directly:** "a disciplined experimentation program... and clear recommendations on what to scale, stop, or learn next." This memo's recommendation is a **stop-and-learn**, not a scale-or-kill — the test itself needs to change before a scale/kill call is even possible.

## Decision: kill this test design, not the hypothesis

**Stop:** the randomized holdout-vs-treatment design specified in the original backlog, on trade-show volume alone. `feasibility_findings.md` shows it cannot detect its own target effect size within any realistic timeframe (minimum 5+ years for the smallest threshold).

**Learn:** trade-show is a structurally low-volume channel (10/month). Any future test that relies on a fixed, short window and a hard significance threshold on this channel specifically will hit the same wall, regardless of what's being tested. That's a fact about the channel, not about this one hypothesis.

**Do instead — a revised measurement plan:**

1. **Skip the holdout. Roll the nudge out to 100% of eligible trade-show single-sample leads.** With this little volume, splitting it further only makes the feasibility problem worse, and a real business doesn't usually leave known money on the table for years just to preserve a control group that can never resolve.
2. **Track it directionally, not with a significance test.** Compare the second-sample rate for leads who received the nudge against the pre-rollout baseline (11%) over the next two full quarters (roughly 60 leads, based on real monthly volume). This can't produce a p-value worth trusting at this N — say so plainly if this gets presented anywhere — but a raw rate moving from 11% to, say, 20%+ and holding for two quarters is still a meaningful operational signal, especially paired with the qualitative logic already documented in `measurement-foundation.md` for why trade-show leads under-perform.
3. **Set an explicit reversal bar, since "directional" isn't "no bar at all":** end the rollout if the second-sample rate over two quarters is not at least 5pp above the 11% baseline (a low bar, deliberately, since this design can't rule out noise at anything higher with confidence) — the point is to protect against the nudge doing nothing or actively hurting engagement, not to certify a specific lift size.
4. **Revisit a real randomized test only when the premise changes** — either trade-show lead volume grows materially (a marketing investment decision, not an experimentation one), or the same nudge mechanism gets tested on a larger, comparable population where a proper RCT is actually feasible (worth a separate feasibility check before committing, using this same `power_analysis.py` tool, not assumed).

## Why this, not a fabricated experiment result

An earlier draft of this work planned to simulate a treatment effect and "run" the test against a synthetically-sized cohort to produce a scale/iterate/kill result. That was dropped deliberately: manufacturing an outcome to a test that can't really be run would be a more impressive-looking deliverable and a less honest one. The real, checkable finding here — that the test as specified is infeasible, backed by a reusable power-analysis tool anyone can rerun against different assumptions — is more valuable than a fake number, and it's the finding a genuinely careful analyst would actually produce before spending a team's time on this test.

## How this relates to the Sample Kit Builder (Hypothesis 2)

The backlog's second hypothesis (a portal re-entry prompt at 21 days of inactivity — the Sample Kit Builder already built in this project) has a simpler, single-threshold design (≥5% of prompted accounts convert within 30 days) rather than a holdout comparison, so it doesn't hit this same power problem in the same way. It's not evaluated here since the prototype isn't receiving real customer traffic yet (it's live on a Shopify dev store, not production commerce) — there's no usage data to check a real threshold against. Worth a follow-up feasibility pass once (or if) it ships for real.
