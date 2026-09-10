import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import attribution as attr

WELCOME_ENGAGEMENTS = [
    {"customer_id": "c1", "program": "welcome", "sent_date": "2026-01-01", "opened": 1, "clicked": 0},
    {"customer_id": "c2", "program": "welcome", "sent_date": "2026-01-01", "opened": 0, "clicked": 0},
    {"customer_id": "c3", "program": "welcome", "sent_date": "2026-01-01", "opened": 0, "clicked": 0},
    {"customer_id": "c4", "program": "welcome", "sent_date": "2026-01-01", "opened": 0, "clicked": 0},
]
REACTIVATION_ENGAGEMENTS = [
    {"customer_id": "c5", "program": "reactivation", "sent_date": "2026-01-01", "opened": 1, "clicked": 0},
    {"customer_id": "c6", "program": "reactivation", "sent_date": "2026-01-01", "opened": 1, "clicked": 0},
    {"customer_id": "c7", "program": "reactivation", "sent_date": "2026-01-01", "opened": 1, "clicked": 0},
    {"customer_id": "c8", "program": "reactivation", "sent_date": "2026-01-01", "opened": 0, "clicked": 0},
]
ALL_ENGAGEMENTS = WELCOME_ENGAGEMENTS + REACTIVATION_ENGAGEMENTS

# c1 (welcome, engaged) buys $500 after the send. c8 (reactivation,
# unengaged) buys $300 after the send. Nobody else buys anything --
# deliberately: reactivation's opened recipients (c5,c6,c7) convert at
# zero, while its one non-opener still buys, so reactivation's real
# commercial value comes from people the platform metric marks as
# "unreached." Welcome is the opposite: its only buyer is its only
# opener.
VALUE_EVENTS = [
    {"customer_id": "c1", "event_date": "2026-01-05", "amount": 500},
    {"customer_id": "c8", "event_date": "2026-01-10", "amount": 300},
]


def test_platform_metrics_open_and_click_rate():
    m = attr.platform_metrics(ALL_ENGAGEMENTS)
    assert m["welcome"] == {"sent": 4, "opened": 1, "clicked": 0, "open_rate": 0.25, "click_rate": 0.0}
    assert m["reactivation"]["open_rate"] == 0.75


def test_commercial_outcomes_splits_engaged_vs_unengaged():
    c = attr.commercial_outcomes(ALL_ENGAGEMENTS, VALUE_EVENTS)
    assert c["welcome"]["engaged"] == {"n": 1, "purchase_rate": 1.0, "mean_value": 500.0}
    assert c["welcome"]["unengaged"] == {"n": 3, "purchase_rate": 0.0, "mean_value": 0.0}
    assert c["reactivation"]["engaged"] == {"n": 3, "purchase_rate": 0.0, "mean_value": 0.0}
    assert c["reactivation"]["unengaged"] == {"n": 1, "purchase_rate": 1.0, "mean_value": 300.0}


def test_customers_with_no_value_event_count_as_zero_not_excluded():
    c = attr.commercial_outcomes(ALL_ENGAGEMENTS, VALUE_EVENTS)
    # c2, c3, c4 never bought anything -- must still appear in the group
    assert c["welcome"]["unengaged"]["n"] == 3


def test_window_days_excludes_events_after_the_window():
    events_with_late_purchase = VALUE_EVENTS + [
        {"customer_id": "c1", "event_date": "2026-02-15", "amount": 9999},
    ]
    unwindowed = attr.commercial_outcomes(WELCOME_ENGAGEMENTS, events_with_late_purchase)
    windowed = attr.commercial_outcomes(WELCOME_ENGAGEMENTS, events_with_late_purchase, window_days=7)
    assert unwindowed["welcome"]["engaged"]["mean_value"] == 500.0 + 9999.0
    assert windowed["welcome"]["engaged"]["mean_value"] == 500.0


def test_value_event_before_send_date_is_not_credited():
    events_before_send = [{"customer_id": "c2", "event_date": "2025-12-01", "amount": 1000}]
    c = attr.commercial_outcomes(WELCOME_ENGAGEMENTS, events_before_send)
    # c2 is unengaged; its only "purchase" predates the send, so it
    # must not count -- otherwise the metric would credit programs for
    # revenue they couldn't possibly have influenced.
    assert c["welcome"]["unengaged"]["mean_value"] == 0.0


def test_divergence_flags_a_program_where_engagement_and_value_disagree():
    platform = attr.platform_metrics(ALL_ENGAGEMENTS)
    commercial = attr.commercial_outcomes(ALL_ENGAGEMENTS, VALUE_EVENTS)
    d = attr.divergence(platform, commercial)
    # reactivation has the higher open rate (platform metric)...
    assert d["by_open_rate"][0] == "reactivation"
    # ...but welcome has the larger engaged-vs-unengaged value gap
    # (commercial outcome) -- the exact divergence this tool exists to catch.
    assert d["by_commercial_value_gap"][0] == "welcome"
    assert d["rank_shifts"]["reactivation"]["shift"] != 0
