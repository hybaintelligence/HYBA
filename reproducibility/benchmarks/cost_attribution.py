#!/usr/bin/env python3
"""Per-service cost attribution and chargeback reporting."""

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List


class CostAttributor:
    """Per-service cost tracking and attribution."""

    def __init__(self, overhead_rate: float = 0.15):
        self.cost_drivers = {
            "compute": 0.50,
            "memory": 0.08,
            "storage": 0.023,
            "network": 0.12,
            "support": 0.15,
        }
        self.overhead_rate = overhead_rate
        self.service_costs: List[Dict[str, Any]] = []

    def calculate_service_cost(
        self, service_id: str, metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate full-cost allocation including overhead."""
        direct = {
            "compute": metrics.get("vcpu_hours", 0) * self.cost_drivers["compute"],
            "memory": metrics.get("gb_hours", 0) * self.cost_drivers["memory"],
            "storage": metrics.get("gb_months", 0) * self.cost_drivers["storage"],
            "network": metrics.get("gb_transferred", 0) * self.cost_drivers["network"],
            "support": metrics.get("support_units", 1) * self.cost_drivers["support"],
        }
        subtotal = sum(direct.values())
        record = {
            "service_id": service_id,
            "department": metrics.get("department", "unallocated"),
            "period": metrics.get("period", "current"),
            "direct_costs": direct,
            "overhead": subtotal * self.overhead_rate,
            "total_cost": subtotal * (1 + self.overhead_rate),
            "calculated_at": datetime.now(timezone.utc),
        }
        self.service_costs.append(record)
        return record

    def generate_chargeback_report(self, period: str) -> Dict[str, Any]:
        """Generate department-level cost allocation."""
        departments: Dict[str, float] = defaultdict(float)
        services = [r for r in self.service_costs if r["period"] == period]
        for record in services:
            departments[record["department"]] += record["total_cost"]
        total = sum(departments.values())
        return {
            "period": period,
            "total_cost": total,
            "departments": dict(departments),
            "services": services,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
