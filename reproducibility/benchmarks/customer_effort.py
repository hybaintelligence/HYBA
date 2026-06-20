#!/usr/bin/env python3
"""Customer effort score analytics."""
from __future__ import annotations
from datetime import datetime, timezone

class CustomerEffortAnalyzer:
    def __init__(self): self.effort_scores=[]
    def measure_effort(self, interaction_id: str, effort_level: int, resolution_time: float) -> dict:
        rec={"interaction_id":interaction_id,"effort_level":int(effort_level),"resolution_time":float(resolution_time),"churn_risk":"high" if effort_level>=4 else "medium" if effort_level==3 else "low","date":datetime.now(timezone.utc).isoformat()}; self.effort_scores.append(rec); return rec
    def summarize(self) -> dict:
        n=len(self.effort_scores); return {"count":n,"average_effort":sum(x["effort_level"] for x in self.effort_scores)/n if n else 0,"high_risk_count":sum(x["churn_risk"]=="high" for x in self.effort_scores)}
