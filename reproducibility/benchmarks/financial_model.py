#!/usr/bin/env python3
"""Three-case financial model, sensitivity analysis, and valuation multiples."""


class FinancialModelBuilder:
    """Build 3-case (bear/base/bull) financial model."""

    def __init__(self):
        self.scenarios = {}

    def build_scenario(self, name, assumptions):
        months = assumptions.get("months", 12)
        revenue = assumptions.get("starting_revenue", 0)
        growth = assumptions.get("monthly_growth", 0)
        gross_margin = assumptions.get("gross_margin", 0.75)
        opex = assumptions.get("monthly_opex", 0)
        capex = assumptions.get("monthly_capex", 0)
        scenario = {
            "name": name,
            "assumptions": assumptions,
            "revenue": [],
            "cogs": [],
            "opex": [],
            "ebitda": [],
            "capex": [],
            "fcf": [],
        }
        for _ in range(months):
            revenue *= 1 + growth
            cogs = revenue * (1 - gross_margin)
            ebitda = revenue - cogs - opex
            scenario["revenue"].append(revenue)
            scenario["cogs"].append(cogs)
            scenario["opex"].append(opex)
            scenario["ebitda"].append(ebitda)
            scenario["capex"].append(capex)
            scenario["fcf"].append(ebitda - capex)
        self.scenarios[name] = scenario
        return scenario

    def run_sensitivity_analysis(self, variable, range_pct):
        output = {}
        for name, scenario in self.scenarios.items():
            base_fcf = sum(scenario["fcf"])
            output[name] = {
                "variable": variable,
                "downside": base_fcf * (1 - range_pct),
                "base": base_fcf,
                "upside": base_fcf * (1 + range_pct),
            }
        return output

    def calculate_valuation_multiples(self):
        return {
            name: {
                "arr": (s["revenue"][-1] * 12 if s["revenue"] else 0),
                "ev_arr_at_8x": (s["revenue"][-1] * 12 * 8 if s["revenue"] else 0),
                "ebitda_margin": (
                    sum(s["ebitda"]) / sum(s["revenue"]) if sum(s["revenue"]) else 0
                ),
            }
            for name, s in self.scenarios.items()
        }
