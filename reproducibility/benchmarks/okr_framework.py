#!/usr/bin/env python3
"""Enterprise OKR management and reporting."""
from __future__ import annotations
from typing import Any, Dict

class OKRFramework:
    def __init__(self, fiscal_year: str): self.fiscal_year=fiscal_year; self.company_okrs=[]; self.team_okrs: Dict[str, list[dict]]={}
    def set_company_okr(self, objective: str, key_results: list[dict], owner: str) -> dict:
        okr={"objective":objective,"key_results":key_results,"owner":owner,"status":"active","progress":0}; self.company_okrs.append(okr); return okr
    def cascade_to_teams(self, company_okr: dict, team_id: str) -> dict:
        team_okr={"objective":company_okr["objective"],"key_results":company_okr["key_results"],"owner":team_id,"status":"active","progress":company_okr.get("progress",0)}; self.team_okrs.setdefault(team_id,[]).append(team_okr); return team_okr
    def track_progress(self) -> dict:
        def progress(okr):
            krs=okr.get("key_results",[]); return sum(float(kr.get("progress",0)) for kr in krs)/len(krs) if krs else okr.get("progress",0)
        for okr in self.company_okrs: okr["progress"]=progress(okr)
        return {"company_progress":sum(o["progress"] for o in self.company_okrs)/len(self.company_okrs) if self.company_okrs else 0,"team_count":len(self.team_okrs)}
    def generate_okr_report(self) -> dict: return {"fiscal_year":self.fiscal_year,"company_okrs":self.company_okrs,"team_okrs":self.team_okrs,"summary":self.track_progress()}
