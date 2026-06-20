#!/usr/bin/env python3
"""SaaS unit economics and ARR forecasting."""
from __future__ import annotations

class UnitEconomicsCalculator:
    def __init__(self): self.metrics={"CAC":0,"LTV":0,"LTV_CAC_ratio":0,"payback_period":0,"gross_margin":0,"magic_number":0}
    def calculate_magic_number(self, arr_current: float, arr_previous: float, s_m_spend: float) -> float:
        self.metrics["magic_number"]=(arr_current-arr_previous)/s_m_spend if s_m_spend else 0; return self.metrics["magic_number"]
    def calculate_ltv_cac(self, arpa: float, gross_margin: float, churn_rate: float, cac: float) -> dict:
        ltv=(arpa*gross_margin/churn_rate) if churn_rate else 0; self.metrics.update({"CAC":cac,"LTV":ltv,"LTV_CAC_ratio":ltv/cac if cac else 0,"gross_margin":gross_margin}); return self.metrics
    def calculate_payback_period(self, cac: float, arpa: float, gross_margin: float) -> float:
        self.metrics["payback_period"]=cac/(arpa*gross_margin) if arpa and gross_margin else 0; return self.metrics["payback_period"]
    def forecast_arr(self, current_arr: float, magic_number: float, months: int) -> list[float]:
        out=[]; arr=current_arr
        for _ in range(months): arr *= 1+(magic_number*.08); out.append(arr)
        return out
