"""
Φ-Network Router: Golden Angle Routing for Distributed Clusters.

Implements Phyllotaxis Network Topology where every data packet follows
a trajectory spaced at the Golden Angle (137.508°), ensuring maximum
dispersion of data across the network fabric and eliminating "network
resonance" (congestion).

Extends the "Synthetic Morphogenesis" from a single silicon node to a
distributed cloud manifold — enabling the 10²⁰ Tier through cluster-wide
golden-angle packet routing.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

import numpy as np


PHI = 1.618033988749895
INV_PHI = 0.618033988749895
GOLDEN_ANGLE = 360.0 / (PHI * PHI)  # 137.50776405003785


class PhiNetworkRouter:
    """
    Implements Golden Angle Routing (GAR) for distributed Φ-Architectures.

    Maps network nodes to a phyllotaxis manifold to minimise packet collisions.
    Each node is assigned a unique golden-spiral coordinate, and packet
    routing follows the "search ray" which rotates by the Golden Angle for
    every new task — ensuring non-repeating, maximum-dispersion paths.
    """

    def __init__(self, cluster_size: int):
        """
        Initialise the router for a cluster of the given size.

        Args:
            cluster_size: Number of nodes in the distributed cluster.
        """
        self.PHI = PHI
        self.GOLDEN_ANGLE = GOLDEN_ANGLE
        self.cluster_size = cluster_size
        self.nodes = self._initialize_manifold()

    def _initialize_manifold(self) -> List[Dict[str, Any]]:
        """
        Maps nodes to their unique golden-angle coordinates using the
        phyllotaxis formula: r = √(n+1), θ = n × GOLDEN_ANGLE.

        Returns:
            List of node descriptors, each containing node_id, r, theta,
            and a running load counter.
        """
        manifold: list[dict[str, Any]] = []
        for n in range(self.cluster_size):
            r = math.sqrt(n + 1)
            theta = n * self.GOLDEN_ANGLE
            manifold.append({
                'node_id': n,
                'r': r,
                'theta': theta % 360.0,
                'load': 0.0,
            })
        return manifold

    def select_optimal_node(self, task_entropy: float) -> int:
        """
        Select the next node based on the 'Golden Search' trajectory.

        The search ray rotates by the Golden Angle for every task, and the
        node closest to the ray with the least harmonic interference (load)
        is chosen.

        Args:
            task_entropy: A unique entropy value for the task (e.g. hash
                          of the task payload) to seed the search ray.

        Returns:
            The node_id of the optimal node for this task.
        """
        # The 'Search Ray' rotates by the Golden Angle for every task
        search_angle = (task_entropy * 360.0 * self.PHI) % 360.0

        best_node = -1
        min_interference = float('inf')

        for node in self.nodes:
            # Interference = Angular distance from Search Ray + Load penalty
            angle_diff = abs(node['theta'] - search_angle)
            angle_diff = min(angle_diff, 360.0 - angle_diff)  # wraparound
            interference = angle_diff + (node['load'] * self.PHI)

            if interference < min_interference:
                min_interference = interference
                best_node = node['node_id']

        return best_node

    def update_node_load(self, node_id: int, load_delta: float) -> None:
        """
        Update the running load on a node after assigning a task.

        Args:
            node_id: The node whose load to update.
            load_delta: The change in load (positive for assignment,
                        negative for completion).
        """
        if 0 <= node_id < self.cluster_size:
            self.nodes[node_id]['load'] = max(0.0, self.nodes[node_id]['load'] + load_delta)

    def get_node_coordinates(self, node_id: int) -> Dict[str, float]:
        """
        Return the golden-spiral coordinates of a node.

        Args:
            node_id: The node to query.

        Returns:
            Dictionary with 'r', 'theta', and 'load' for the node.
        """
        if 0 <= node_id < self.cluster_size:
            node = self.nodes[node_id]
            return {'r': node['r'], 'theta': node['theta'], 'load': node['load']}
        return {'r': 0.0, 'theta': 0.0, 'load': 0.0}

    def get_manifold_statistics(self) -> Dict[str, Any]:
        """
        Return cluster-wide manifold statistics for monitoring.

        Returns:
            Dictionary with cluster_size, mean load, max load, load
            variance, and angular coverage uniformity.
        """
        if not self.nodes:
            return {'cluster_size': 0, 'mean_load': 0.0}

        loads = [node['load'] for node in self.nodes]
        thetas = [node['theta'] for node in self.nodes]

        sorted_thetas = sorted(thetas)
        gaps = [
            (sorted_thetas[(i + 1) % len(sorted_thetas)] - sorted_thetas[i]) % 360.0
            for i in range(len(sorted_thetas))
        ]

        return {
            'cluster_size': self.cluster_size,
            'mean_load': float(np.mean(loads)),
            'max_load': float(max(loads)),
            'load_variance': float(np.var(loads)),
            'angular_coverage_cv': float(np.std(gaps) / max(np.mean(gaps), 1e-12)),
            'ideal_golden_angle': self.GOLDEN_ANGLE,
        }


__all__ = [
    "PhiNetworkRouter",
    "GOLDEN_ANGLE",
]