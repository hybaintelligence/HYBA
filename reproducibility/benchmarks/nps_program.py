#!/usr/bin/env python3
"""NPS tracking, segment analysis, and churn-risk forecasting."""
from __future__ import annotations
from collections import Counter, defaultdict
from datetime import datetime, timezone

class NPSProgram:
    def __init__(self): self.surveys=[]; self.segments={}
    def _categorize(self, score: int) -> str: return "promoter" if score>=9 else "passive" if score>=7 else "detractor"
    def record_nps(self, customer_id: str, score: int, feedback: str, segment: str):
        self.surveys.append({"customer_id":customer_id,"score":score,"category":self._categorize(score),"feedback":feedback,"segment":segment,"date":datetime.now(timezone.utc).isoformat()})
    def analyze_by_segment(self) -> dict:
        grouped=defaultdict(list)
        for s in self.surveys: grouped[s["segment"]].append(s)
        return {seg:self._score(vals) for seg,vals in grouped.items()}
    def _score(self, vals) -> float:
        return 100*(sum(v["category"]=="promoter" for v in vals)-sum(v["category"]=="detractor" for v in vals))/len(vals) if vals else 0
    def identify_detractor_drivers(self) -> dict: return dict(Counter(w.lower().strip('.,') for s in self.surveys if s["category"]=="detractor" for w in s["feedback"].split()))
    def forecast_churn_risk(self) -> dict: return {s["customer_id"]:(.6 if s["category"]=="detractor" else .2 if s["category"]=="passive" else .05) for s in self.surveys}
