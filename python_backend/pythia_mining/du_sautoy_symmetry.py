"""Du Sautoy Symmetry Exploitation Engine.

Uses group theory and symmetry to exponentially reduce search space.
The PULVINI D/I compound has 120-element automorphism group - exploit it!
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Dict, List, Set, Tuple

import numpy as np

PHI = (1 + math.sqrt(5)) / 2  # Golden ratio


@dataclass
class OrbitStructure:
    """Equivalence class of nodes under symmetry group"""

    representative: int
    orbit_members: List[int]
    orbit_size: int
    stabilizer_size: int

    def to_dict(self) -> dict:
        return asdict(self)


class SymmetryExploitationEngine:
    """Du Sautoy: use symmetry to reduce search exponentially.

    The D/I compound has 120 automorphisms. Nodes in the same orbit under
    this group action are equivalent - only need to search one representative.
    """

    def __init__(self, automorphisms: List[Dict[int, int]]):
        """Initialize with automorphism group.

        Args:
            automorphisms: List of permutations (each is dict: node_id -> node_id)
        """
        self.automorphisms = automorphisms
        self.group_size = len(automorphisms)
        self.orbits = self._compute_orbits()
        self.orbit_map = self._build_orbit_map()
        self.search_reduction_factor = 32.0 / len(self.orbits)

    def _compute_orbits(self) -> List[OrbitStructure]:
        """Partition nodes into equivalence classes under group action"""

        visited: Set[int] = set()
        orbits: List[OrbitStructure] = []

        for node in range(32):
            if node in visited:
                continue

            # Compute orbit of this node
            orbit_members = {node}
            for automorphism in self.automorphisms:
                # automorphism is tuple: (node_0_image, node_1_image, ..., node_31_image)
                if isinstance(automorphism, (list, tuple)) and len(automorphism) > node:
                    orbit_members.add(int(automorphism[node]))
                elif isinstance(automorphism, dict):
                    orbit_members.add(automorphism.get(node, node))

            visited.update(orbit_members)

            # Compute stabilizer size (automorphisms that fix this node)
            stabilizer_size = 0
            for aut in self.automorphisms:
                if isinstance(aut, (list, tuple)) and len(aut) > node:
                    if int(aut[node]) == node:
                        stabilizer_size += 1
                elif isinstance(aut, dict):
                    if aut.get(node, node) == node:
                        stabilizer_size += 1

            orbits.append(
                OrbitStructure(
                    representative=node,
                    orbit_members=sorted(orbit_members),
                    orbit_size=len(orbit_members),
                    stabilizer_size=stabilizer_size,
                )
            )

        return orbits

    def _build_orbit_map(self) -> Dict[int, int]:
        """Map each node to its orbit representative"""

        orbit_map = {}
        for orbit in self.orbits:
            for member in orbit.orbit_members:
                orbit_map[member] = orbit.representative

        return orbit_map

    def reduce_search_space_by_orbit(self, node_assignments: Dict[int, any]) -> Dict[int, any]:
        """Return only orbit representatives from full node set"""

        reduced = {}
        for orbit in self.orbits:
            rep = orbit.representative
            if rep in node_assignments:
                reduced[rep] = node_assignments[rep]

        return reduced

    def expand_result_to_full_orbit(self, representative_results: Dict[int, any]) -> Dict[int, any]:
        """Expand results from representatives to full orbit"""

        full_results = {}
        for orbit in self.orbits:
            rep = orbit.representative
            if rep in representative_results:
                # Apply result to all orbit members
                for member in orbit.orbit_members:
                    full_results[member] = representative_results[rep]

        return full_results

    def exploit_symmetry_for_nonce_allocation(
        self, total_nonce_space: int
    ) -> Dict[int, Tuple[int, int]]:
        """Allocate nonce ranges using orbit structure"""

        # Only allocate to orbit representatives
        nonces_per_orbit = total_nonce_space // len(self.orbits)

        allocations = {}
        current_nonce = 0

        for orbit in self.orbits:
            # Weight by orbit size (larger orbits get more nonces)
            weighted_allocation = int(nonces_per_orbit * orbit.orbit_size / orbit.stabilizer_size)

            allocations[orbit.representative] = (
                current_nonce,
                current_nonce + weighted_allocation - 1,
            )
            current_nonce += weighted_allocation

        return allocations

    def fibonacci_heap_allocation(self) -> Dict[int, float]:
        """Du Sautoy: Fibonacci numbers emerge from golden ratio.

        Use Fibonacci sequence for node capacity allocation.
        """

        def fib(n: int) -> int:
            """Compute nth Fibonacci number"""
            if n <= 1:
                return n
            phi_n = PHI**n
            psi_n = -(PHI**-n)
            return int((phi_n - psi_n) / math.sqrt(5))

        # Allocate Fibonacci(orbit_index) capacity to each orbit
        capacities = {}
        for i, orbit in enumerate(self.orbits):
            capacity = float(fib(i + 2))  # Start at fib(2) = 1
            for member in orbit.orbit_members:
                capacities[member] = capacity

        # Normalize
        total = sum(capacities.values())
        return {node: cap / total for node, cap in capacities.items()}

    def golden_spiral_search(self, center_nonce: int, max_radius: int) -> List[int]:
        """Du Sautoy: search in golden spiral pattern.

        Golden angle = 2π / φ creates optimal packing.
        """

        nonces = []
        angle = 0.0
        radius = 1.0
        golden_angle = 2 * math.pi / PHI

        while radius < max_radius:
            # Convert polar to nonce offset
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            nonce_offset = int(x + y * 1000)  # Map 2D to 1D

            nonce = (center_nonce + nonce_offset) % (2**32)
            nonces.append(nonce)

            # Step in golden spiral
            angle += golden_angle
            radius *= PHI ** (1.0 / 32.0)  # Slow spiral

        return nonces

    def detect_temporal_symmetry(self, share_history: List[Dict[str, any]]) -> Dict[str, any]:
        """Du Sautoy: patterns are symmetries in data.

        Look for periodicity in successful shares.
        """

        if len(share_history) < 10:
            return {"periodicity": None, "confidence": 0.0}

        # Extract timestamps of successful shares
        success_times = [s["timestamp"] for s in share_history if s.get("accepted", False)]

        if len(success_times) < 5:
            return {"periodicity": None, "confidence": 0.0}

        # Compute inter-arrival times
        intervals = np.diff(success_times)

        # Look for periodicity using autocorrelation
        if len(intervals) < 3:
            return {"periodicity": None, "confidence": 0.0}

        # Simple period detection: most common interval
        interval_counts = defaultdict(int)
        for interval in intervals:
            # Bin intervals to nearest second
            binned = round(interval)
            interval_counts[binned] += 1

        if not interval_counts:
            return {"periodicity": None, "confidence": 0.0}

        most_common_interval = max(interval_counts, key=interval_counts.get)
        confidence = interval_counts[most_common_interval] / len(intervals)

        return {
            "periodicity": most_common_interval,
            "confidence": float(confidence),
            "detected": confidence > 0.5,
        }

    def discover_spatial_symmetry(
        self, successful_node_patterns: List[List[int]]
    ) -> Dict[str, any]:
        """Find geometric patterns in successful node sequences"""

        if len(successful_node_patterns) < 3:
            return {"patterns": [], "confidence": 0.0}

        # Look for node patterns that repeat
        pattern_counts = defaultdict(int)

        for pattern in successful_node_patterns:
            # Check if pattern maps to itself under some automorphism
            for automorphism in self.automorphisms:
                mapped = [automorphism.get(node, node) for node in pattern]
                if sorted(mapped) == sorted(pattern):
                    # Pattern is symmetric under this automorphism
                    pattern_tuple = tuple(sorted(pattern))
                    pattern_counts[pattern_tuple] += 1

        if not pattern_counts:
            return {"patterns": [], "confidence": 0.0}

        # Return most symmetric patterns
        sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)

        return {
            "patterns": [
                {"nodes": list(pattern), "symmetry_count": count}
                for pattern, count in sorted_patterns[:5]
            ],
            "confidence": (
                float(sorted_patterns[0][1] / len(successful_node_patterns))
                if sorted_patterns
                else 0.0
            ),
        }

    def get_symmetry_metrics(self) -> Dict[str, any]:
        """Return symmetry exploitation statistics"""

        return {
            "group_size": self.group_size,
            "num_orbits": len(self.orbits),
            "search_reduction_factor": self.search_reduction_factor,
            "orbit_sizes": [orbit.orbit_size for orbit in self.orbits],
            "largest_orbit": max(orbit.orbit_size for orbit in self.orbits),
            "smallest_orbit": min(orbit.orbit_size for orbit in self.orbits),
            "avg_stabilizer_size": float(np.mean([orbit.stabilizer_size for orbit in self.orbits])),
        }


__all__ = ["SymmetryExploitationEngine", "OrbitStructure"]
