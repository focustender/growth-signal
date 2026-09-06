# Task 3 report: Digest orchestrator + optional live CRM section

## What was done

Implemented `.claude/skills/lifecycle-pulse/scripts/generate_digest.py` per the
plan's Task 3 code, with one path-arithmetic correction (see below). Ran it
live for real (not backdated/simulated) against today's actual date,
2026-09-05, from inside `.claude/skills/lifecycle-pulse/`:

```
python3 scripts/generate_digest.py
```

Output:
```
Wrote /Users/iancastorillo/fireclayTile/trade-signal/.claude/skills/lifecycle-pulse/digest_output/2026-09-05-digest.md
```

This created:
- `.claude/skills/lifecycle-pulse/snapshots/2026-09-05.json` (new live snapshot)
- `.claude/skills/lifecycle-pulse/digest_output/2026-09-05-digest.md` (new digest, and the first file in that directory — `digest_output/` did not exist before this run)

## Path arithmetic: the fix and why

The plan's literal code set `REPO_ROOT = SKILL_DIR.parents[1]`. This is wrong
for the real directory depth and was not used as-is.

`generate_digest.py` lives at
`.claude/skills/lifecycle-pulse/scripts/generate_digest.py`, i.e. 4 path
segments below the repo root (`.claude`, `skills`, `lifecycle-pulse`,
`scripts`). Given:

```python
SCRIPT_DIR = Path(__file__).resolve().parent   # .../trade-signal/.claude/skills/lifecycle-pulse/scripts
SKILL_DIR = SCRIPT_DIR.parent                   # .../trade-signal/.claude/skills/lifecycle-pulse
```

