# Task 2 Report — Snapshot builder (real backdated cutoffs from `trade_signal.db`)

## What was done

1. Wrote the failing test file `.claude/skills/lifecycle-pulse/tests/test_make_snapshots.py` exactly as given in Task 2 Step 1 (4 tests: all-segments/all-stages coverage, counts grow with later cutoff, project stage near-zero outside trade/commercial, three-weekly-cutoffs correctness).
2. Ran it and confirmed the expected failure: `ModuleNotFoundError: No module named 'make_snapshots'` (module not found, as predicted by Step 2).
3. Implemented `.claude/skills/lifecycle-pulse/scripts/make_snapshots.py` per Task 2 Step 3's code block, with one corrected line (see Deviation below).
4. Ran the test suite — after fixing the path bug, all 4 passed (see exact output below).
5. Ran the script's entry point (`python3 scripts/make_snapshots.py`) to generate the three real backdated snapshots.
6. Sanity-checked all 24 segment/stage combinations across the three snapshot dates for monotonic non-decrease.
7. Staged and committed exactly the 5 intended files (script, test, three snapshot JSONs). No other files were staged.

## Deviation from the plan's literal text (with justification)

**The plan's code as written does not work.** Both the test file's `DB_PATH` line and the script's `__main__` block's `db_path` line use:

```python
Path(__file__).resolve().parents[3] / "data" / "trade_signal.db"
```

Verified path depth by direct computation:

- For the test file at `.claude/skills/lifecycle-pulse/tests/test_make_snapshots.py`: `parents[3]` resolves to `.../trade-signal/.claude` (not the repo root), so the constructed path is `.claude/data/trade_signal.db`, which does not exist.
- For the script at `.claude/skills/lifecycle-pulse/scripts/make_snapshots.py`: same problem, `parents[3]` also lands on `.../trade-signal/.claude`.
- The actual database lives at `/Users/iancastorillo/fireclayTile/trade-signal/data/trade_signal.db`, i.e. the repo root, which is `parents[4]` from both file locations (tests dir: tests -> lifecycle-pulse -> skills -> .claude -> trade-signal is 4 levels; scripts dir: scripts -> lifecycle-pulse -> skills -> .claude -> trade-signal is also 4 levels).

With the plan's literal `parents[3]`, running the test suite against the implemented module failed 3 of 4 tests with `sqlite3.OperationalError: unable to open database file` (only `test_three_snapshots_are_seven_days_apart_and_distinct`, which never touches the database, passed). This is a distinct, unambiguous off-by-one bug — not the segment-count assumption the plan's own caveat anticipated — so per the task instructions ("something in your implementation differs from the plan's code, not the plan being wrong" applies specifically to the project-stage test/live-db caveat; this is a separate, structural path bug), I corrected `parents[3]` to `parents[4]` in both files and proceeded. This was verified against the live filesystem before changing anything (see `find`/`ls` output during the session).

No other deviations. Everything else — `STAGE_EVENT_TYPES`, `SEGMENTS`, the `build_snapshot` SQL, `three_weekly_cutoffs`, and the `__main__` snapshot-writing loop — matches the plan's code verbatim.

## Exact test output (after the path fix)

```
$ cd .claude/skills/lifecycle-pulse && python3 -m pytest tests/test_make_snapshots.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0 -- /opt/miniconda3/bin/python3
cachedir: .pytest_cache
rootdir: /Users/iancastorillo/fireclayTile/trade-signal/.claude/skills/lifecycle-pulse
plugins: anyio-4.12.1
collecting ... collected 4 items

tests/test_make_snapshots.py::test_build_snapshot_has_all_segments_and_stages PASSED [ 25%]
tests/test_make_snapshots.py::test_build_snapshot_counts_grow_with_later_cutoff PASSED [ 50%]
tests/test_make_snapshots.py::test_build_snapshot_project_stage_near_zero_outside_trade_commercial PASSED [ 75%]
tests/test_make_snapshots.py::test_three_snapshots_are_seven_days_apart_and_distinct PASSED [100%]

============================== 4 passed in 0.09s ===============================
```

