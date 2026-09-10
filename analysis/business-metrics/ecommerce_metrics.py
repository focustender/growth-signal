"""Generic e-commerce unit-economics engine: AOV, conversion rate, total
revenue, and revenue-per-customer by segment. No Fireclay-specific
assumptions -- takes plain customer/order dicts. Built because the
vendored business-metrics-calculator skill's shipped script
(saas_metrics.py) only covers SaaS metrics (MRR, churn, LTV/CAC)
despite its own description mentioning e-commerce; there's no AOV/GMV
path in it to adapt. See README.md."""
from collections import defaultdict


def segment_metrics(customers, orders):
    """customers: iterable of {customer_id, segment}.
    orders: iterable of {customer_id, amount} -- one row per purchase or
    repeat-purchase event; a customer with multiple orders appears once
    per order.

    Returns {segment: {n_customers, n_purchasers, conversion_rate, aov,
    total_revenue, revenue_per_customer}}. Customers with zero orders
    still count toward n_customers and revenue_per_customer -- a
    segment's revenue-per-customer reflects everyone in it, not just
    the people who bought something."""
    segment_of = {c["customer_id"]: c["segment"] for c in customers}
    n_customers = defaultdict(int)
    for c in customers:
        n_customers[c["segment"]] += 1

    revenue = defaultdict(float)
    order_count = defaultdict(int)
    purchasers = defaultdict(set)
    for o in orders:
        segment = segment_of.get(o["customer_id"])
        if segment is None:
            continue
        revenue[segment] += o.get("amount") or 0.0
        order_count[segment] += 1
        purchasers[segment].add(o["customer_id"])

    result = {}
    for segment, n in n_customers.items():
        n_purchasers = len(purchasers[segment])
        n_orders = order_count[segment]
        result[segment] = {
            "n_customers": n,
            "n_purchasers": n_purchasers,
            "conversion_rate": n_purchasers / n if n else 0.0,
            "aov": revenue[segment] / n_orders if n_orders else 0.0,
            "total_revenue": round(revenue[segment], 2),
            "revenue_per_customer": revenue[segment] / n if n else 0.0,
        }
    return result
