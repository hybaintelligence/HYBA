#!/usr/bin/env python3
"""Smoke tests for McKinsey-grade benchmark additions."""

from datetime import datetime, timezone

from change_management import ChangeImpactAssessor
from cohort_analytics import CohortAnalytics
from compliance_validator import ComplianceValidator
from cost_attribution import CostAttributor
from customer_effort import CustomerEffortAnalyzer
from executive_dashboard import ExecutiveDashboard
from financial_health import FinancialHealthAnalyzer
from financial_model import FinancialModelBuilder
from nps_program import NPSProgram
from okr_framework import OKRFramework
from organizational_design import RACAMatrix
from peer_benchmarking import PeerBenchmarking
from risk_registry import EnterpriseRiskRegistry
from sla_tracker import SLATracker
from unit_economics import UnitEconomicsCalculator
from win_loss_analysis import WinLossAnalyzer


def test_operational_and_governance_additions_smoke():
    sla = SLATracker(revenue_per_downtime_second=10)
    breach = sla.track_metric("latency_p99", 150, datetime.now(timezone.utc))
    assert breach and sla.generate_sla_report()["breach_count"] == 1

    cost = CostAttributor().calculate_service_cost(
        "api", {"vcpu_hours": 10, "gb_hours": 20, "department": "platform"}
    )
    assert cost["total_cost"] > 0

    risk = EnterpriseRiskRegistry()
    registered = risk.register_risk("operational", "Latency regression", 0.2, 0.5, "SRE")
    assert registered["risk_score"] == 0.1

    compliance = ComplianceValidator().validate_framework(
        "SOC2", ["availability", "security", "confidentiality", "integrity"]
    )
    assert compliance["status"] == "compliant"


def test_strategy_finance_customer_additions_smoke():
    cohorts = CohortAnalytics()
    cohorts.create_cohort("2026-06", "2026-06-01", 100, {"segment": "enterprise"})
    assert (
        cohorts.track_cohort_metrics("2026-06", 1, {"retained_customers": 90})["retention_rate"]
        == 0.9
    )

    unit = UnitEconomicsCalculator()
    assert unit.calculate_magic_number(120, 100, 20) == 1
    assert len(unit.forecast_arr(100, 1, 3)) == 3

    raci = RACAMatrix()
    raci.define_ownership("incident", "SRE", "CTO", ["Security"], ["CEO"])
    assert raci.audit_decision_authority()["domain_count"] == 1

    finance = FinancialModelBuilder()
    finance.build_scenario(
        "base", {"starting_revenue": 1000, "monthly_growth": 0.1, "monthly_opex": 500}
    )
    assert finance.calculate_valuation_multiples()["base"]["arr"] > 0

    health = FinancialHealthAnalyzer()
    assert health.calculate_payback_period([-10, -1, 1]) == 2

    nps = NPSProgram()
    nps.record_nps("c1", 10, "great", "enterprise")
    assert nps.analyze_by_segment()["enterprise"]["nps"] == 100

    ces = CustomerEffortAnalyzer()
    assert ces.measure_effort("i1", 5, 20)["churn_risk"] == "high"

    win_loss = WinLossAnalyzer()
    win_loss.record_opportunity("o1", "Acme", "lost", 100, "Competitor", "price", None)
    assert win_loss.analyze_loss_patterns()["loss_count"] == 1

    dashboard = ExecutiveDashboard()
    assert dashboard.generate_weekly_ops_review()["title"] == "Weekly Operations Review"

    peers = PeerBenchmarking()
    assert peers.compare_to_peers({"nps_median": 75})["nps_median"]["position"] == "Top Quartile"

    okrs = OKRFramework(2026)
    okr = okrs.set_company_okr("Scale", [{"name": "ARR", "progress": 0.5}], "CEO")
    okrs.cascade_to_teams(okr, "growth")
    assert okrs.generate_okr_report()["average_company_progress"] == 0.5

    change = ChangeImpactAssessor()
    assert "technical" in change.assess_change_impact("API migration", ["customer_api"])


def test_enterprise_telemetry_bridge_wires_live_evidence_to_dashboard():
    from telemetry_bridge import EnterpriseTelemetryBridge

    bridge = EnterpriseTelemetryBridge()
    output = bridge.ingest_snapshot(
        {
            "timestamp": "2026-06-20T00:00:00Z",
            "period": "2026-06",
            "sla": {"availability": 0.999, "latency_p99": 125, "error_rate": 0.00005},
            "costs": [
                {
                    "service_id": "qaas-api",
                    "department": "platform",
                    "period": "2026-06",
                    "vcpu_hours": 20,
                    "gb_hours": 50,
                    "support_units": 4,
                }
            ],
            "cohorts": [
                {
                    "cohort_id": "enterprise-2026-06",
                    "start_date": "2026-06-01",
                    "initial_size": 10,
                    "month": 1,
                    "metrics": {"retained_customers": 9, "revenue": 12000, "cac": 5000},
                    "attributes": {"segment": "enterprise"},
                }
            ],
            "incidents": [
                {
                    "category": "operational",
                    "severity": "high",
                    "description": "p99 latency exceeded target",
                    "owner": "SRE",
                }
            ],
            "customers": {"customer_count": 10, "churn_rate": 0.1, "net_revenue_retention": 1.15},
            "kpis": {"arr": 144000, "gross_margin": 0.72},
        }
    )

    assert output["sla_report"]["breach_count"] == 2
    assert output["chargeback_report"]["departments"]["platform"] > 0
    assert output["retention_curve"]["enterprise-2026-06"][0]["retention_rate"] == 0.9
    assert output["risk_count"] == 1
    assert output["weekly_ops_review"]["metrics"]["sla_latency_p99"] == 125
    assert output["quarterly_deck"]["slides"][0]["metrics"]["arr"] == 144000