The `test_build_snapshot_project_stage_near_zero_outside_trade_commercial` test passed as written — no need to invoke the live sqlite spot-check on segment/`project_upload` counts, since the plan's assumption (only trade and commercial segments have `project_upload` events) held with this implementation.

## Commit

- Hash: `f0c541f030003b5a6a45f783b46e85939071e5c9`
- Message: "Add snapshot builder and generate three backdated demo snapshots" (plus a note in the body about the parents[3]→parents[4] fix)
- Files committed (exactly these 5, verified via `git status --short` before commit):
  - `.claude/skills/lifecycle-pulse/scripts/make_snapshots.py`
  - `.claude/skills/lifecycle-pulse/tests/test_make_snapshots.py`
  - `.claude/skills/lifecycle-pulse/snapshots/2025-10-28.json`
  - `.claude/skills/lifecycle-pulse/snapshots/2025-11-04.json`
  - `.claude/skills/lifecycle-pulse/snapshots/2025-11-11.json`

## Snapshot counts (raw output from the script run)

```
Wrote 2025-10-28.json — {'date': '2025-10-28', 'segments': {
  'homeowner': {'interest': 1769, 'sample': 1252, 'project': 0, 'purchase': 766, 'repeat': 83, 'advocacy': 272},
  'designer':  {'interest': 662,  'sample': 498,  'project': 0, 'purchase': 402, 'repeat': 80, 'advocacy': 115},
  'trade':     {'interest': 558,  'sample': 352,  'project': 115, 'purchase': 190, 'repeat': 45, 'advocacy': 58},
  'commercial':{'interest': 211,  'sample': 88,   'project': 34,  'purchase': 72,  'repeat': 13, 'advocacy': 15}}}

Wrote 2025-11-04.json — {'date': '2025-11-04', 'segments': {
  'homeowner': {'interest': 1769, 'sample': 1252, 'project': 0, 'purchase': 766, 'repeat': 83, 'advocacy': 275},
  'designer':  {'interest': 662,  'sample': 498,  'project': 0, 'purchase': 402, 'repeat': 80, 'advocacy': 116},
  'trade':     {'interest': 558,  'sample': 352,  'project': 115, 'purchase': 190, 'repeat': 45, 'advocacy': 58},
  'commercial':{'interest': 211,  'sample': 88,   'project': 34,  'purchase': 72,  'repeat': 13, 'advocacy': 15}}}

Wrote 2025-11-11.json — {'date': '2025-11-11', 'segments': {
  'homeowner': {'interest': 1769, 'sample': 1252, 'project': 0, 'purchase': 768, 'repeat': 83, 'advocacy': 277},
  'designer':  {'interest': 662,  'sample': 498,  'project': 0, 'purchase': 402, 'repeat': 80, 'advocacy': 117},
  'trade':     {'interest': 558,  'sample': 352,  'project': 115, 'purchase': 191, 'repeat': 45, 'advocacy': 58},
  'commercial':{'interest': 211,  'sample': 88,   'project': 34,  'purchase': 72,  'repeat': 13, 'advocacy': 15}}}
```

### Spot-check: non-decreasing counts across the three cutoffs

Beyond the test-covered `homeowner`/`purchase` (766 -> 766 -> 768, non-decreasing), spot-checked:

- `homeowner` / `advocacy`: 272 -> 275 -> 277 (increasing)
- `designer` / `advocacy`: 115 -> 116 -> 117 (increasing)
- `trade` / `purchase`: 190 -> 190 -> 191 (increasing)

A full programmatic check of all 24 segment x stage combinations across the three files confirmed every one is non-decreasing (most are flat, several increase slightly, none decrease). This matches expectations for cumulative-count snapshots taken at progressively later cutoffs.

## Note per Task 2 Step 5's contingency instructions

The contingency ("if `test_build_snapshot_project_stage_near_zero_outside_trade_commercial` fails, check `docs/measurement-foundation.md` vs `data/generate_dataset.py`") did not trigger — that test passed cleanly with `homeowner['project'] == 0` at the 2025-11-11 cutoff, consistent with the plan's live-database verification that only trade (115) and commercial (34) segments have any `project_upload` events.
