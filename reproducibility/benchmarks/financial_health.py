#!/usr/bin/env python3
"""Financial health, runway, break-even, and profitability analysis."""


class FinancialHealthAnalyzer:
    """Track financial sustainability metrics."""

    def __init__(self):
        self.metrics = {}

    def calculate_monthly_burn_rate(self, expenses, revenue):
        burn = expenses - revenue
        return {"monthly_burn": burn, "burn_rate_months": max(burn, 0)}

    def calculate_payback_period(self, cumulative_cash_flow):
        for month, cash_flow in enumerate(cumulative_cash_flow):
            if cash_flow >= 0:
                return month
        return None

    def calculate_break_even_arr(self, fixed_costs, gross_margin):
        return fixed_costs / gross_margin if gross_margin else float("inf")

    def project_path_to_profitability(self, current_state, growth_assumptions):
        cash = current_state.get("cash", 0)
        revenue = current_state.get("monthly_revenue", 0)
        expenses = current_state.get("monthly_expenses", 0)
        rg = growth_assumptions.get("revenue_growth", 0)
        eg = growth_assumptions.get("expense_growth", 0)
        months = growth_assumptions.get("months", 24)
        timeline = []
        for month in range(1, months + 1):
            revenue *= 1 + rg
            expenses *= 1 + eg
            cash += revenue - expenses
            timeline.append(
                {
                    "month": month,
                    "revenue": revenue,
                    "expenses": expenses,
                    "cash": cash,
                    "profitable": revenue >= expenses,
                }
            )
            if revenue >= expenses:
                break
        return timeline
