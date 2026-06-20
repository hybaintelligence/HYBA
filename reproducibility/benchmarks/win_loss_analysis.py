#!/usr/bin/env python3
"""Competitive win/loss analytics and positioning reports."""

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List


class WinLossAnalyzer:
    """Track competitive win/loss patterns."""

    def __init__(self):
        self.opportunities: List[Dict[str, Any]] = []

    def record_opportunity(
        self, opp_id, account_name, status, value, competitor, loss_reason, win_factor
    ):
        """Record sales opportunity outcome."""
        record = {
            "id": opp_id,
            "account": account_name,
            "status": status,
            "value": value,
            "competitor": competitor,
            "loss_reason": loss_reason,
            "win_factor": win_factor,
            "date": datetime.now(timezone.utc),
        }
        self.opportunities.append(record)
        return record

    def analyze_loss_patterns(self):
        """Identify patterns in lost deals."""
        losses = [o for o in self.opportunities if o["status"] == "lost"]
        return {
            "top_loss_reasons": Counter(o["loss_reason"] for o in losses).most_common(3),
            "lost_value": sum(o["value"] for o in losses),
            "loss_count": len(losses),
        }

    def competitive_positioning_report(self):
        """Generate competitive strength assessment."""
        by_competitor = defaultdict(lambda: {"won": 0, "lost": 0, "value": 0})
        for opp in self.opportunities:
            row = by_competitor[opp["competitor"]]
            row[opp["status"]] = row.get(opp["status"], 0) + 1
            row["value"] += opp["value"]
        return {"competitors": dict(by_competitor), "loss_patterns": self.analyze_loss_patterns()}
