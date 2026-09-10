"""Runs ecommerce_metrics.py's generic engine against real customer and
funnel-event data: AOV, conversion rate, and revenue per customer by
segment. Writes output/metrics_report.json for the findings write-up
to cite exact numbers from."""
import json
import sqlite3
from pathlib import Path

import ecommerce_metrics as em

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "data" / "trade_signal.db"


def run() -> dict:
    conn = sqlite3.connect(DB_PATH)
    customers = [
        {"customer_id": r[0], "segment": r[1]}
        for r in conn.execute("SELECT customer_id, segment FROM customers")
    ]
    orders = [
        {"customer_id": r[0], "amount": r[1]}
        for r in conn.execute(
            "SELECT customer_id, amount FROM funnel_events "
            "WHERE event_type IN ('purchase','repeat_purchase')"
        )
    ]
    conn.close()
    return em.segment_metrics(customers, orders)


if __name__ == "__main__":
    result = run()
    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "metrics_report.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))
    print(f"\nWrote {out_path}")
