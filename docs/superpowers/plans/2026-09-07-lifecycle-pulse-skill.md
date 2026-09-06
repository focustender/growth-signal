# Lifecycle Pulse Claude Code Skill — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a real, git-committed Claude Code skill — `lifecycle-pulse` — that generates a recurring lifecycle/funnel digest: week-over-week deltas by segment and stage, anomaly flags, and (when reachable) a live HubSpot/Salesforce lifecycle-stage snapshot. Directly demonstrates the JD's "built skills, projects, agents... rely on AI for role optimization all day every day," since Claude is named in the JD's own tool list and this is a literal, runnable artifact rather than a narrated one.

**Architecture:** The funnel/segment digest data (interest -> sample -> project -> purchase -> repeat -> advocacy, by homeowner/designer/trade/commercial) always comes from `trade_signal.db` — it's the only source with real event-level history for all four segments. **Design refinement on the original spec:** HubSpot and Salesforce each hold one current `lifecyclestage`/`Status` value per contact, not funnel-event history, so they cannot actually substitute for the SQLite funnel data — treating them as a "fallback" for the same data would be dishonest about what they contain. Instead, a live CRM cross-reference is a distinct, optional supplementary section of the digest: current HubSpot `lifecyclestage` and Salesforce `Status` distributions for the trade/commercial segment, shown only when Build A's live connections are reachable, omitted gracefully otherwise. No real weeks are needed to demonstrate trend/anomaly detection: `make_snapshots.py` time-slices the existing event data at three real, 7-day-apart historical cutoffs.

**Tech Stack:** Python 3, `PyYAML`, `pytest`, `sqlite3` (stdlib), reuses Build A's `salesforce_client.py`/`hubspot_client.py` for the optional live CRM section (no code duplication).

**Spec:** `/Users/iancastorillo/.claude/plans/i-m-realizing-i-would-clever-canyon.md` (see "Build B" section). This plan refines that spec's "falls back to trade_signal.db" framing into "trade_signal.db is the primary/only source for funnel data; live CRM state is a separate, optional section" — see Architecture above.

## Global Constraints

- Working directory: `/Users/iancastorillo/fireclayTile/trade-signal`.
- Skill lives at `trade-signal/.claude/skills/lifecycle-pulse/`, committed to git — not a bare folder elsewhere, and not installed globally (see the approved spec's reasoning: a repo clone should auto-discover it).
- No Fireclay-specific field names hardcoded where avoidable — `config.yaml` externalizes thresholds and (for the optional CRM section) reuses Build A's own config pattern.
- Confirmed real schema (verified during planning, not assumed): `funnel_events(event_id, customer_id, event_type, event_date, sku_collection, channel, amount)` with `event_type` in `{site_visit, visualizer_use, sample_request, purchase, project_upload, repeat_purchase}`; `customers(customer_id, segment, source_channel, signup_date, region, company_name, email_opt_in)`; `reviews(customer_id, score, date)`. Real event-date range: **2024-01-01 to 2025-11-11** (not "Aug 2025" — that was an earlier guess, corrected here against the live database).
- Conversion-stage definitions must match `docs/measurement-foundation.md` exactly: Interest = `site_visit` or `visualizer_use`; Sample = `sample_request`; Project = `project_upload`; Purchase = `purchase`; Repeat = `repeat_purchase`; Advocacy = a `reviews` row for that customer.
- Every doc/output labels itself real/live vs. synthetic vs. simulated, per the project's honesty convention.
- Commit after each task passes its tests.

---

### Task 1: Digest logic core — deltas, anomalies, rendering (TDD)

**Files:**
- Create: `.claude/skills/lifecycle-pulse/scripts/digest_logic.py`
- Test: `.claude/skills/lifecycle-pulse/tests/test_digest_logic.py`
- Create: `.claude/skills/lifecycle-pulse/config.example.yaml`

**Interfaces:**
- Produces: `compute_deltas(current: dict, previous: dict) -> dict` — both args shaped `{"date": "YYYY-MM-DD", "segments": {"<segment>": {"<stage>": int, ...}, ...}}`; returns the same segment/stage shape but with delta ints (current minus previous; missing previous stage treated as 0).
- Produces: `flag_anomalies(deltas: dict, current: dict, threshold_pp: float) -> list[dict]` — flags a `{segment, stage, delta, current_rate_pp_or_note}` entry wherever a stage's conversion-rate-equivalent drop (delta as a percentage of the *previous* period's count for that segment/stage) exceeds `threshold_pp` percentage points in the negative direction. Convention: a stage with zero prior count and zero current count is never anomalous (0/0 is not a drop).
- Produces: `render_digest_markdown(current: dict, deltas: dict, anomalies: list, data_quality_section: str | None) -> str` — a markdown document; appends `data_quality_section` verbatim under a `## Data quality` heading only if not `None`.

