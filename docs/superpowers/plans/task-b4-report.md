# Task 4 report: SKILL.md, README, and final wiring

**Commit:** `31edff6` — "Document Lifecycle Pulse skill and link it from the case study"

## What was done

1. Read Task 4's full text from `docs/superpowers/plans/2026-09-07-lifecycle-pulse-skill.md` (lines 449-487).

2. Wrote `.claude/skills/lifecycle-pulse/SKILL.md` verbatim from the plan's Step 1 code block — front matter (`name`, `description`) and the one-line usage instruction, unchanged.

3. Wrote `.claude/skills/lifecycle-pulse/README.md`. Before writing it, read the actual committed artifacts rather than restating the plan's prose:
   - `config.example.yaml` — confirmed its fields (`anomaly_threshold_pp`, `segments`, `stages`, `live_crm_section.enabled`).
   - `scripts/generate_digest.py` — confirmed it hardcodes `threshold_pp=5.0` and never reads `config.yaml` at all; `make_snapshots.py`'s `SEGMENTS`/`STAGE_EVENT_TYPES` constants are likewise not sourced from config. This is a real gap between the documented convention and the wired code, called out honestly in the README's "Adapting this to a different setup" section (point 3) rather than glossed over.
   - `digest_output/2026-09-05-digest.md` — confirmed it's the one live-executed run, and that its "Live CRM snapshot" section contains a real (not fabricated) Salesforce auth failure: `SOAP API login() is disabled by default in this org`. The README describes this explicitly as a real failed API call left in rather than hidden, per `build_live_crm_section()`'s actual exception-handling behavior in `generate_digest.py`.
   - `docs/hubspot-setup.md` and `visualizer/README.md` — read first to match this project's established tone for the real/synthetic/simulated honesty labeling (direct, technical, willing to state gaps and failures plainly rather than smoothing them over).
   - `analysis/crm-reconciliation/` — checked for `output/reconciliation_findings.md` / `output/reconciliation_report.json`; neither exists yet (Build A is still in progress concurrently — confirmed via `git status` and `ls`, and via the presence of untracked `analysis/crm-reconciliation/hubspot_client.py` / `extract_hubspot.py`). The README's "Loose coupling" section states this current state explicitly (no `## Data quality` section yet in the checked-in digest) rather than assuming Build A had landed.

4. Updated `site/case-study.html`. Read the file in full first. Found four existing cards already in "The two design artifacts" `.grid-two` grid (Sample Kit Builder, Room Visualizer, Figma spec, Shopify preview) — no pre-existing "Build A" card/section to match, since CRM reconciliation hasn't reached its own site integration yet. Added a new, separate `<section>` titled "Lifecycle Pulse" positioned between that grid and "Build status," using only existing classes (`section-sub`, `grid-two`, `deliverable`, `kicker`, `link-btn`) — no new CSS. The card has two `link-btn` anchors (existing single-link cards only needed one, but nothing in the CSS prevents two, and this card needs both a README link and a live-example link): one to `../.claude/skills/lifecycle-pulse/README.md`, one to `../.claude/skills/lifecycle-pulse/digest_output/2026-09-05-digest.md`.

5. Confirmed the root `README.md`'s existing line — "check `analysis/crm-reconciliation/README.md` and `.claude/skills/lifecycle-pulse/README.md` for their own status" (line 43) — is accurate now that `.claude/skills/lifecycle-pulse/README.md` exists at exactly that path. No edit made.

6. Staged and committed exactly `.claude/skills/lifecycle-pulse/SKILL.md`, `.claude/skills/lifecycle-pulse/README.md`, `site/case-study.html` — verified via `git status --short` before committing that no other files were staged. Did not use `git add -A`.

## Deviations from the plan's literal text, with justification

- **Site integration placement:** the plan's Step 3 said "Add one card to 'The two design artifacts' grid (or a new small section near Build A's)." Since Build A has no site section yet (its `output/` directory doesn't exist, confirmed above), there was nothing to place "near." Also, that grid's own subheading ("Both are live, interactive Claude artifacts — not screenshots") describes claude.ai/Figma/Shopify-hosted design artifacts, not a repo-local analytics skill, so folding Lifecycle Pulse into that same grid would have misdescribed it. I used the plan's explicit fallback ("a new small section") instead — a new `<section>` reusing the identical `grid-two`/`deliverable` pattern, placed directly after the design-artifacts section and before "Build status." This satisfies the parent task's literal instruction ("Add one new card... Match the existing HTML/CSS structure and tone exactly") without misplacing it.
- **Two `link-btn` anchors in one card** instead of the one-per-card pattern every existing card uses. Required because the task explicitly asks for both a README link and a live digest-file link, and the existing CSS (`.link-btn { display:inline-block; ... }`) already supports multiple instances without modification — no new CSS was added or needed.
- **README content beyond the plan's four bullet topics:** included the concrete detail that `config.yaml` is not actually wired into `generate_digest.py`/`make_snapshots.py` yet (values are hardcoded in the scripts). This wasn't explicitly called for in the plan's Step 2 prose, but the parent task instruction required reading the actual files "so the README accurately describes what's really there rather than restating the plan's prose" — and this is a real, verifiable discrepancy between the documented config convention and the current code, worth surfacing under "how to adapt" rather than letting a reader assume config.yaml already works.
- No changes made to root `README.md` (confirmed accurate, per plan Step 4 — this is not a deviation, just confirming no edit was warranted).

## Verification

- `python3 -m pytest tests/ -q` from `.claude/skills/lifecycle-pulse/` — 11 passed (before this task's changes; Task 4 added no code, so this remained the state throughout).
- `git status --short` immediately before commit showed exactly the three intended files staged, plus Build A's own concurrent untracked files (`analysis/crm-reconciliation/hubspot_client.py`, `analysis/crm-reconciliation/extract_hubspot.py`) correctly left untouched.
- `git log --oneline -3` after commit: `31edff6 Document Lifecycle Pulse skill and link it from the case study` (Build A's own commit `6de5658` landed concurrently in between the branch's prior tip and this commit, confirming Build A is progressing in parallel as expected — it did not interfere with this task's file set).
