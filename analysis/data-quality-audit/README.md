# Data Quality Audit

## What this is

A formal data-quality audit of this project's core dataset and its deliberately messy CRM-export reconciliation exercise, using the vendored `data-quality-audit` and `programmatic-eda` Claude Code skills (see `.claude/skills/README.md`) — six standard quality dimensions (Completeness, Accuracy, Consistency, Timeliness, Uniqueness, Validity), scored and documented the way a real pre-production data-quality gate would be, answering the JD's own "data-quality checks" and "trustworthy reporting" language directly.

Real results: **9.41/10 overall**, no Critical or High findings. The most interesting result isn't a defect — it's a real limitation of a generic tool: `duplicate_finder.py`'s exact-key check reports 0 duplicates on the raw CRM export, because that file's 68 real duplicate customers are encoded as suffixed IDs (`CUST-00042-dup`), not exact-matching keys. Re-deriving the base ID independently reproduces this project's own already-published "669→600, 68 merged" figure. Full write-up: `output/quality_rubric.md` (the scorecard) and `output/eda_findings_summary.md` (the EDA-specific notes).

## What this isn't

Not a live pipeline monitor — this dataset is static and generated once, so the freshness dimension is scored N/A rather than forced into a misleading number. Not a rewrite of the vendored skill scripts — `rules.json` and this README are the only Fireclay-shaped wiring; the checks themselves run the vendored scripts as-is (with one necessary exception, below).

## How it works

1. **`rules.json`** — the business rules for `value_range_validator.py`: `amount ≥ 0`, `email_opt_in ∈ {0,1}`, `score ∈ [1,10]`.
2. Every other check runs a vendored script directly against `data/*.csv`, captured to `output/raw_script_output/`.
3. **One necessary workaround:** `.claude/skills/data-quality-audit/scripts/null_counter.py` and `.claude/skills/programmatic-eda/scripts/null_profiler.py` both crash under Python 3.14 on any invocation (not just `--help`) — an upstream bug where argparse's stricter help-string validation trips on a bare `%` in one of their `help=` strings. Rather than edit the vendored files, their core functions (`count_nulls`, `profile_nulls`) are imported directly and called in plain Python — see `output/raw_script_output/null_checks_direct_import.txt` and `null_counter_clean.txt`.
4. Results are hand-scored into `output/quality_rubric.md` using the six dimensions defined in `.claude/skills/data-quality-audit/references/quality_dimensions.md`.

## Adapting this to a different dataset

Point `rules.json` at your own columns/rules and re-run the same script list against your own CSVs — none of the vendored scripts have any Fireclay-specific assumptions. If you're on Python 3.14+, apply the same direct-import workaround for `null_counter.py`/`null_profiler.py` until upstream fixes the `%`-in-help-string bug.

## Known limitation

This is a one-time audit of a static, synthetic dataset — there's no recurring pipeline to re-check on a schedule, so "Review date" in the scorecard's sign-off section is N/A rather than a real next-audit date.

## Running it yourself

```bash
cd analysis/data-quality-audit
cat rules.json
# see output/raw_script_output/ for every captured script run, or re-run any
# individual vendored script from ../../.claude/skills/<skill>/scripts/ directly
```
