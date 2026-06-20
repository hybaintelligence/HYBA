#!/usr/bin/env python3
"""Break-even, runway, payback, and profitability analysis."""
from __future__ import annotations

class FinancialHealthAnalyzer:
    def __init__(self): self.metrics={}
    def calculate_monthly_burn_rate(self, expenses: float, revenue: float) -> dict:
        burn=expenses-revenue; return {"monthly_burn":burn,"burn_rate_months":max(burn,0)}
    def calculate_payback_period(self, cumulative_cash_flow: list[float]) -> int | None:
        for i,v in enumerate(cumulative_cash_flow):
            if v >= 0: return i
        return None
    def calculate_break_even_arr(self, fixed_costs: float, gross_margin: float) -> float: return fixed_costs/gross_margin if gross_margin else float("inf")
    def project_path_to_profitability(self, current_state: dict, growth_assumptions: dict) -> dict:
        revenue=current_state.get("monthly_revenue",0); expenses=current_state.get("monthly_expenses",0); growth=growth_assumptions.get("monthly_revenue_growth",.05)
        for month in range(1,121):
            if revenue >= expenses: return {"months_to_profitability":month-1,"projected_revenue":revenue,"projected_expenses":expenses}
            revenue*=1+growth
        return {"months_to_profitability":None,"projected_revenue":revenue,"projected_expenses":expenses}
