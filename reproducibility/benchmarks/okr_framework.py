#!/usr/bin/env python3
"""Enterprise OKR tracking and alignment."""

from typing import Any, Dict, List


class OKRFramework:
    """Enterprise OKR management."""

    def __init__(self, fiscal_year):
        self.fiscal_year = fiscal_year
        self.company_okrs: List[Dict[str, Any]] = []
        self.team_okrs: Dict[str, List[Dict[str, Any]]] = {}

    def set_company_okr(self, objective, key_results, owner):
        """Set strategic OKR."""
        okr = {
            "objective": objective,
            "key_results": key_results,
            "owner": owner,
            "status": "active",
            "progress": 0,
        }
        self.company_okrs.append(okr)
        return okr

    def cascade_to_teams(self, company_okr, team_id):
        """Cascade OKRs to teams."""
        team_okr = {
            "parent_objective": company_okr["objective"],
            "key_results": company_okr["key_results"],
            "owner": team_id,
            "status": "active",
            "progress": 0,
        }
        self.team_okrs.setdefault(team_id, []).append(team_okr)
        return team_okr

    def track_progress(self):
        """Weekly/monthly progress tracking."""
        all_okrs = self.company_okrs + [okr for okrs in self.team_okrs.values() for okr in okrs]
        for okr in all_okrs:
            results = okr.get("key_results", [])
            if results and isinstance(results[0], dict):
                okr["progress"] = sum(kr.get("progress", 0) for kr in results) / len(results)
        return {
            "fiscal_year": self.fiscal_year,
            "company_progress": [o["progress"] for o in self.company_okrs],
            "team_count": len(self.team_okrs),
        }

    def generate_okr_report(self):
        """Executive summary of OKR achievement."""
        self.track_progress()
        avg = (
            sum(o["progress"] for o in self.company_okrs) / len(self.company_okrs)
            if self.company_okrs
            else 0
        )
        return {
            "fiscal_year": self.fiscal_year,
            "average_company_progress": avg,
            "company_okrs": self.company_okrs,
            "team_okrs": self.team_okrs,
        }
