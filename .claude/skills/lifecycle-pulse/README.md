# Lifecycle Pulse

A Claude Code skill that generates a week-over-week lifecycle/funnel digest — interest, sample, project, purchase, repeat, advocacy — broken out by customer segment (homeowner, designer, trade, commercial), with automatic anomaly flags where a segment/stage count drops more than a configurable threshold versus the prior snapshot. `scripts/digest_logic.py` holds the pure delta/anomaly/rendering logic (tested in isolation, no I/O); `scripts/make_snapshots.py` builds a funnel snapshot as of any cutoff date by querying `trade_signal.db` directly; `scripts/generate_digest.py` orchestrates a full run — build today's snapshot, load the most recent prior one, compute deltas, flag anomalies, optionally append a live CRM cross-reference and a data-quality section, and write the result to `digest_output/`.

## What's real, what's simulated

This project labels every artifact against the same three categories the repo root README uses. Lifecycle Pulse only ever touches the first and third:

- **Real / live.** `digest_output/2026-09-05-digest.md` is the one genuinely live-executed run — produced by actually running `generate_digest.py` on that date against the live `trade_signal.db`, not hand-written. It also shows the live CRM cross-reference actually being attempted against the real Salesforce org: the digest includes the line `(live CRM section unavailable: Authentication failed (code: INVALID_OPERATION): SOAP API login() is disabled by default in this org...)`. That's a real error from a real API call, left in rather than suppressed or faked into a success — `build_live_crm_section()` in `generate_digest.py` catches the exception and reports it verbatim instead of silently omitting the section, which is deliberate: a digest that goes quiet on a broken integration is worse than one that says so.
- **Simulated.** `snapshots/2025-10-28.json`, `snapshots/2025-11-04.json`, and `snapshots/2025-11-11.json` are backdated re-derivations of real historical data — `make_snapshots.py` time-slices the actual `funnel_events`/`reviews` tables at three cutoffs exactly 7 days apart, so every count in them is real, but they weren't captured in real time week over week. They exist to prove the delta/anomaly logic works across weekly cadence without waiting three real weeks. Any digest that diffs against one of these (rather than another live run) inherits that same "simulated cadence, real underlying counts" label.

Nothing here fabricates funnel counts. The only simulated part is the *timing* — running the same real query against the same real database at three different pretend "today"s instead of three actual Mondays.

## Adapting this to a different setup

The parts of this skill that are genuinely specific to Trade Signal's schema and the parts that aren't split cleanly:

1. Copy `config.example.yaml` to `config.yaml`. Point `segments` and `stages` at your own funnel model, and set `anomaly_threshold_pp` to whatever decline you'd actually want flagged.
2. Reimplement `make_snapshots.py`'s `build_snapshot(db_path, cutoff_date)` against your own data source — a SQL warehouse, a different CRM's API, an events pipeline. This is the only function that knows about `funnel_events`, `customers`, `reviews`, or SQLite at all. Everything downstream of it (`digest_logic.py`'s `compute_deltas`, `flag_anomalies`, `render_digest_markdown`, and `generate_digest.py`'s orchestration) only ever sees the shape `{"date": ..., "segments": {segment: {stage: count}}}` and doesn't care where it came from.
3. One honest gap as of this writing: `config.yaml` is a documented convention, not yet a wired-in one. `generate_digest.py` currently hardcodes `threshold_pp=5.0` rather than reading it from config, and `make_snapshots.py`'s segment/stage list lives in its own `SEGMENTS`/`STAGE_EVENT_TYPES` constants rather than being loaded from `config.yaml`. Adapting the threshold or stage list today means editing those in code; wiring `config.yaml` in for real (a `yaml.safe_load` at the top of `generate_digest.py`) is a small, obvious next step, not yet done.
4. If you have a different CRM (or none), edit or delete `build_live_crm_section()` in `generate_digest.py`. It's already written to degrade gracefully — no client module present, no credentials, or a live API error all fall through to "digest produced, CRM section just omitted or shows the error" rather than a hard failure.

## Loose coupling with `analysis/crm-reconciliation/`

`generate_digest.py` checks for two things from Build A (the HubSpot↔Salesforce reconciliation project) at run time, both optional:

- `analysis/crm-reconciliation/salesforce_client.py` — if present, `build_live_crm_section()` imports it and queries live Salesforce Lead status counts for the digest's "Live CRM snapshot" section. If it's not there, that section is skipped, not an error.
- `analysis/crm-reconciliation/output/reconciliation_report.json` — if present, `build_data_quality_section()` reads its `summary` block (stage mismatches, HubSpot-only/Salesforce-only counts, matched-contact count) and appends a `## Data quality` section citing `analysis/crm-reconciliation/output/reconciliation_findings.md`.

As of this writing, `analysis/crm-reconciliation/output/` doesn't exist yet — that build is still in progress — so the checked-in `digest_output/2026-09-05-digest.md` has no `## Data quality` section, only the live (failed) CRM snapshot from the client file that does already exist. Once Build A finishes and writes its `output/reconciliation_report.json`, the next `generate_digest.py` run will pick it up automatically with no changes needed on this side — that's the point of the coupling being a file-existence check rather than a hard import or a shared config flag.
