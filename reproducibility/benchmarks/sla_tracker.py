#!/usr/bin/env python3
"""Enterprise SLA tracking and financial impact reporting."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class SLATracker:
    """Enterprise SLA enforcement and reporting."""

    def __init__(self, revenue_per_downtime_second: float = 0.0):
        self.targets = {
            "availability": 0.9999,
            "latency_p99": 100.0,
            "latency_p999": 500.0,
            "error_rate": 0.0001,
        }
        self.revenue_per_downtime_second = revenue_per_downtime_second
        self.measurements: List[Dict[str, Any]] = []
        self.breaches: List[Dict[str, Any]] = []

    def track_metric(
        self, metric_name: str, value: float, timestamp: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """Track a metric against the configured SLA target."""
        timestamp = timestamp or datetime.now(timezone.utc)
        measurement = {"metric": metric_name, "value": value, "timestamp": timestamp}
        self.measurements.append(measurement)
        if metric_name not in self.targets:
            return None
        target = self.targets[metric_name]
        breached = value < target if metric_name == "availability" else value > target
        if not breached:
            return None
        severity = (
            ((target - value) / target) if metric_name == "availability" else ((value / target) - 1)
        )
        breach = {
            "metric": metric_name,
            "target": target,
            "actual": value,
            "breach_severity": severity,
            "timestamp": timestamp,
        }
        self.breaches.append(breach)
        return breach

    def generate_sla_report(self) -> Dict[str, Any]:
        """Generate an executive SLA report with breach and financial impact summaries."""
        downtime_seconds = 0.0
        for breach in self.breaches:
            if breach["metric"] == "availability":
                downtime_seconds += max(
                    0.0, (breach["target"] - breach["actual"]) * 30 * 24 * 60 * 60
                )
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "targets": self.targets,
            "measurement_count": len(self.measurements),
            "breach_count": len(self.breaches),
            "breaches": self.breaches,
            "estimated_downtime_seconds": downtime_seconds,
            "estimated_revenue_impact": downtime_seconds * self.revenue_per_downtime_second,
        }
