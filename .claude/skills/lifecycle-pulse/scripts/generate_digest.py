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
# SKILL_DIR is .claude/skills/lifecycle-pulse (3 path segments below repo
# root: .claude, skills, lifecycle-pulse), so parents[2] -- not parents[1]
# -- is the repo root. parents[0] would be .../skills and parents[1] would
# be .../.claude, both still inside .claude. (Confirmed against
# make_snapshots.py, which reaches the same repo root via
# Path(__file__).resolve().parents[4] directly from scripts/.)
REPO_ROOT = SKILL_DIR.parents[2]
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
