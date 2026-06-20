#!/usr/bin/env python3
"""Unit economics and ARR forecasting."""


class UnitEconomicsCalculator:
    """McKinsey-standard unit economics."""

    def __init__(self):
        self.metrics = {
            "CAC": 0,
            "LTV": 0,
            "LTV_CAC_ratio": 0,
            "payback_period": 0,
            "gross_margin": 0,
            "magic_number": 0,
        }

    def calculate_ltv_cac(self, arpa, gross_margin, churn_rate, cac):
        self.metrics.update(
            {
                "CAC": cac,
                "gross_margin": gross_margin,
                "LTV": (arpa * gross_margin / churn_rate) if churn_rate else 0,
                "LTV_CAC_ratio": (
                    ((arpa * gross_margin / churn_rate) / cac) if churn_rate and cac else 0
                ),
                "payback_period": cac / (arpa * gross_margin / 12) if arpa and gross_margin else 0,
            }
        )
        return self.metrics

    def calculate_magic_number(self, arr_current, arr_previous, s_m_spend):
        self.metrics["magic_number"] = (arr_current - arr_previous) / s_m_spend if s_m_spend else 0
        return self.metrics["magic_number"]

    def forecast_arr(self, current_arr, magic_number, months):
        forecasts = []
        arr = current_arr
        for _ in range(months):
            arr *= 1 + (magic_number * 0.08)
            forecasts.append(arr)
        return forecasts