- [ ] **Step 1: Write `config.example.yaml`**

```yaml
# Copy to config.yaml. anomaly_threshold_pp is in percentage points of
# decline (e.g. 5.0 means "flag any segment/stage whose count dropped
# 5%+ versus the prior snapshot").
anomaly_threshold_pp: 5.0
segments: [homeowner, designer, trade, commercial]
stages: [interest, sample, project, purchase, repeat, advocacy]
# Optional live CRM cross-reference section (Build A's connections).
# If either block's credentials aren't set, that block is skipped, not an error.
live_crm_section:
  enabled: true
```

- [ ] **Step 2: Write the failing tests**

```python
# .claude/skills/lifecycle-pulse/tests/test_digest_logic.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import digest_logic as dl

CURRENT = {
    "date": "2025-11-11",
    "segments": {
        "homeowner": {"interest": 1800, "sample": 1260, "project": 0, "purchase": 780, "repeat": 85, "advocacy": 210},
        "trade": {"interest": 560, "sample": 355, "project": 210, "purchase": 195, "repeat": 46, "advocacy": 30},
    },
}
PREVIOUS = {
    "date": "2025-11-04",
    "segments": {
        "homeowner": {"interest": 1790, "sample": 1250, "project": 0, "purchase": 770, "repeat": 84, "advocacy": 205},
        "trade": {"interest": 555, "sample": 350, "project": 208, "purchase": 220, "repeat": 46, "advocacy": 30},
    },
}

def test_compute_deltas_basic():
    deltas = dl.compute_deltas(CURRENT, PREVIOUS)
    assert deltas["segments"]["homeowner"]["sample"] == 10
    assert deltas["segments"]["trade"]["purchase"] == -25

def test_compute_deltas_missing_previous_stage_treated_as_zero():
    current = {"date": "2025-11-11", "segments": {"designer": {"interest": 50}}}
    previous = {"date": "2025-11-04", "segments": {"designer": {}}}
    deltas = dl.compute_deltas(current, previous)
    assert deltas["segments"]["designer"]["interest"] == 50

def test_flag_anomalies_detects_significant_drop():
    deltas = dl.compute_deltas(CURRENT, PREVIOUS)
    anomalies = dl.flag_anomalies(deltas, CURRENT, threshold_pp=5.0)
    flagged = {(a["segment"], a["stage"]) for a in anomalies}
    # trade/purchase: 220 -> 195 is a ~11.4% drop, over the 5.0pp threshold
    assert ("trade", "purchase") in flagged

def test_flag_anomalies_ignores_small_changes():
    deltas = dl.compute_deltas(CURRENT, PREVIOUS)
    anomalies = dl.flag_anomalies(deltas, CURRENT, threshold_pp=5.0)
    flagged = {(a["segment"], a["stage"]) for a in anomalies}
    # homeowner/sample: 1250 -> 1260 is a gain, never an anomaly
    assert ("homeowner", "sample") not in flagged

def test_flag_anomalies_zero_over_zero_is_not_anomalous():
    current = {"date": "2025-11-11", "segments": {"homeowner": {"project": 0}}}
    previous = {"date": "2025-11-04", "segments": {"homeowner": {"project": 0}}}
    deltas = dl.compute_deltas(current, previous)
    anomalies = dl.flag_anomalies(deltas, current, threshold_pp=5.0)
    assert anomalies == []

def test_render_digest_markdown_includes_date_and_omits_data_quality_when_none():
    deltas = dl.compute_deltas(CURRENT, PREVIOUS)
    anomalies = dl.flag_anomalies(deltas, CURRENT, threshold_pp=5.0)
    md = dl.render_digest_markdown(CURRENT, deltas, anomalies, data_quality_section=None)
    assert "2025-11-11" in md
    assert "Data quality" not in md

def test_render_digest_markdown_includes_data_quality_when_given():
    deltas = dl.compute_deltas(CURRENT, PREVIOUS)
    anomalies = dl.flag_anomalies(deltas, CURRENT, threshold_pp=5.0)
    md = dl.render_digest_markdown(CURRENT, deltas, anomalies, data_quality_section="3 new mismatches found.")
    assert "## Data quality" in md
    assert "3 new mismatches found." in md
```

