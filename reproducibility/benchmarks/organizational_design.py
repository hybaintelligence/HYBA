#!/usr/bin/env python3
"""RACI ownership and escalation framework."""
from __future__ import annotations
from collections import Counter
from typing import Any, Dict, Iterable

class RACIMatrix:
    def __init__(self): self.matrix: Dict[str, Dict[str, Any]]={}
    def define_ownership(self, decision_domain: str, responsible: str, accountable: str, consulted: Iterable[str], informed: Iterable[str]):
        self.matrix[decision_domain]={"responsible":responsible,"accountable":accountable,"consulted":list(consulted),"informed":list(informed)}
    def generate_escalation_path(self, decision_domain: str, resolution_time_hours: int) -> Dict[str, Any]:
        row=self.matrix[decision_domain]; return {"domain":decision_domain,"level_1":row["responsible"],"level_2":row["accountable"],"deadline_hours":resolution_time_hours,"escalate_after_hours":max(1, resolution_time_hours//2)}
    def audit_decision_authority(self) -> Dict[str, Any]:
        missing=[d for d,r in self.matrix.items() if not r.get("responsible") or not r.get("accountable")]; counts=Counter(r["accountable"] for r in self.matrix.values())
        return {"domains":len(self.matrix),"missing_authority":missing,"accountability_load":dict(counts),"overloaded_accountable":[k for k,v in counts.items() if v>5]}