`SKILL_DIR` sits 3 path segments below the repo root (`.claude`, `skills`,
`lifecycle-pulse`). Pathlib's `.parents[n]` indexing means:
- `SKILL_DIR.parents[0]` = `.../trade-signal/.claude/skills`
- `SKILL_DIR.parents[1]` = `.../trade-signal/.claude`  (still inside `.claude` — this is what the plan's literal code would have produced, which is wrong)
- `SKILL_DIR.parents[2]` = `.../trade-signal`  (the actual repo root)

So the correct line is:

```python
REPO_ROOT = SKILL_DIR.parents[2]
```

I verified this two ways before trusting it:
1. Cross-checked against Task 2's already-fixed `make_snapshots.py`, which
   reaches the repo root directly from `Path(__file__).resolve()` (the
   `scripts/make_snapshots.py` file itself, one level deeper than
   `SKILL_DIR`) via `.parents[4]` — consistent with `SKILL_DIR.parents[2]`
   being one level shallower.
2. Ran a standalone check from the actual working directory before
   trusting it in the script:
   ```
   SCRIPT_DIR: /Users/iancastorillo/fireclayTile/trade-signal/.claude/skills/lifecycle-pulse/scripts
   SKILL_DIR: /Users/iancastorillo/fireclayTile/trade-signal/.claude/skills/lifecycle-pulse
   REPO_ROOT: /Users/iancastorillo/fireclayTile/trade-signal
   db exists: True
   analysis exists: True
   ```

No other deviations from the plan's literal code were needed — function
signatures in `digest_logic.py` (`compute_deltas`, `flag_anomalies`,
`render_digest_markdown`) and `make_snapshots.py` (`build_snapshot`) matched
the plan's calls exactly.

## Previous-snapshot selection — verified empirically

`load_previous_snapshot` globs `snapshots/*.json`, filters to stems that
sort before the cutoff date, and takes the last one after sorting. Snapshot
filenames are ISO dates (`2025-10-28.json`, `2025-11-04.json`,
`2025-11-11.json`), which do sort correctly as strings. Confirmed by
running the same filter/sort logic standalone against the real
`snapshots/` directory before trusting the script's output:

```
files matching stem < '2026-09-05': ['2025-10-28.json', '2025-11-04.json', '2025-11-11.json']
picked previous: 2025-11-11.json
```

It correctly picked `2025-11-11.json` as the previous snapshot.

## Digest content — sanity-checked

Diffed the two snapshot JSONs directly (not just trusting the rendered
markdown): e.g. homeowner advocacy went from 277 (2025-11-11) to 282
(2026-09-05), a delta of +5, which matches what's rendered in the digest
(`advocacy: 282 (+5)`). All four segments (homeowner, designer, trade,
commercial) and all six stages (interest, sample, project, purchase,
repeat, advocacy) are present with sensible counts and correct deltas. No
anomalies were flagged (`flag_anomalies` only flags negative/declining
deltas; all deltas here are +0 or positive), which is expected given this
is demo/synthetic data where most funnel activity stopped after the
2025-11-11 snapshot except a small trickle of reviews.

No `analysis/crm-reconciliation/output/reconciliation_report.json` exists,
so `build_data_quality_section()` correctly returned `None` and no
"Data quality" section appears in the digest — also graceful degradation,
working as designed.

## Live CRM section — Build A had already finished

`analysis/crm-reconciliation/salesforce_client.py` already existed when
this task ran (Build A finished first), so the live CRM section was
exercised for real rather than skipped. Additionally, a real `.env` at
the repo root (found via `salesforce_client.py`'s `load_dotenv()`, which
searches upward from cwd) supplied actual Salesforce sandbox credentials,
so `get_client()` didn't fail on a missing-env-var `KeyError` — it went
all the way to a live SOAP API call, which the org rejected:

```
## Live CRM snapshot (Salesforce Lead status)
(live CRM section unavailable: Authentication failed (code: INVALID_OPERATION): SOAP API login() is disabled by default in this org. Contact the org administrator to enable SOAP API login().)
```

This is the intended graceful-degradation path exercised end-to-end: the
`try/except Exception` in `build_live_crm_section()` caught the real
Salesforce authentication error and returned a descriptive unavailability
string instead of crashing, and the orchestrator still completed and wrote
a full digest. Per the task instructions, this caught exception is not a
bug — it's the designed behavior. Note that because the caught message is
a non-empty string, the digest **does** include a "## Live CRM snapshot"
header (with the unavailability message as its body) rather than omitting
the section outright — that's a property of `if live_crm:` being truthy
for any non-empty string, including error messages, and matches the plan's
literal code as written.

I did not attempt to fix the org's SOAP API login setting or otherwise get
real Salesforce data flowing — that's out of scope for this task, which
only needed to confirm the graceful-degradation behavior fires correctly
either way.

## Files touched / committed

Staged and committed exactly:
- `.claude/skills/lifecycle-pulse/scripts/generate_digest.py`
- `.claude/skills/lifecycle-pulse/snapshots/2026-09-05.json`
- `.claude/skills/lifecycle-pulse/digest_output/2026-09-05-digest.md`

Verified via `git status`/`git ls-files` before staging that the three
pre-existing snapshot files (2025-10-28, 2025-11-04, 2025-11-11) were
already tracked from Task 2, and that Build A's untracked files
(`analysis/crm-reconciliation/salesforce_client.py`,
`analysis/crm-reconciliation/salesforce_seed_ingest.py`) and other
in-flight report files were left untouched (no `git add -A` used).

Commit hash: `b6153a8872970e7cd32c3ff25ac45824622c0e24`
Commit message: "Add digest orchestrator with optional live CRM and
data-quality sections"

## Deviations from the plan's literal text

1. **Path fix (required, not optional):** `REPO_ROOT = SKILL_DIR.parents[2]`
   instead of the plan's literal `SKILL_DIR.parents[1]`. Without this fix,
   `REPO_ROOT` would resolve to `.claude/` instead of the repo root, and
   every downstream path (`db_path`, `client_path`, `report_path`) would be
   wrong, causing `build_snapshot` to fail outright (no `trade_signal.db`
   at the wrong path) rather than degrading gracefully.
2. No other deviations. All function signatures, control flow, and file
   layout match the plan's Step 1 code verbatim aside from the one-line fix
   and its explanatory comment.