- [ ] **Step 3: Run to verify failure**

Run: `cd .claude/skills/lifecycle-pulse && python3 -m pytest tests/test_digest_logic.py -v`
Expected: FAIL — module not found.

- [ ] **Step 4: Implement `scripts/digest_logic.py`**

```python
"""Pure functions for the Lifecycle Pulse digest: delta computation,
anomaly flagging, and markdown rendering. No I/O, no live-account
dependency -- everything here is testable against plain dicts."""


def compute_deltas(current: dict, previous: dict) -> dict:
    deltas = {"date": current["date"], "segments": {}}
    for segment, stages in current["segments"].items():
        prev_stages = previous.get("segments", {}).get(segment, {})
        deltas["segments"][segment] = {
            stage: count - prev_stages.get(stage, 0)
            for stage, count in stages.items()
        }
    return deltas


def flag_anomalies(deltas: dict, current: dict, threshold_pp: float) -> list:
    anomalies = []
    for segment, stages in deltas["segments"].items():
        for stage, delta in stages.items():
            if delta >= 0:
                continue
            current_count = current["segments"][segment][stage]
            previous_count = current_count - delta
            if previous_count == 0:
                continue
            drop_pct = (-delta / previous_count) * 100
            if drop_pct >= threshold_pp:
                anomalies.append({
                    "segment": segment, "stage": stage, "delta": delta,
                    "drop_pct": round(drop_pct, 1),
                })
    return anomalies


def render_digest_markdown(current: dict, deltas: dict, anomalies: list,
                            data_quality_section: str | None) -> str:
    lines = [f"# Lifecycle Pulse — {current['date']}", ""]
    if anomalies:
        lines.append("## Anomalies")
        for a in anomalies:
            lines.append(f"- **{a['segment']} / {a['stage']}**: down {a['drop_pct']}% ({a['delta']:+d})")
        lines.append("")
    lines.append("## Funnel by segment")
    for segment, stages in current["segments"].items():
        lines.append(f"### {segment.title()}")
        for stage, count in stages.items():
            delta = deltas["segments"].get(segment, {}).get(stage, 0)
            sign = "+" if delta >= 0 else ""
            lines.append(f"- {stage}: {count} ({sign}{delta})")
        lines.append("")
    if data_quality_section is not None:
        lines.append("## Data quality")
        lines.append(data_quality_section)
        lines.append("")
    return "\n".join(lines)
```

- [ ] **Step 5: Run to verify pass**

Run: `cd .claude/skills/lifecycle-pulse && python3 -m pytest tests/test_digest_logic.py -v`
Expected: 7 passed.

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/lifecycle-pulse/scripts/digest_logic.py .claude/skills/lifecycle-pulse/tests/ .claude/skills/lifecycle-pulse/config.example.yaml
git commit -m "Add Lifecycle Pulse digest logic core with passing test suite"
```

---

### Task 2: Snapshot builder — real backdated cutoffs from `trade_signal.db`

**Files:**
- Create: `.claude/skills/lifecycle-pulse/scripts/make_snapshots.py`
- Test: `.claude/skills/lifecycle-pulse/tests/test_make_snapshots.py`

**Interfaces:**
- Produces: `build_snapshot(db_path: str, cutoff_date: str) -> dict` returning `{"date": cutoff_date, "segments": {segment: {stage: count, ...}, ...}}` for all 4 segments x 6 stages, counting only `funnel_events`/`reviews` rows with `event_date`/`date` <= `cutoff_date`, joined to `customers` for segment.

- [ ] **Step 1: Write the failing test**

```python
# .claude/skills/lifecycle-pulse/tests/test_make_snapshots.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import make_snapshots as ms

DB_PATH = str(Path(__file__).resolve().parents[3] / "data" / "trade_signal.db")

def test_build_snapshot_has_all_segments_and_stages():
    snapshot = ms.build_snapshot(DB_PATH, "2025-11-11")
    assert snapshot["date"] == "2025-11-11"
    for segment in ("homeowner", "designer", "trade", "commercial"):
        for stage in ("interest", "sample", "project", "purchase", "repeat", "advocacy"):
            assert stage in snapshot["segments"][segment]

