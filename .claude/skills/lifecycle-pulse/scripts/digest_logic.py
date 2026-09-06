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
