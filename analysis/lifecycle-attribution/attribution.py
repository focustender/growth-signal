"""Generic lifecycle-program attribution: for a set of engagement
records (a program touch with an open/click flag) and a set of
downstream value events (an amount tied to a date), computes both the
platform metric a program is normally judged on (open/click rate) and
the real commercial outcome (purchase rate and $ value after the send,
engaged vs. unengaged recipients) per program -- then flags where the
two disagree on which program matters most. No Fireclay-specific field
names or program names; takes plain dicts."""
from collections import defaultdict
from datetime import datetime, timedelta


def _parse(d):
    return datetime.strptime(d, "%Y-%m-%d") if isinstance(d, str) else d


def platform_metrics(engagements):
    """engagements: iterable of {program, opened, clicked}.
    Returns {program: {sent, opened, clicked, open_rate, click_rate}}."""
    agg = defaultdict(lambda: {"sent": 0, "opened": 0, "clicked": 0})
    for e in engagements:
        a = agg[e["program"]]
        a["sent"] += 1
        a["opened"] += int(bool(e["opened"]))
        a["clicked"] += int(bool(e["clicked"]))
    return {
        program: {
            **a,
            "open_rate": a["opened"] / a["sent"] if a["sent"] else 0.0,
            "click_rate": a["clicked"] / a["sent"] if a["sent"] else 0.0,
        }
        for program, a in agg.items()
    }


def commercial_outcomes(engagements, value_events, window_days=None, engagement_flag="opened"):
    """engagements: iterable of {customer_id, program, sent_date, opened, clicked}.
    value_events: iterable of {customer_id, event_date, amount} -- any
    downstream event worth crediting (a purchase, a repeat purchase).

    For each program, splits recipients into engaged / unengaged by
    whether `engagement_flag` was ever true across their sends of that
    program, then credits each customer with the total value of events
    on or after their earliest send of that program (optionally capped
    at `window_days` later). Customers with no qualifying event count
    as $0, not excluded -- a program's real value includes the people
    it failed to move.

    Returns {program: {engaged: {n, purchase_rate, mean_value},
                        unengaged: {n, purchase_rate, mean_value}}}."""
    events_by_customer = defaultdict(list)
    for v in value_events:
        events_by_customer[v["customer_id"]].append(v)

    first_send = {}
    ever_engaged = {}
    for e in engagements:
        key = (e["customer_id"], e["program"])
        d = _parse(e["sent_date"])
        if key not in first_send or d < first_send[key]:
            first_send[key] = d
        ever_engaged[key] = ever_engaged.get(key, False) or bool(e.get(engagement_flag))

    by_program = defaultdict(lambda: {"engaged": [], "unengaged": []})
    for (customer_id, program), sent_date in first_send.items():
        window_end = sent_date + timedelta(days=window_days) if window_days else None
        total = 0.0
        for v in events_by_customer.get(customer_id, []):
            vd = _parse(v["event_date"])
            if vd >= sent_date and (window_end is None or vd <= window_end):
                total += v.get("amount") or 0.0
        bucket = "engaged" if ever_engaged[(customer_id, program)] else "unengaged"
        by_program[program][bucket].append(total)

    def summarize(values):
        n = len(values)
        converted = sum(1 for v in values if v > 0)
        return {
            "n": n,
            "purchase_rate": converted / n if n else 0.0,
            "mean_value": sum(values) / n if n else 0.0,
        }

    return {
        program: {"engaged": summarize(g["engaged"]), "unengaged": summarize(g["unengaged"])}
        for program, g in by_program.items()
    }


def divergence(platform, commercial):
    """Ranks programs by open_rate (the platform metric) and by the
    engaged-vs-unengaged mean_value gap (the commercial outcome), and
    reports each program's rank under both -- the literal "platform
    metric vs. commercial outcome" gap named in the JD."""
    programs = list(platform.keys())
    by_open = sorted(programs, key=lambda p: platform[p]["open_rate"], reverse=True)
    by_value_gap = sorted(
        programs,
        key=lambda p: commercial[p]["engaged"]["mean_value"] - commercial[p]["unengaged"]["mean_value"],
        reverse=True,
    )
    open_rank = {p: i for i, p in enumerate(by_open)}
    value_rank = {p: i for i, p in enumerate(by_value_gap)}
    return {
        "by_open_rate": by_open,
        "by_commercial_value_gap": by_value_gap,
        "rank_shifts": {
            p: {
                "open_rank": open_rank[p],
                "value_rank": value_rank[p],
                "shift": open_rank[p] - value_rank[p],
            }
            for p in programs
        },
    }