def test_build_snapshot_counts_grow_with_later_cutoff():
    early = ms.build_snapshot(DB_PATH, "2024-06-01")
    late = ms.build_snapshot(DB_PATH, "2025-11-11")
    # cumulative counts can only stay the same or grow with a later cutoff
    assert late["segments"]["homeowner"]["purchase"] >= early["segments"]["homeowner"]["purchase"]

def test_build_snapshot_project_stage_near_zero_outside_trade_commercial():
    snapshot = ms.build_snapshot(DB_PATH, "2025-11-11")
    # measurement-foundation.md: project_upload is a trade/commercial-only event
    assert snapshot["segments"]["homeowner"]["project"] == 0

def test_three_snapshots_are_seven_days_apart_and_distinct():
    cutoffs = ms.three_weekly_cutoffs(end_date="2025-11-11")
    assert cutoffs == ["2025-10-28", "2025-11-04", "2025-11-11"]
```

- [ ] **Step 2: Run to verify failure**

Run: `cd .claude/skills/lifecycle-pulse && python3 -m pytest tests/test_make_snapshots.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `scripts/make_snapshots.py`**

```python
"""Builds a lifecycle funnel snapshot as of a given cutoff date by
querying trade_signal.db directly. Also provides three_weekly_cutoffs,
used to generate backdated demonstration snapshots without waiting
real weeks."""
import sqlite3
from datetime import date, timedelta

STAGE_EVENT_TYPES = {
    "interest": ("site_visit", "visualizer_use"),
    "sample": ("sample_request",),
    "project": ("project_upload",),
    "purchase": ("purchase",),
    "repeat": ("repeat_purchase",),
}
SEGMENTS = ("homeowner", "designer", "trade", "commercial")


def build_snapshot(db_path: str, cutoff_date: str) -> dict:
    conn = sqlite3.connect(db_path)
    segments = {}
    for segment in SEGMENTS:
        stages = {}
        for stage, event_types in STAGE_EVENT_TYPES.items():
            placeholders = ",".join("?" for _ in event_types)
            query = f"""
                SELECT COUNT(DISTINCT fe.customer_id)
                FROM funnel_events fe
                JOIN customers c ON c.customer_id = fe.customer_id
                WHERE c.segment = ? AND fe.event_type IN ({placeholders})
                  AND fe.event_date <= ?
            """
            cur = conn.execute(query, (segment, *event_types, cutoff_date))
            stages[stage] = cur.fetchone()[0]
        cur = conn.execute("""
            SELECT COUNT(DISTINCT r.customer_id)
            FROM reviews r
            JOIN customers c ON c.customer_id = r.customer_id
            WHERE c.segment = ? AND r.date <= ?
        """, (segment, cutoff_date))
        stages["advocacy"] = cur.fetchone()[0]
        segments[segment] = stages
    conn.close()
    return {"date": cutoff_date, "segments": segments}


def three_weekly_cutoffs(end_date: str) -> list:
    end = date.fromisoformat(end_date)
    return [(end - timedelta(days=14)).isoformat(),
            (end - timedelta(days=7)).isoformat(),
            end.isoformat()]


if __name__ == "__main__":
    import json
    from pathlib import Path
    db_path = str(Path(__file__).resolve().parents[3] / "data" / "trade_signal.db")
    out_dir = Path(__file__).resolve().parents[1] / "snapshots"
    out_dir.mkdir(exist_ok=True)
    for cutoff in three_weekly_cutoffs("2025-11-11"):
        snapshot = build_snapshot(db_path, cutoff)
        with open(out_dir / f"{cutoff}.json", "w") as f:
            json.dump(snapshot, f, indent=2)
        print(f"Wrote {cutoff}.json — {snapshot}")
```

- [ ] **Step 4: Run to verify pass**

Run: `cd .claude/skills/lifecycle-pulse && python3 -m pytest tests/test_make_snapshots.py -v`
Expected: 4 passed. If `test_build_snapshot_project_stage_near_zero_outside_trade_commercial` fails because homeowner has a nonzero `project` count, check whether `docs/measurement-foundation.md`'s claim ("Project — trade/commercial only") is actually enforced in `data/generate_dataset.py` or merely a documentation note; if the live data disagrees with the doc, trust the live data, fix this test's assertion to match reality, and note the discrepancy in your final report rather than silently loosening it.

- [ ] **Step 5: Generate the three real backdated snapshots**

