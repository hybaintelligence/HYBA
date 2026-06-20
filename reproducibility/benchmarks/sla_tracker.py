#!/usr/bin/env python3
"""Enterprise SLA tracking and service-credit reporting."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List

@dataclass
class SLABreach:
    metric: str
    target: float
    actual: float
    breach_severity: float
    timestamp: str
    service_id: str = "default"

class SLATracker:
    """Enterprise SLA enforcement, breach tracking, and reporting."""
    def __init__(self, targets: Dict[str, float] | None = None):
        self.targets = targets or {"availability":0.9999,"latency_p99":100.0,"latency_p999":500.0,"error_rate":0.0001}
        self.breaches: List[SLABreach] = []
        self.observations: List[Dict[str, Any]] = []
    def _is_breach(self, metric: str, value: float) -> bool:
        target = self.targets[metric]
        return value < target if metric == "availability" else value > target
    def track_metric(self, metric_name: str, value: float, timestamp: str | None = None, service_id: str = "default") -> Dict[str, Any]:
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        obs = {"metric":metric_name,"value":float(value),"timestamp":ts,"service_id":service_id,"breached":False}
        if metric_name in self.targets and self._is_breach(metric_name, float(value)):
            target = self.targets[metric_name]
            severity = ((target - value) / target) if metric_name == "availability" and target else ((value / target) - 1 if target else 0)
            breach = SLABreach(metric_name, target, float(value), float(severity), ts, service_id)
            self.breaches.append(breach); obs["breached"] = True; obs["breach"] = asdict(breach)
        self.observations.append(obs); return obs
    def generate_sla_report(self, revenue_at_risk: float = 0.0) -> Dict[str, Any]:
        service_credits = sum(max(b.breach_severity,0) for b in self.breaches) * revenue_at_risk
        return {"targets":self.targets,"observation_count":len(self.observations),"breach_count":len(self.breaches),"breaches":[asdict(b) for b in self.breaches],"estimated_service_credits":service_credits,"status":"breached" if self.breaches else "within_sla"}
