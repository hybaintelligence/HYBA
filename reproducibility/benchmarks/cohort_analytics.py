#!/usr/bin/env python3
"""Cohort retention, expansion, churn, LTV, and CAC analytics."""
from __future__ import annotations
from typing import Any, Dict

class CohortAnalytics:
    def __init__(self): self.cohorts: Dict[str, Dict[str, Any]]={}
    def create_cohort(self, cohort_id: str, start_date: str, customer_count: int, attributes: Dict[str, Any] | None=None):
        self.cohorts[cohort_id]={"start_date":start_date,"initial_size":int(customer_count),"attributes":attributes or {},"lifecycle_stages":[]}
    def track_cohort_metrics(self, cohort_id: str, month: int, metrics: Dict[str, float]) -> Dict[str, Any]:
        cohort=self.cohorts[cohort_id]; retained=metrics.get("retained_customers", cohort["initial_size"])
        stage={"month":int(month),**metrics,"retention_rate":retained/cohort["initial_size"] if cohort["initial_size"] else 0,"churn_rate":1-(retained/cohort["initial_size"] if cohort["initial_size"] else 0)}
        cohort["lifecycle_stages"].append(stage); return stage
    def generate_retention_curve(self) -> Dict[str, list[float]]:
        return {cid:[s["retention_rate"] for s in sorted(c["lifecycle_stages"], key=lambda x:x["month"])] for cid,c in self.cohorts.items()}
    def calculate_ltv_cac(self, cohort_id: str, gross_margin: float = .75) -> Dict[str, float]:
        stages=self.cohorts[cohort_id]["lifecycle_stages"]; revenue=sum(float(s.get("revenue",0)) for s in stages); cac=sum(float(s.get("cac",0)) for s in stages)
        return {"ltv":revenue*gross_margin,"cac":cac,"ltv_cac_ratio":(revenue*gross_margin/cac) if cac else 0}