Run: `cd .claude/skills/lifecycle-pulse && python3 scripts/make_snapshots.py`
Expected: writes `snapshots/2025-10-28.json`, `snapshots/2025-11-04.json`, `snapshots/2025-11-11.json`. These are **simulated** in the sense that they're backdated re-derivations of historical cutoffs computed today, not captured in real time week-over-week — label them this way in Task 4's README, not as "live."

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/lifecycle-pulse/scripts/make_snapshots.py .claude/skills/lifecycle-pulse/tests/test_make_snapshots.py .claude/skills/lifecycle-pulse/snapshots/
git commit -m "Add snapshot builder and generate three backdated demo snapshots"
```

---

### Task 3: Digest orchestrator + optional live CRM section

**Files:**
- Create: `.claude/skills/lifecycle-pulse/scripts/generate_digest.py`
- Create: `.claude/skills/lifecycle-pulse/digest_output/` (populated by running it, see Step 4)

**Interfaces:**
- Consumes: `digest_logic.py` (Task 1), `make_snapshots.py`'s `build_snapshot` (Task 2), optionally `analysis/crm-reconciliation/salesforce_client.py` and `hubspot_client.py` (Build A, if that plan has landed — check whether `analysis/crm-reconciliation/salesforce_client.py` exists before importing it; if it doesn't yet, skip the live CRM section entirely rather than failing, per this task's whole point of graceful degradation) and `analysis/crm-reconciliation/output/reconciliation_report.json` (for the data-quality section).
- Produces: a runnable script that writes one new digest to `digest_output/<date>-digest.md`.

- [ ] **Step 1: Implement `scripts/generate_digest.py`**

```python
"""Orchestrates one Lifecycle Pulse run: builds today's snapshot,
loads the most recent prior snapshot, computes deltas/anomalies,
optionally appends a live CRM cross-reference and a data-quality
section, and writes the digest."""
import json
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REPO_ROOT = SKILL_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))
import digest_logic as dl
import make_snapshots as ms


def load_previous_snapshot(snapshots_dir: Path, before_date: str) -> dict | None:
    files = sorted(p for p in snapshots_dir.glob("*.json") if p.stem < before_date)
    if not files:
        return None
    with open(files[-1]) as f:
        return json.load(f)


def build_data_quality_section() -> str | None:
    report_path = REPO_ROOT / "analysis" / "crm-reconciliation" / "output" / "reconciliation_report.json"
    if not report_path.exists():
        return None
    with open(report_path) as f:
        report = json.load(f)
    s = report["summary"]
    return (f"{s['stage_mismatch_count']} lifecycle-stage mismatches, "
            f"{s['hubspot_only_count']} HubSpot-only records, "
            f"{s['salesforce_only_count']} Salesforce-only records "
            f"across {s['matched_count']} matched cross-system contacts "
            f"(see analysis/crm-reconciliation/output/reconciliation_findings.md).")


def build_live_crm_section() -> str | None:
    client_path = REPO_ROOT / "analysis" / "crm-reconciliation" / "salesforce_client.py"
    if not client_path.exists():
        return None
    try:
        sys.path.insert(0, str(client_path.parent))
        from salesforce_client import get_client
        sf = get_client()
        result = sf.query("SELECT Status, COUNT(Id) cnt FROM Lead WHERE Email LIKE '%@example.com' GROUP BY Status")
        return "\n".join(f"- {r['Status']}: {r['cnt']}" for r in result["records"])
    except Exception as exc:
        return f"(live CRM section unavailable: {exc})"


def run(cutoff_date: str | None = None) -> Path:
    cutoff_date = cutoff_date or date.today().isoformat()
    db_path = str(REPO_ROOT / "data" / "trade_signal.db")
    snapshots_dir = SKILL_DIR / "snapshots"
    output_dir = SKILL_DIR / "digest_output"
    output_dir.mkdir(exist_ok=True)

    current = ms.build_snapshot(db_path, cutoff_date)
    previous = load_previous_snapshot(snapshots_dir, cutoff_date) or {"date": None, "segments": {}}
    deltas = dl.compute_deltas(current, previous)
    anomalies = dl.flag_anomalies(deltas, current, threshold_pp=5.0)
    data_quality = build_data_quality_section()
    digest_md = dl.render_digest_markdown(current, deltas, anomalies, data_quality)

    live_crm = build_live_crm_section()
    if live_crm:
        digest_md += f"\n## Live CRM snapshot (Salesforce Lead status)\n{live_crm}\n"

    with open(snapshots_dir / f"{cutoff_date}.json", "w") as f:
        json.dump(current, f, indent=2)
    out_path = output_dir / f"{cutoff_date}-digest.md"
    with open(out_path, "w") as f:
        f.write(digest_md)
    return out_path


