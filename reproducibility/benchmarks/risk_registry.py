#!/usr/bin/env python3
"""Enterprise risk registry and mitigation tracking."""

from datetime import datetime, timezone
from typing import Any, Dict, List


class EnterpriseRiskRegistry:
    """McKinsey-grade risk management."""

    RISK_CATEGORIES = {
        "operational": ["availability", "performance", "security"],
        "strategic": ["market", "competition", "technology"],
        "financial": ["cost overrun", "budget variance", "capex"],
        "compliance": ["regulatory", "audit", "legal"],
    }

    def __init__(self):
        self.risks: List[Dict[str, Any]] = []

    def register_risk(
        self,
        category: str,
        description: str,
        probability: float,
        impact: float,
        owner: str,
    ) -> Dict[str, Any]:
        """Register identified risk with mitigation plan."""
        if category not in self.RISK_CATEGORIES:
            raise ValueError(f"Unknown risk category: {category}")
        risk = {
            "id": f"RISK-{len(self.risks)+1:04d}",
            "category": category,
            "description": description,
            "probability": max(0.0, min(1.0, probability)),
            "impact": impact,
            "risk_score": max(0.0, min(1.0, probability)) * impact,
            "owner": owner,
            "mitigation_plan": None,
            "status": "open",
            "created": datetime.now(timezone.utc),
        }
        self.risks.append(risk)
        return risk

    def set_mitigation_plan(
        self, risk_id: str, plan: str, status: str = "mitigating"
    ) -> Dict[str, Any]:
        """Attach mitigation plan and update risk status."""
        for risk in self.risks:
            if risk["id"] == risk_id:
                risk["mitigation_plan"] = plan
                risk["status"] = status
                return risk
        raise KeyError(risk_id)

    def calculate_risk_adjusted_metrics(
        self, base_metrics: Dict[str, float]
    ) -> Dict[str, float]:
        """Adjust KPIs for identified risks, capped at 25%."""
        exposure = sum(r["risk_score"] for r in self.risks if r["status"] != "closed")
        adjustment = min(exposure, 0.25)
        return {key: value * (1 - adjustment) for key, value in base_metrics.items()}
