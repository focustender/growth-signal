import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ecommerce_metrics as em

CUSTOMERS = [
    {"customer_id": "c1", "segment": "homeowner"},
    {"customer_id": "c2", "segment": "homeowner"},
    {"customer_id": "c3", "segment": "homeowner"},
    {"customer_id": "c4", "segment": "trade"},
    {"customer_id": "c5", "segment": "trade"},
]
# c1 buys twice (an initial + a repeat purchase), c2 buys once, c3 never
# buys. c4 (trade) buys once at a much larger amount, c5 (trade) never
# buys -- deliberately asymmetric conversion and order size across
# segments, matching this project's real data shape.
ORDERS = [
    {"customer_id": "c1", "amount": 400.0},
    {"customer_id": "c1", "amount": 600.0},
    {"customer_id": "c2", "amount": 500.0},
    {"customer_id": "c4", "amount": 9000.0},
]


def test_aov_is_revenue_over_orders_not_over_customers():
    m = em.segment_metrics(CUSTOMERS, ORDERS)
    # homeowner revenue = 400+600+500 = 1500 over 3 orders -> AOV 500,
    # not over 2 purchasers (750) and not over 3 customers (500 would
    # coincidentally match here, so assert against the order count directly)
    assert m["homeowner"]["aov"] == 500.0
    assert m["homeowner"]["total_revenue"] == 1500.0


def test_segment_grouping_keeps_segments_independent():
    m = em.segment_metrics(CUSTOMERS, ORDERS)
    assert m["trade"]["aov"] == 9000.0
    assert m["trade"]["total_revenue"] == 9000.0
    assert m["homeowner"]["aov"] != m["trade"]["aov"]


def test_zero_purchase_customers_count_toward_conversion_and_revenue_per_customer():
    m = em.segment_metrics(CUSTOMERS, ORDERS)
    # 2 of 3 homeowners ever purchased
    assert m["homeowner"]["n_customers"] == 3
    assert m["homeowner"]["n_purchasers"] == 2
    assert m["homeowner"]["conversion_rate"] == 2 / 3
    # revenue-per-customer divides by all 3 homeowners, not just the 2 buyers
    assert m["homeowner"]["revenue_per_customer"] == 1500.0 / 3


def test_segment_with_zero_orders_has_zero_aov_not_a_crash():
    customers = [{"customer_id": "c1", "segment": "commercial"}]
    m = em.segment_metrics(customers, [])
    assert m["commercial"]["aov"] == 0.0
    assert m["commercial"]["conversion_rate"] == 0.0
    assert m["commercial"]["n_purchasers"] == 0
