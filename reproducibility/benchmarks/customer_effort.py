#!/usr/bin/env python3
"""Customer Effort Score tracking and churn-risk signals."""

from datetime import datetime, timezone
from typing import Any, Dict, List


class CustomerEffortAnalyzer:
    """Track ease of doing business."""

    def __init__(self):
        self.effort_scores: List[Dict[str, Any]] = []

    def measure_effort(self, interaction_id, effort_level, resolution_time):
        """Measure ease of specific interactions on a 1-5 scale."""
        record = {
            "interaction_id": interaction_id,
            "effort_level": effort_level,
            "resolution_time": resolution_time,
            "churn_risk": (
                "high"
                if effort_level >= 4
                else "medium" if effort_level == 3 else "low"
            ),
            "date": datetime.now(timezone.utc),
        }
        self.effort_scores.append(record)
        return record

    def summarize(self):
        avg = (
            sum(r["effort_level"] for r in self.effort_scores) / len(self.effort_scores)
            if self.effort_scores
            else 0
        )
        return {
            "average_effort": avg,
            "high_risk_interactions": [
                r for r in self.effort_scores if r["churn_risk"] == "high"
            ],
            "interaction_count": len(self.effort_scores),
        }
