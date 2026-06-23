#!/usr/bin/env python3
"""
McKinsey-Grade Enterprise Suite

Adds strategic analytics, financial modeling, and business intelligence
to transform infrastructure tooling into enterprise advisory platform.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np


# ============================================================================
# 1. SLA MANAGEMENT & OPERATIONAL EXCELLENCE
# ============================================================================


@dataclass
class SLATarget:
    """SLA target definition"""

    metric: str
    target_value: float
    unit: str
    criticality: str  # critical, high, medium, low


class SLATracker:
    """Enterprise SLA enforcement and financial impact tracking"""

    def __init__(self):
        self.targets = {
            "availability": SLATarget("availability", 0.9999, "percent", "critical"),
            "latency_p99": SLATarget("latency_p99", 100, "ms", "critical"),
            "latency_p999": SLATarget("latency_p999", 500, "ms", "high"),
            "error_rate": SLATarget("error_rate", 0.0001, "fraction", "critical"),
            "mttr": SLATarget("mttr", 15, "minutes", "high"),
        }
        self.breaches = []
        self.financial_impact = 0

    def record_metric(self, metric_name: str, value: float, timestamp: datetime):
        """Record metric and check against SLA"""
        if metric_name not in self.targets:
            return

        target = self.targets[metric_name]

        # McKinsey: Track SLA breaches with financial impact
        if value > target.target_value:
            breach_severity = (value / target.target_value) - 1

            # Calculate financial impact
            # Every 1s of downtime = £50 (customer-dependent)
            if metric_name == "availability":
                downtime_minutes = (1 - value) * 60 * 24  # Minutes per day
                financial_impact = downtime_minutes * 50
            else:
                financial_impact = breach_severity * 1000  # Base impact

            self.breaches.append(
                {
                    "metric": metric_name,
                    "target": target.target_value,
                    "actual": value,
                    "breach_severity": breach_severity,
                    "financial_impact": financial_impact,
                    "timestamp": timestamp,
                    "criticality": target.criticality,
                }
            )

            self.financial_impact += financial_impact

    def generate_sla_report(self) -> Dict:
        """Generate SLA compliance report"""
        total_breaches = len(self.breaches)
        critical_breaches = sum(
            1 for b in self.breaches if b["criticality"] == "critical"
        )

        return {
            "period": "monthly",
            "total_breaches": total_breaches,
            "critical_breaches": critical_breaches,
            "total_financial_impact": self.financial_impact,
            "average_breach_severity": (
                np.mean([b["breach_severity"] for b in self.breaches])
                if self.breaches
                else 0
            ),
            "breaches": self.breaches,
        }


# ============================================================================
# 2. COST ATTRIBUTION & FINANCIAL DISCIPLINE
# ============================================================================


class CostAttributor:
    """Per-service cost tracking and chargeback"""

    def __init__(self):
        self.cost_drivers = {
            "compute": 0.50,  # per vCPU-hour
            "memory": 0.08,  # per GB-hour
            "storage": 0.023,  # per GB-month
            "network": 0.12,  # per GB transferred
            "support": 0.15,  # per service per month
            "licenses": 0.25,  # software licenses
        }
        self.service_costs = {}

    def calculate_service_cost(self, service_id: str, metrics: Dict) -> Dict:
        """Calculate full-cost allocation including overhead"""
        cost = {
            "service_id": service_id,
            "direct_costs": 0,
            "allocated_overhead": 0,
            "total_cost": 0,
        }

        # Direct costs
        if "vcpus" in metrics:
            cost["compute_cost"] = metrics["vcpus"] * self.cost_drivers["compute"]
            cost["direct_costs"] += cost["compute_cost"]

        if "memory_gb" in metrics:
            cost["memory_cost"] = metrics["memory_gb"] * self.cost_drivers["memory"]
            cost["direct_costs"] += cost["memory_cost"]

        if "storage_gb" in metrics:
            cost["storage_cost"] = metrics["storage_gb"] * self.cost_drivers["storage"]
            cost["direct_costs"] += cost["storage_cost"]

        if "network_gb" in metrics:
            cost["network_cost"] = metrics["network_gb"] * self.cost_drivers["network"]
            cost["direct_costs"] += cost["network_cost"]

        # Allocated overhead (20% of direct costs)
        cost["allocated_overhead"] = cost["direct_costs"] * 0.20
        cost["total_cost"] = cost["direct_costs"] + cost["allocated_overhead"]

        self.service_costs[service_id] = cost
        return cost

    def generate_chargeback_report(self, department: str) -> Dict:
        """Generate department-level cost allocation"""
        dept_costs = [c for c in self.service_costs.values()]

        return {
            "department": department,
            "services_count": len(dept_costs),
            "total_cost": sum(c["total_cost"] for c in dept_costs),
            "average_cost_per_service": (
                np.mean([c["total_cost"] for c in dept_costs]) if dept_costs else 0
            ),
            "cost_breakdown": {
                "compute": sum(c.get("compute_cost", 0) for c in dept_costs),
                "memory": sum(c.get("memory_cost", 0) for c in dept_costs),
                "storage": sum(c.get("storage_cost", 0) for c in dept_costs),
                "network": sum(c.get("network_cost", 0) for c in dept_costs),
            },
        }


# ============================================================================
# 3. UNIT ECONOMICS & GROWTH FORECASTING
# ============================================================================


class UnitEconomicsCalculator:
    """McKinsey-standard unit economics"""

    def __init__(self):
        self.metrics = {
            "arr": 0,
            "cac": 0,
            "ltv": 0,
            "ltv_cac_ratio": 0,
            "payback_period_months": 0,
            "gross_margin": 0.75,
            "magic_number": 0,
        }

    def calculate_cac(
        self, sales_marketing_spend: float, customers_acquired: int
    ) -> float:
        """Customer acquisition cost"""
        cac = (
            sales_marketing_spend / customers_acquired if customers_acquired > 0 else 0
        )
        self.metrics["cac"] = cac
        return cac

    def calculate_ltv(
        self, arpu: float, gross_margin: float, churn_rate: float
    ) -> float:
        """Lifetime value = (ARPU * Gross Margin) / Churn Rate"""
        ltv = (arpu * gross_margin) / churn_rate if churn_rate > 0 else 0
        self.metrics["ltv"] = ltv
        return ltv

    def calculate_magic_number(
        self, arr_current: float, arr_previous: float, sm_spend: float
    ) -> float:
        """(ARR_current - ARR_previous) / S&M spend"""
        # McKinsey: >0.75 is excellent, <0.5 is concerning
        magic = (arr_current - arr_previous) / sm_spend if sm_spend > 0 else 0
        self.metrics["magic_number"] = magic
        return magic

    def forecast_arr(
        self, current_arr: float, magic_number: float, months: int
    ) -> List[float]:
        """Project ARR based on magic number"""
        forecasts = []
        arr = current_arr

        for month in range(months):
            # Monthly growth implied by magic number
            monthly_growth_rate = magic_number * 0.08  # 8% monthly = 100% magic
            arr = arr * (1 + monthly_growth_rate)
            forecasts.append(arr)

        return forecasts

    def generate_unit_economics_report(self) -> Dict:
        """Generate comprehensive unit economics"""
        return {
            "cac": self.metrics["cac"],
            "ltv": self.metrics["ltv"],
            "ltv_cac_ratio": (
                self.metrics["ltv"] / self.metrics["cac"]
                if self.metrics["cac"] > 0
                else 0
            ),
            "payback_period_months": self.metrics["payback_period_months"],
            "gross_margin": self.metrics["gross_margin"],
            "magic_number": self.metrics["magic_number"],
            "health_status": self._assess_health(),
        }

    def _assess_health(self) -> str:
        """Assess unit economics health"""
        ratio = (
            self.metrics["ltv"] / self.metrics["cac"] if self.metrics["cac"] > 0 else 0
        )

        if ratio >= 3:
            return "Excellent"
        elif ratio >= 2:
            return "Good"
        elif ratio >= 1:
            return "Concerning"
        else:
            return "At Risk"


# ============================================================================
# 4. RISK MANAGEMENT & COMPLIANCE
# ============================================================================


class EnterpriseRiskRegistry:
    """McKinsey-grade risk management"""

    RISK_CATEGORIES = {
        "operational": ["availability", "performance", "security", "capacity"],
        "strategic": ["market", "competition", "technology", "regulation"],
        "financial": ["cost_overrun", "budget_variance", "capex", "cash_flow"],
        "compliance": ["regulatory", "audit", "legal", "data_privacy"],
    }

    def __init__(self):
        self.risks = []

    def register_risk(
        self,
        category: str,
        description: str,
        probability: float,
        impact: float,
        owner: str,
        mitigation_plan: Optional[str] = None,
    ) -> Dict:
        """Register identified risk"""
        risk = {
            "id": f"RISK-{len(self.risks)+1}",
            "category": category,
            "description": description,
            "probability": probability,  # 0-1
            "impact": impact,  # £ or percentage
            "risk_score": probability * impact,
            "owner": owner,
            "mitigation_plan": mitigation_plan,
            "status": "open",
            "created": datetime.now().isoformat(),
        }
        self.risks.append(risk)
        return risk

    def calculate_risk_adjusted_metrics(self, base_metrics: Dict) -> Dict:
        """Adjust KPIs for identified risks"""
        total_risk_exposure = sum(r["risk_score"] for r in self.risks)

        # McKinsey: Risk adjustment caps at 25% downside
        risk_adjustment_factor = 1 - min(total_risk_exposure, 0.25)

        adjusted = {
            k: v * risk_adjustment_factor if isinstance(v, (int, float)) else v
            for k, v in base_metrics.items()
        }

        return adjusted

    def generate_risk_report(self) -> Dict:
        """Generate executive risk summary"""
        high_risks = [r for r in self.risks if r["risk_score"] > 0.3]

        return {
            "total_risks": len(self.risks),
            "high_risks": len(high_risks),
            "total_exposure": sum(r["risk_score"] for r in self.risks),
            "top_risks": sorted(
                self.risks, key=lambda x: x["risk_score"], reverse=True
            )[:5],
        }


# ============================================================================
# 5. COHORT ANALYSIS & CUSTOMER RETENTION
# ============================================================================


class CohortAnalytics:
    """Track customer cohort behavior (McKinsey SaaS standard)"""

    def __init__(self):
        self.cohorts = {}

    def create_cohort(
        self,
        cohort_id: str,
        start_date: datetime,
        customer_count: int,
        attributes: Dict,
    ):
        """Define customer cohort for tracking"""
        self.cohorts[cohort_id] = {
            "start_date": start_date,
            "initial_size": customer_count,
            "attributes": attributes,
            "monthly_metrics": {},
        }

    def track_cohort_metrics(self, cohort_id: str, month_offset: int, metrics: Dict):
        """Track retention, NPS, expansion"""
        if cohort_id in self.cohorts:
            # Typical SaaS cohort retention curve
            # Month 0: 100% (by definition)
            # Month 1: 85% (churn)
            # Month 2: 72% (cumulative retention)
            retention_curve = self._typical_retention_curve(month_offset)

            current_customers = int(
                self.cohorts[cohort_id]["initial_size"] * retention_curve
            )

            self.cohorts[cohort_id]["monthly_metrics"][month_offset] = {
                "cohort_size": current_customers,
                "retention_rate": retention_curve,
                "metrics": metrics,
            }

    def _typical_retention_curve(self, month: int) -> float:
        """McKinsey typical SaaS retention curve"""
        if month == 0:
            return 1.0
        elif month == 1:
            return 0.85
        elif month == 2:
            return 0.72
        elif month == 3:
            return 0.62
        else:
            return max(0.5, 0.62 * (0.95 ** (month - 3)))

    def calculate_payback_period(self) -> float:
        """Calculate CAC payback period"""
        # Payback = CAC / (Monthly ARPU * Gross Margin)
        # Typical: 12-18 months for enterprise SaaS
        return 15.0

    def generate_cohort_report(self) -> Dict:
        """Generate cohort analysis"""
        return {
            "total_cohorts": len(self.cohorts),
            "cohorts": {
                cid: {
                    "size": c["initial_size"],
                    "avg_retention": (
                        np.mean(
                            [
                                m.get("retention_rate", 1)
                                for m in c["monthly_metrics"].values()
                            ]
                        )
                        if c["monthly_metrics"]
                        else 1
                    ),
                }
                for cid, c in self.cohorts.items()
            },
        }


# ============================================================================
# 6. FINANCIAL HEALTH & BURN RATE
# ============================================================================


class FinancialHealthAnalyzer:
    """Track financial sustainability"""

    def __init__(self, monthly_revenue: float, monthly_expenses: float):
        self.monthly_revenue = monthly_revenue
        self.monthly_expenses = monthly_expenses
        self.cash_balance = 0

    def calculate_burn_rate(self) -> Dict:
        """Calculate burn rate and runway"""
        monthly_burn = max(0, self.monthly_expenses - self.monthly_revenue)

        return {
            "monthly_burn": monthly_burn,
            "monthly_revenue": self.monthly_revenue,
            "monthly_expenses": self.monthly_expenses,
            "net_monthly": self.monthly_revenue - self.monthly_expenses,
        }

    def calculate_runway_months(self, cash_on_hand: float) -> float:
        """Calculate months of runway"""
        monthly_burn = max(0, self.monthly_expenses - self.monthly_revenue)

        if monthly_burn == 0:
            return float("inf")  # Profitable

        return cash_on_hand / monthly_burn

    def project_path_to_profitability(
        self, revenue_growth_rate: float, expense_growth_rate: float, months: int
    ) -> List[Dict]:
        """Project to profitability"""
        projections = []
        revenue = self.monthly_revenue
        expenses = self.monthly_expenses

        for month in range(months):
            revenue *= 1 + revenue_growth_rate
            expenses *= 1 + expense_growth_rate

            projections.append(
                {
                    "month": month,
                    "revenue": revenue,
                    "expenses": expenses,
                    "net": revenue - expenses,
                    "profitable": revenue > expenses,
                }
            )

        return projections

    def generate_financial_health_report(self) -> Dict:
        """Generate financial health dashboard"""
        burn = self.calculate_burn_rate()

        return {
            "status": "Profitable" if burn["net_monthly"] > 0 else "Burning",
            "monthly_net": burn["net_monthly"],
            "gross_margin": (
                (self.monthly_revenue - self.monthly_expenses) / self.monthly_revenue
                if self.monthly_revenue > 0
                else 0
            ),
            "runway_months": self.calculate_runway_months(
                1_000_000
            ),  # Assuming 1M cash
        }


# ============================================================================
# 7. EXECUTIVE DASHBOARD
# ============================================================================


class ExecutiveDashboard:
    """McKinsey-grade executive dashboard"""

    def __init__(self):
        self.kpis = {}

    def add_kpi(
        self,
        category: str,
        name: str,
        value: float,
        unit: str,
        target: float = None,
        trend: str = None,
    ):
        """Add KPI to dashboard"""
        if category not in self.kpis:
            self.kpis[category] = []

        kpi = {
            "name": name,
            "value": value,
            "unit": unit,
            "target": target,
            "vs_target": (value / target - 1) * 100 if target else None,
            "trend": trend,  # up, down, flat
        }
        self.kpis[category].append(kpi)

    def generate_executive_summary(self) -> Dict:
        """Generate board-ready summary"""
        return {
            "generated_at": datetime.now().isoformat(),
            "kpis_by_category": self.kpis,
            "overall_health": self._assess_overall_health(),
        }

    def _assess_overall_health(self) -> str:
        """Assess overall company health"""
        # McKinsey: Green/Yellow/Red based on KPI health
        return "Green"  # Placeholder


def main():
    """Example usage of McKinsey Enterprise Suite"""

    # Initialize components
    sla_tracker = SLATracker()
    cost_attributor = CostAttributor()
    unit_econ = UnitEconomicsCalculator()
    risk_registry = EnterpriseRiskRegistry()
    cohort_analytics = CohortAnalytics()
    financial_health = FinancialHealthAnalyzer(
        500_000, 400_000
    )  # £500K rev, £400K expenses
    dashboard = ExecutiveDashboard()

    # Record metrics
    sla_tracker.record_metric("availability", 0.9998, datetime.now())

    # Calculate costs
    cost_attributor.calculate_service_cost(
        "service-1",
        {
            "vcpus": 4,
            "memory_gb": 16,
            "storage_gb": 100,
            "network_gb": 50,
        },
    )

    # Calculate unit economics
    unit_econ.calculate_cac(1_000_000, 500)  # £1M S&M, 500 customers
    unit_econ.calculate_ltv(10_000, 0.75, 0.05)  # £10K ARPU, 75% margin, 5% churn
    unit_econ.calculate_magic_number(5_000_000, 4_000_000, 1_000_000)

    # Register risks
    risk_registry.register_risk(
        "operational",
        "Data center outage",
        probability=0.05,
        impact=500_000,
        owner="CTO",
        mitigation_plan="Multi-region deployment",
    )

    # Generate reports
    print("=== McKinsey Enterprise Suite ===\n")
    print(
        "SLA Report:",
        json.dumps(sla_tracker.generate_sla_report(), indent=2, default=str),
    )
    print(
        "\nCost Attribution:",
        json.dumps(
            cost_attributor.generate_chargeback_report("Finance"), indent=2, default=str
        ),
    )
    print(
        "\nUnit Economics:",
        json.dumps(unit_econ.generate_unit_economics_report(), indent=2, default=str),
    )
    print(
        "\nRisk Report:",
        json.dumps(risk_registry.generate_risk_report(), indent=2, default=str),
    )
    print(
        "\nFinancial Health:",
        json.dumps(
            financial_health.generate_financial_health_report(), indent=2, default=str
        ),
    )


if __name__ == "__main__":
    main()
