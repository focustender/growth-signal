# Final QA Gate

## What this is

The pre-send quality gate for this round of work, using the vendored `analysis-qa-checklist` skill — `scripts/qa_runner.py` run against every key data file touched or produced this round, plus a manual walkthrough of `references/qa_checklist_master.md`'s six sections against the full updated `site/case-study.html`. Result: approved for delivery, zero must-fix items, three independent cross-checks confirming previously-published numbers still hold up. Full sign-off: `output/qa_signoff.md`.

## What this isn't

Not a rubber stamp — the sign-off names real, specific things (a pre-existing charset/mojibake issue, several small-sample-size findings) rather than reporting a clean pass with nothing to say.

## How it works

`qa_runner.py`'s CLI works as shipped (no vendored-script bugs encountered here, unlike several other skills used this round — see the other `analysis/*/README.md` files for those). Run against `data/*.csv` and this round's key `analysis/*/output/*.csv` files; JSON reports in `output/`. The manual six-section checklist walkthrough is in `output/qa_signoff.md`.

## Running it yourself

```bash
python3 .claude/skills/analysis-qa-checklist/scripts/qa_runner.py --input data/customers.csv
```
