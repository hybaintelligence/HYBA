#!/usr/bin/env python3
"""Enterprise risk registry and mitigation tracking."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List

class EnterpriseRiskRegistry:
    RISK_CATEGORIES={"operational":["availability","performance","security"],"strategic":["market","competition","technology"],"financial":["cost overrun","budget variance","capex"],"compliance":["regulatory","audit","legal"]}
    def __init__(self): self.risks: List[Dict[str, Any]]=[]
    def register_risk(self, category: str, description: str, probability: float, impact: float, owner: str, mitigation_plan: str | None=None) -> Dict[str, Any]:
        if category not in self.RISK_CATEGORIES: raise ValueError(f"unknown risk category: {category}")
        risk={"id":f"RISK-{len(self.risks)+1:03d}","category":category,"description":description,"probability":float(probability),"impact":float(impact),"risk_score":float(probability)*float(impact),"owner":owner,"mitigation_plan":mitigation_plan,"status":"mitigating" if mitigation_plan else "open","created":datetime.now(timezone.utc).isoformat()}
        self.risks.append(risk); return risk
    def update_mitigation(self, risk_id: str, mitigation_plan: str, status: str="mitigating") -> Dict[str, Any]:
        for risk in self.risks:
            if risk["id"] == risk_id: risk.update({"mitigation_plan":mitigation_plan,"status":status}); return risk
        raise KeyError(risk_id)
    def calculate_risk_adjusted_metrics(self, base_metrics: Dict[str, float]) -> Dict[str, float]:
        exposure=sum(r["risk_score"] for r in self.risks); factor=1-min(exposure,0.25)
        return {k:float(v)*factor for k,v in base_metrics.items()}
    def generate_risk_report(self) -> Dict[str, Any]:
        return {"risk_count":len(self.risks),"total_exposure":sum(r["risk_score"] for r in self.risks),"top_risks":sorted(self.risks,key=lambda r:r["risk_score"],reverse=True)[:5],"open_risks":[r for r in self.risks if r["status"]!="closed"]}
