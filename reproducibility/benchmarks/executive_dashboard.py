#!/usr/bin/env python3
"""Board-ready executive operating dashboard."""

from datetime import datetime, timezone
from typing import Any, Dict


class ExecutiveDashboard:
    """McKinsey-grade executive dashboard."""

    def __init__(self):
        self.kpis = {
            "arr": 0,
            "arr_growth_yoy": 0,
            "logo_growth": 0,
            "customer_count": 0,
            "gross_margin": 0,
            "operating_margin": 0,
            "fcf": 0,
            "payback_period_months": 0,
            "magic_number": 0,
            "cac_payback_months": 0,
            "ltv_cac_ratio": 0,
            "sales_efficiency": 0,
            "nps": 0,
            "churn_rate": 0,
            "net_revenue_retention": 0,
            "upsell_rate": 0,
            "sla_availability": 0.9999,
            "sla_latency_p99": 0,
            "customer_acquisition_cost": 0,
            "support_cost_per_customer": 0,
        }

    def update_kpis(self, **kpis):
        self.kpis.update(kpis)
        return self.kpis

    def generate_quarterly_deck(self):
        """Generate board-ready dashboard."""
        return {
            "title": "Quarterly Business Review",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "slides": [
                {
                    "name": "Growth",
                    "metrics": {
                        k: self.kpis[k]
                        for k in [
                            "arr",
                            "arr_growth_yoy",
                            "logo_growth",
                            "customer_count",
                        ]
                    },
                },
                {
                    "name": "Profitability",
                    "metrics": {
                        k: self.kpis[k]
                        for k in ["gross_margin", "operating_margin", "fcf"]
                    },
                },
                {
                    "name": "Health",
                    "metrics": {
                        k: self.kpis[k]
                        for k in [
                            "nps",
                            "churn_rate",
                            "net_revenue_retention",
                            "sla_availability",
                        ]
                    },
                },
            ],
        }

    def generate_weekly_ops_review(self):
        """Generate ops review slides."""
        return {
            "title": "Weekly Operations Review",
            "metrics": {
                k: self.kpis[k]
                for k in [
                    "sla_availability",
                    "sla_latency_p99",
                    "support_cost_per_customer",
                    "churn_rate",
                ]
            },
        }
