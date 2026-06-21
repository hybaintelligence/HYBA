#!/usr/bin/env python3
"""Wire live platform telemetry into enterprise operating analytics."""

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

from cohort_analytics import CohortAnalytics
from cost_attribution import CostAttributor
from executive_dashboard import ExecutiveDashboard
from risk_registry import EnterpriseRiskRegistry
from sla_tracker import SLATracker


class EnterpriseTelemetryBridge:
    """Translate HYBA/QaaS telemetry snapshots into board-grade evidence.

    The bridge keeps the Phase 3.5 calculators deterministic while giving them
    a single integration point for live platform evidence: uptime/latency/error
    metrics, usage cost drivers, customer lifecycle cohorts, and operational
    incidents.
    """

    def __init__(
        self,
        sla_tracker: Optional[SLATracker] = None,
        cost_attributor: Optional[CostAttributor] = None,
        risk_registry: Optional[EnterpriseRiskRegistry] = None,
        cohort_analytics: Optional[CohortAnalytics] = None,
        executive_dashboard: Optional[ExecutiveDashboard] = None,
    ):
        self.sla_tracker = sla_tracker or SLATracker()
        self.cost_attributor = cost_attributor or CostAttributor()
        self.risk_registry = risk_registry or EnterpriseRiskRegistry()
        self.cohort_analytics = cohort_analytics or CohortAnalytics()
        self.executive_dashboard = executive_dashboard or ExecutiveDashboard()

    def ingest_snapshot(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest one telemetry snapshot and return executive-ready outputs."""
        timestamp = self._coerce_timestamp(snapshot.get("timestamp"))
        sla_breaches = self._ingest_sla(snapshot.get("sla", {}), timestamp)
        cost_records = self._ingest_costs(snapshot.get("costs", []))
        cohort_updates = self._ingest_cohorts(snapshot.get("cohorts", []))
        risk_updates = self._ingest_incidents(snapshot.get("incidents", []))

        latest_kpis = self._derive_dashboard_kpis(snapshot, cost_records)
        self.executive_dashboard.update_kpis(**latest_kpis)

        period = snapshot.get("period", "current")
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period": period,
            "sla_report": self.sla_tracker.generate_sla_report(),
            "chargeback_report": self.cost_attributor.generate_chargeback_report(period),
            "retention_curve": self.cohort_analytics.generate_retention_curve(),
            "risk_count": len(self.risk_registry.risks),
            "new_sla_breaches": sla_breaches,
            "new_cost_records": cost_records,
            "new_cohort_updates": cohort_updates,
            "new_risk_updates": risk_updates,
            "weekly_ops_review": self.executive_dashboard.generate_weekly_ops_review(),
            "quarterly_deck": self.executive_dashboard.generate_quarterly_deck(),
        }

    def _ingest_sla(self, metrics: Dict[str, float], timestamp: datetime) -> list:
        breaches = []
        for metric_name, value in metrics.items():
            breach = self.sla_tracker.track_metric(metric_name, value, timestamp)
            if breach:
                breaches.append(breach)
        return breaches

    def _ingest_costs(self, services: Iterable[Dict[str, Any]]) -> list:
        records = []
        for service in services:
            service_id = service.get("service_id")
            if not service_id:
                raise ValueError("Cost telemetry requires service_id")
            metrics = {k: v for k, v in service.items() if k != "service_id"}
            records.append(self.cost_attributor.calculate_service_cost(service_id, metrics))
        return records

    def _ingest_cohorts(self, cohorts: Iterable[Dict[str, Any]]) -> list:
        updates = []
        for cohort in cohorts:
            cohort_id = cohort["cohort_id"]
            if cohort_id not in self.cohort_analytics.cohorts:
                self.cohort_analytics.create_cohort(
                    cohort_id,
                    cohort.get("start_date"),
                    cohort.get("initial_size", cohort.get("retained_customers", 0)),
                    cohort.get("attributes", {}),
                )
            updates.append(
                self.cohort_analytics.track_cohort_metrics(
                    cohort_id, cohort.get("month", 0), cohort.get("metrics", cohort)
                )
            )
        return updates

    def _ingest_incidents(self, incidents: Iterable[Dict[str, Any]]) -> list:
        risks = []
        for incident in incidents:
            severity = incident.get("severity", "medium")
            probability = {"low": 0.1, "medium": 0.25, "high": 0.5, "critical": 0.8}.get(
                severity, 0.25
            )
            impact = incident.get(
                "impact",
                {"low": 0.2, "medium": 0.4, "high": 0.7, "critical": 1.0}.get(
                    severity, 0.4
                ),
            )
            risks.append(
                self.risk_registry.register_risk(
                    incident.get("category", "operational"),
                    incident.get("description", "Telemetry incident"),
                    probability,
                    impact,
                    incident.get("owner", "Platform"),
                )
            )
        return risks

    def _derive_dashboard_kpis(
        self, snapshot: Dict[str, Any], cost_records: list
    ) -> Dict[str, float]:
        sla = snapshot.get("sla", {})
        customers = snapshot.get("customers", {})
        total_support_cost = sum(r["direct_costs"].get("support", 0.0) for r in cost_records)
        customer_count = customers.get("customer_count", 0)
        derived = {
            "sla_availability": sla.get(
                "availability", self.executive_dashboard.kpis["sla_availability"]
            ),
            "sla_latency_p99": sla.get(
                "latency_p99", self.executive_dashboard.kpis["sla_latency_p99"]
            ),
            "customer_count": customer_count,
            "churn_rate": customers.get("churn_rate", self.executive_dashboard.kpis["churn_rate"]),
            "net_revenue_retention": customers.get(
                "net_revenue_retention", self.executive_dashboard.kpis["net_revenue_retention"]
            ),
            "support_cost_per_customer": (
                total_support_cost / customer_count if customer_count else 0
            ),
        }
        derived.update(snapshot.get("kpis", {}))
        return derived

    @staticmethod
    def _coerce_timestamp(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return datetime.now(timezone.utc)
