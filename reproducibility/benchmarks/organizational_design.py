#!/usr/bin/env python3
"""RACI governance and escalation framework."""

from collections import Counter


class RACAMatrix:
    """Enterprise RACI matrix for governance."""

    def __init__(self):
        self.matrix = {}

    def define_ownership(self, decision_domain, responsible, accountable, consulted, informed):
        self.matrix[decision_domain] = {
            "responsible": responsible,
            "accountable": accountable,
            "consulted": consulted,
            "informed": informed,
        }

    def generate_escalation_path(self, decision_domain, resolution_time_hours):
        owner = self.matrix.get(decision_domain, {})
        return {
            "decision_domain": decision_domain,
            "tier_1": owner.get("responsible"),
            "tier_2": owner.get("accountable"),
            "resolution_time_hours": resolution_time_hours,
            "executive_escalation_hours": resolution_time_hours * 2,
        }

    def audit_decision_authority(self):
        gaps = [
            d
            for d, r in self.matrix.items()
            if not r.get("accountable") or not r.get("responsible")
        ]
        accountable_counts = Counter(str(r.get("accountable")) for r in self.matrix.values())
        return {
            "gaps": gaps,
            "overloaded_accountables": {k: v for k, v in accountable_counts.items() if v > 3},
            "domain_count": len(self.matrix),
        }
