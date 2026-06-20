#!/usr/bin/env python3
"""Competitive win/loss analysis."""
from __future__ import annotations
from collections import Counter, defaultdict
from datetime import datetime, timezone

class WinLossAnalyzer:
    def __init__(self): self.opportunities=[]
    def record_opportunity(self, opp_id: str, account_name: str, status: str, value: float, competitor: str, loss_reason: str | None, win_factor: str | None):
        self.opportunities.append({"id":opp_id,"account":account_name,"status":status,"value":float(value),"competitor":competitor,"loss_reason":loss_reason,"win_factor":win_factor,"date":datetime.now(timezone.utc).isoformat()})
    def analyze_loss_patterns(self) -> dict:
        losses=[o for o in self.opportunities if o["status"]=="lost"]; return {"loss_count":len(losses),"top_loss_reasons":Counter(o["loss_reason"] for o in losses).most_common(3),"lost_value":sum(o["value"] for o in losses)}
    def competitive_positioning_report(self) -> dict:
        by=defaultdict(lambda:{"won":0,"lost":0,"value_won":0.0})
        for o in self.opportunities:
            by[o["competitor"]][o["status"]]+=1; by[o["competitor"]]["value_won"] += o["value"] if o["status"]=="won" else 0
        return dict(by)
