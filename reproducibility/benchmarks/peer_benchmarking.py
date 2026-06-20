#!/usr/bin/env python3
"""Peer benchmarking against SaaS operating medians."""


class PeerBenchmarking:
    """Compare against SaaS benchmarks."""

    def __init__(self):
        self.peer_data = {
            "arr_growth_median": 0.35,
            "gross_margin_median": 0.75,
            "nps_median": 50,
            "magic_number_median": 0.75,
            "payback_period_median_months": 14,
            "ltv_cac_ratio_median": 3.5,
        }

    def compare_to_peers(self, company_metrics):
        """Compare company metrics to SaaS benchmarks."""
        comparison = {}
        for metric, value in company_metrics.items():
            if metric in self.peer_data:
                peer_value = self.peer_data[metric]
                percentile = (value / peer_value) * 100 if peer_value else 0
                comparison[metric] = {
                    "company": value,
                    "peer_median": peer_value,
                    "percentile": percentile,
                    "position": self._percentile_ranking(percentile),
                }
        return comparison

    def _percentile_ranking(self, percentile):
        if percentile >= 75:
            return "Top Quartile"
        if percentile >= 50:
            return "Above Median"
        if percentile >= 25:
            return "Below Median"
        return "Bottom Quartile"
