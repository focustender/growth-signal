# This Round's Narrative (SCR framework)

*Drafted using the vendored `data-narrative-builder` skill's Situation-Complication-Resolution framework, then adapted into the short intro block published in `site/case-study.html` right before the Data Quality Audit section. Kept here in full since the published version is necessarily compressed.*

## Situation

The original build already answered the JD's headline asks with real, live evidence: a trade-show stall finding, a live HubSpot↔Salesforce reconciliation, a real stop-and-redesign experimentation call, and a working Claude Code skill. That work stood on its own.

## Complication

But three things were true at the same time: one analysis engine (`lifecycle-attribution/`) had been built and tested but never actually run or wired into the story — code with no output. There was no formal, scored data-quality pass anywhere in the repo, despite the JD naming "data-quality checks" directly. And every finding so far was a point-in-time snapshot — no trend, no cohort view, no segment-level dollar value, no cross-check that the numbers still hold up.

## Resolution

This round closes all three gaps using a curated set of vendored analytics skills (`.claude/skills/README.md`) as workflow tooling, laid on top of this project's own original engines rather than replacing them. The result isn't just more sections — it's the same core theme, reinforced from three independent directions instead of one:

- **Attribution** (`analysis/lifecycle-attribution/`): a platform metric and a commercial outcome disagree at the *email program* level, and disagree differently depending on the measurement window.
- **Business metrics** (`analysis/business-metrics/`): the same disagreement shows up at the *segment* level — the best-converting segment isn't the most valuable one.
- **Cohort + root-cause** (`analysis/cohort-analysis/`, `analysis/root-cause/`): even a real, positive trend (the declining stall rate) doesn't survive a naive single-dimension explanation — the honest answer is "no smoking gun," not a fabricated one.

The thread across all of it: a platform-level number is never the whole story, and checking that gap — rather than assuming a metric means what it looks like it means — is what this round actually demonstrates, three times over, on three different slices of the same dataset.
