#!/usr/bin/env python3
"""Per-service cost attribution and chargeback reporting."""
from __future__ import annotations
from typing import Any, Dict

class CostAttributor:
    """Allocate infrastructure costs to services using deterministic cost drivers."""
    def __init__(self, cost_drivers: Dict[str, float] | None = None):
        self.cost_drivers = cost_drivers or {"compute":0.50,"memory":0.08,"storage":0.023,"network":0.12,"support":0.15}
        self.service_costs: Dict[str, Dict[str, Any]] = {}
    def calculate_service_cost(self, service_id: str, metrics: Dict[str, float]) -> Dict[str, Any]:
        line_items = {k: float(metrics.get(k,0))*rate for k, rate in self.cost_drivers.items()}
        overhead = float(metrics.get("overhead_pct",0.0)) * sum(line_items.values())
        result = {"service_id":service_id,"line_items":line_items,"overhead":overhead,"total_cost":sum(line_items.values())+overhead}
        self.service_costs[service_id] = result; return result
    def generate_chargeback_report(self, period: str) -> Dict[str, Any]:
        total = sum(v["total_cost"] for v in self.service_costs.values())
        return {"period":period,"total_cost":total,"services":self.service_costs,"allocation_pct":{sid:(v["total_cost"]/total if total else 0) for sid,v in self.service_costs.items()}}
