#!/usr/bin/env python3
"""Cohort retention, expansion, churn, LTV, and CAC analytics."""

from typing import Any, Dict


class CohortAnalytics:
    """Track customer/service cohort behavior."""

    def __init__(self):
        self.cohorts: Dict[str, Dict[str, Any]] = {}

    def create_cohort(self, cohort_id, start_date, customer_count, attributes):
        self.cohorts[cohort_id] = {
            "start_date": start_date,
            "initial_size": customer_count,
            "attributes": attributes,
            "lifecycle_stages": [],
        }

    def track_cohort_metrics(self, cohort_id, month, metrics):
        cohort = self.cohorts[cohort_id]
        retained = metrics.get("retained_customers", cohort["initial_size"])
        revenue = metrics.get("revenue", 0.0)
        cac = metrics.get("cac", 0.0)
        stage = {
            "month": month,
            "metrics": metrics,
            "retention_rate": (
                retained / cohort["initial_size"] if cohort["initial_size"] else 0
            ),
            "churn_rate": 1
            - (retained / cohort["initial_size"] if cohort["initial_size"] else 0),
            "ltv_to_date": (
                revenue / cohort["initial_size"] if cohort["initial_size"] else 0
            ),
            "cac_payback_month": month if revenue >= cac and cac else None,
        }
        cohort["lifecycle_stages"].append(stage)
        return stage

    def generate_retention_curve(self):
        return {
            cid: [
                {"month": s["month"], "retention_rate": s["retention_rate"]}
                for s in c["lifecycle_stages"]
            ]
            for cid, c in self.cohorts.items()
        }
