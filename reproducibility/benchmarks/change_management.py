#!/usr/bin/env python3
"""Organizational change impact and communications planning."""
from __future__ import annotations
from typing import Any, Dict, Iterable

class ChangeImpactAssessor:
    def __init__(self): self.stakeholder_map: Dict[str, list[str]]={}
    def assess_change_impact(self, change_description: str, affected_systems: Iterable[str]) -> Dict[str, Any]:
        systems=list(affected_systems); high=len(systems)>=3
        return {"change":change_description,"affected_systems":systems,"technical":systems,"operational":["runbook","support"] if high else ["runbook"],"financial":["cost_model"],"organizational":["training"],"customer_facing":["release_notes"] if high else [],"risk":"high" if high else "medium"}
    def generate_change_communication_plan(self, change: str, stakeholders: Iterable[str]) -> Dict[str, Any]:
        return {"change":change,"waves":[{"day":-7,"audience":list(stakeholders),"message":"advance notice"},{"day":0,"audience":list(stakeholders),"message":"launch and support path"},{"day":7,"audience":list(stakeholders),"message":"adoption check"}]}
