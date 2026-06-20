#!/usr/bin/env python3
"""Executive dashboard KPI summaries."""
from __future__ import annotations

class ExecutiveDashboard:
    def __init__(self):
        self.kpis={"arr":0,"arr_growth_yoy":0,"logo_growth":0,"customer_count":0,"gross_margin":0,"operating_margin":0,"fcf":0,"payback_period_months":0,"magic_number":0,"cac_payback_months":0,"ltv_cac_ratio":0,"sales_efficiency":0,"nps":0,"churn_rate":0,"net_revenue_retention":0,"upsell_rate":0,"sla_availability":0.9999,"sla_latency_p99":0,"customer_acquisition_cost":0,"support_cost_per_customer":0}
    def update_kpi(self, name: str, value: float):
        if name not in self.kpis: raise KeyError(name)
        self.kpis[name]=value
    def generate_quarterly_deck(self) -> dict:
        return {"growth":{"arr":self.kpis["arr"],"arr_growth_yoy":self.kpis["arr_growth_yoy"]},"profitability":{"gross_margin":self.kpis["gross_margin"],"fcf":self.kpis["fcf"]},"health":{"nps":self.kpis["nps"],"churn_rate":self.kpis["churn_rate"]},"operational":{"sla_availability":self.kpis["sla_availability"],"sla_latency_p99":self.kpis["sla_latency_p99"]}}
    def generate_weekly_ops_review(self) -> dict:
        return {"sla": {"availability":self.kpis["sla_availability"],"latency_p99":self.kpis["sla_latency_p99"]},"customer": {"nps":self.kpis["nps"],"support_cost_per_customer":self.kpis["support_cost_per_customer"]}}
