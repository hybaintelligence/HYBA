#!/usr/bin/env python3
"""Three-case financial model and sensitivity analysis."""
from __future__ import annotations
from typing import Any, Dict

class FinancialModelBuilder:
    def __init__(self): self.scenarios: Dict[str, Dict[str, Any]]={}
    def build_scenario(self, name: str, assumptions: Dict[str, float]) -> Dict[str, Any]:
        months=int(assumptions.get("months",12)); rev=assumptions.get("starting_revenue",0); growth=assumptions.get("monthly_growth",.05); cogs_pct=assumptions.get("cogs_pct",.25); opex=assumptions.get("monthly_opex",0); capex=assumptions.get("monthly_capex",0)
        s={"name":name,"assumptions":assumptions,"revenue":[],"cogs":[],"opex":[],"ebitda":[],"capex":[],"fcf":[]}
        for _ in range(months):
            rev*=1+growth; cogs=rev*cogs_pct; ebitda=rev-cogs-opex; s["revenue"].append(rev); s["cogs"].append(cogs); s["opex"].append(opex); s["ebitda"].append(ebitda); s["capex"].append(capex); s["fcf"].append(ebitda-capex)
        self.scenarios[name]=s; return s
    def run_sensitivity_analysis(self, variable: str, range_pct: float) -> Dict[str, Any]:
        return {name:{"variable":variable,"downside_pct":-abs(range_pct),"upside_pct":abs(range_pct),"base_fcf":sum(s["fcf"])} for name,s in self.scenarios.items()}
    def calculate_valuation_multiples(self, arr_multiple: float=8.0) -> Dict[str, float]:
        return {name:(s["revenue"][-1]*12*arr_multiple if s["revenue"] else 0) for name,s in self.scenarios.items()}
