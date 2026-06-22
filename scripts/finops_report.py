#!/usr/bin/env python3
"""Generate a last-30-day HYBA FinOps report from AWS Cost Explorer.

Requires AWS credentials in the environment and Cost Explorer permissions.
Outputs JSON to stdout. Exits non-zero when credentials or boto3 are unavailable.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, timedelta
from decimal import Decimal
from typing import Any


def _money(value: str) -> float:
    return float(Decimal(value).quantize(Decimal("0.0001")))


def main() -> int:
    if not os.getenv("AWS_ACCESS_KEY_ID"):
        print("AWS_ACCESS_KEY_ID is required", file=sys.stderr)
        return 2

    try:
        import boto3
    except ImportError:
        print("boto3 is required: pip install boto3", file=sys.stderr)
        return 2

    end = date.today()
    start = end - timedelta(days=30)
    client = boto3.client("ce")

    def query(group_key: dict[str, str]) -> list[dict[str, Any]]:
        response = client.get_cost_and_usage(
            TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[group_key],
        )
        rows = []
        for period in response.get("ResultsByTime", []):
            for group in period.get("Groups", []):
                amount = group["Metrics"]["UnblendedCost"]["Amount"]
                unit = group["Metrics"]["UnblendedCost"]["Unit"]
                rows.append({"key": group.get("Keys", ["unknown"])[0], "amount": _money(amount), "unit": unit})
        return rows

    by_service = query({"Type": "DIMENSION", "Key": "SERVICE"})
    by_customer = query({"Type": "TAG", "Key": "Customer"})
    by_surface = query({"Type": "TAG", "Key": "ApiSurface"})
    total_cost = round(sum(row["amount"] for row in by_service), 4)

    report = {
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "total_unblended_cost_usd": total_cost,
        "cost_by_aws_service": by_service,
        "cost_per_customer": by_customer,
        "cost_per_api_surface": by_surface,
        "gross_margin_estimate": {
            "status": "requires_revenue_input",
            "formula": "(revenue - total_unblended_cost_usd) / revenue",
            "total_unblended_cost_usd": total_cost,
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