if __name__ == "__main__":
    path = run()
    print(f"Wrote {path}")
```

- [ ] **Step 2: Run it for real**

Run: `cd .claude/skills/lifecycle-pulse && python3 scripts/generate_digest.py`
Expected: writes `snapshots/<today>.json` and `digest_output/<today>-digest.md`. This is the **one genuinely live-executed run** — label it that way explicitly in the README (Task 4), distinct from the three backdated/simulated snapshots from Task 2. If Build A's `analysis/crm-reconciliation/salesforce_client.py` doesn't exist yet when this runs, the digest should still be produced successfully, just without a "Live CRM snapshot" section — confirm this actually happens (temporarily rename or check for the file's absence) rather than assuming the `if client_path.exists()` branch works correctly.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/lifecycle-pulse/scripts/generate_digest.py .claude/skills/lifecycle-pulse/digest_output/ .claude/skills/lifecycle-pulse/snapshots/
git commit -m "Add digest orchestrator with optional live CRM and data-quality sections"
```

---

### Task 4: SKILL.md, README, and final wiring

**Files:**
- Create: `.claude/skills/lifecycle-pulse/SKILL.md`
- Create: `.claude/skills/lifecycle-pulse/README.md`
- Modify: `site/case-study.html` (one new card/section, matching Build A's site integration)
- Modify: `README.md` (repo root — already references this skill's path; confirm it's accurate now that the skill exists)

- [ ] **Step 1: Write `SKILL.md`**

```markdown
---
name: lifecycle-pulse
description: Generate a week-over-week lifecycle/funnel digest (interest, sample, project, purchase, repeat, advocacy) by customer segment, with anomaly flags and optional live HubSpot/Salesforce lifecycle-stage cross-reference. Use when asked for a lifecycle report, funnel digest, or growth/retention snapshot.
---

# Lifecycle Pulse

Run `python3 scripts/generate_digest.py` from this directory to produce a new digest in `digest_output/`. See `README.md` for what it does and how to adapt it to a different HubSpot/Salesforce setup.
```

- [ ] **Step 2: Write `README.md`**

Cover: what this skill does (one paragraph); the honesty labeling for what's real (the CRM connections when reachable, the one digest run recorded with today's real date) vs. simulated (the three backdated snapshots, explicitly time-sliced from historical data, not captured in real time); how to adapt it — copy `config.example.yaml` to `config.yaml`, point `segments`/`stages` at your own funnel model, and reimplement `make_snapshots.py`'s `build_snapshot` against your own data source (SQL warehouse, another CRM, an events API) since that's the only piece genuinely specific to this project's schema; the loose coupling with the CRM reconciliation tool in `analysis/crm-reconciliation/` (present only if that's been run — this skill degrades gracefully without it).

- [ ] **Step 3: Update `site/case-study.html`**

Add one card to "The two design artifacts" grid (or a new small section near Build A's) describing Lifecycle Pulse, linking to `.claude/skills/lifecycle-pulse/README.md` and to one of the checked-in `digest_output/*.md` files as a live example a reviewer can read without running anything.

- [ ] **Step 4: Confirm the root `README.md`'s existing reference is accurate**

It already says: "check `.claude/skills/lifecycle-pulse/README.md` for their own status" — no change needed unless this task's README ended up at a different path.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/lifecycle-pulse/SKILL.md .claude/skills/lifecycle-pulse/README.md site/case-study.html
git commit -m "Document Lifecycle Pulse skill and link it from the case study"
```

---

## Self-Review Notes (completed during plan authoring)

- **Spec coverage:** digest generation, anomaly detection, snapshot strategy, portability/config, honesty labeling, and site integration are all covered.
- **Design refinement over the original spec:** HubSpot/Salesforce reframed from "fallback data source" to "optional supplementary section," since they don't actually hold funnel-event history in this data model — see Architecture note above.
- **Schema verified, not assumed:** `funnel_events`'s real event types and the real 2024-01-01 to 2025-11-11 date range were checked against the live database during planning, not guessed from an earlier session's stale note (which had assumed "Aug 2025").
- **Graceful degradation is tested for, not just claimed:** Task 3, Step 2 explicitly requires confirming the no-Build-A-yet case actually works, not assuming the `if` branch is correct.
