#!/usr/bin/env python3
"""Organizational change impact assessment."""


class ChangeImpactAssessor:
    """Assess organizational impact of technical changes."""

    def __init__(self):
        self.stakeholder_map = {}

    def assess_change_impact(self, change_description, affected_systems):
        return {
            "change": change_description,
            "technical": affected_systems,
            "operational": [f"Runbook update for {s}" for s in affected_systems],
            "financial": ["Budget and chargeback review"],
            "organizational": list(self.stakeholder_map.keys()),
            "customer_facing": [
                s
                for s in affected_systems
                if "api" in s.lower() or "customer" in s.lower()
            ],
        }

    def generate_change_communication_plan(self, change, stakeholders):
        return {
            "change": change,
            "waves": [
                {"name": "awareness", "audience": stakeholders, "timing": "T-14 days"},
                {"name": "readiness", "audience": stakeholders, "timing": "T-3 days"},
                {"name": "go-live", "audience": stakeholders, "timing": "T day"},
                {
                    "name": "reinforcement",
                    "audience": stakeholders,
                    "timing": "T+7 days",
                },
            ],
        }
