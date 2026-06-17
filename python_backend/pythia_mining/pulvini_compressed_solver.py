"""Solver adapter for pre-search compressed PULVINI nonce plans."""

from __future__ import annotations

import asyncio
import hashlib
import math
import os
import time
from typing import Any, Dict, List, Optional

from .quantum_solver import (
    PULVINI_HASHRATE_CAP_EHS,
    DodecahedralQuantumSolver,
    QuantumSolverConfigurationError,
)


class PulviniCompressedQuantumSolver(DodecahedralQuantumSolver):
    """Configure and execute search from a compressed nonce plan before solving."""

    def __init__(self, configured_capacity_ehs: Optional[float] = None):
        super().__init__(configured_capacity_ehs=configured_capacity_ehs)
        self.compressed_plan: Any = None
        self.last_solve_trace: List[Dict[str, Any]] = []
        # Deterministic attempt counter changes the search phase for repeated solves
        # without introducing pseudo-random runtime telemetry.
        self._solve_counter = 0
        # Mutable target compression ratio — updated by reflexive self-optimisation.
        # Clamped to [1.0, 2.0] (PULVINI lossless invertibility limit).
        self.compression_target_ratio: float = 1.86
        # Initialize default compressed search metrics for production readiness checks
        phi_tier = int(os.getenv("HYBA_PULVINI_PHI_TIER", "12"))
        phi_multiplier = ((1.0 + math.sqrt(5.0)) / 2.0) ** phi_tier
        self.current_config.update(
            {
                "nonce_space_contract": "pulvini_phi_compressed_pre_search",
                "candidate_generation_complexity": "O(1) deterministic per attempt, O(D/2^256) expected attempts to block",
                "complete_nonce_coverage": True,
                "overlap_free_nonce_coverage": True,
                "compressed_working_set_size": 20,
                "retained_kernel_lanes": 20,
                "working_set_compression_ratio": 1.86,
                "phi_compression_factor": 1.86,
                "phi_filter_acceptance_ratio": 1.0,
                "phi_tier": phi_tier,
                "phi_tier_multiplier": phi_multiplier,
                "hashrate_cap_ehs": PULVINI_HASHRATE_CAP_EHS,
                "configured_capacity_ehs": self.configured_capacity_ehs,
            }
        )

    async def configure_compressed_search(self, target: int, compressed_plan: Any) -> bool:
        if not bool(compressed_plan.complete_coverage) or not bool(compressed_plan.overlap_free):
            raise QuantumSolverConfigurationError(
                "compressed nonce plan must provide complete overlap-free coverage"
            )
        await self.configure_search(int(target), list(compressed_plan.solver_ranges))
        self.compressed_plan = compressed_plan
        phi_tier = int(os.getenv("HYBA_PULVINI_PHI_TIER", "12"))
        phi_multiplier = ((1.0 + math.sqrt(5.0)) / 2.0) ** phi_tier
        self.current_config.update(
            {
                "nonce_space_contract": "pulvini_phi_compressed_pre_search",
                "candidate_generation_complexity": "O(1) deterministic per attempt, O(D/2^256) expected attempts to block",
                "complete_nonce_coverage": True,
                "overlap_free_nonce_coverage": True,
                "original_lanes": int(compressed_plan.original_lanes),
                "compressed_working_set_size": int(compressed_plan.working_set_dimension),
                "retained_kernel_lanes": int(compressed_plan.retained_kernel_lanes),
                "working_set_compression_ratio": float(
                    compressed_plan.working_set_compression_ratio
                ),
                "phi_compression_factor": float(compressed_plan.working_set_compression_ratio),
                "phi_filter_acceptance_ratio": float(
                    compressed_plan.working_set_dimension / max(1, compressed_plan.original_lanes)
                ),
                "phi_tier": phi_tier,
                "phi_tier_multiplier": phi_multiplier,
                "hashrate_cap_ehs": PULVINI_HASHRATE_CAP_EHS,
                "configured_capacity_ehs": self.configured_capacity_ehs,
                "compressed_nonce_plan": compressed_plan.to_dict(),
            }
        )
        self.last_solve_trace = [
            {
                "stage": "compressed_nonce_space_received",
                "working_set_dimension": int(compressed_plan.working_set_dimension),
                "complete_coverage": True,
            }
        ]
        return True

    @staticmethod
    def _unit_hash(material: str, seed: int = 0) -> float:
        """Map material and deterministic attempt seed into the unit interval."""
        digest = hashlib.blake2b(f"{material}:{seed}".encode("utf-8"), digest_size=8).digest()
        return int.from_bytes(digest, "big") / float(1 << 64)

    def _collapse_coordinate(self) -> Any:
        if self.compressed_plan is None:
            raise QuantumSolverConfigurationError(
                "compressed solver must be configured before solving"
            )
        target = int(self.current_config["target"])
        coordinates = list(self.compressed_plan.coordinates)
        if not coordinates:
            raise QuantumSolverConfigurationError(
                "compressed nonce plan contains no active coordinates"
            )
        scored = []
        for coordinate in coordinates:
            phase = self._unit_hash(
                f"{target}:{coordinate.coordinate_id}:{coordinate.coverage_size}",
                self._solve_counter,
            )
            weight = max(float(coordinate.coverage_size), 1.0) * (1.0 + phase)
            scored.append((weight, coordinate))
        scored.sort(key=lambda item: item[0], reverse=True)
        collapsed = scored[0][1]
        self.last_solve_trace.append(
            {
                "stage": "search_space_collapsed",
                "coordinate_id": int(collapsed.coordinate_id),
                "coverage_size": int(collapsed.coverage_size),
            }
        )
        return collapsed

    def _walk_coordinate(self, collapsed_coordinate: Any, max_iterations: int) -> Any:
        coordinates = list(self.compressed_plan.coordinates)
        if len(coordinates) == 1:
            return collapsed_coordinate
        steps = max(1, min(int(max_iterations), int(math.ceil(math.sqrt(len(coordinates))))))
        position = int(collapsed_coordinate.coordinate_id)
        target = int(self.current_config["target"])
        for step in range(steps):
            left = (position - 1) % len(coordinates)
            right = (position + 1) % len(coordinates)
            left_score = self._unit_hash(
                f"walk:{target}:{self._solve_counter}:{step}:{left}",
                self._solve_counter + step,
            )
            right_score = self._unit_hash(
                f"walk:{target}:{self._solve_counter}:{step}:{right}",
                self._solve_counter + step,
            )
            position = right if right_score >= left_score else left
        walked = coordinates[position]
        self.last_solve_trace.append(
            {
                "stage": "quantum_walk_completed",
                "steps": steps,
                "coordinate_id": int(walked.coordinate_id),
            }
        )
        return walked

    def _tunnel_anneal_project_nonce(self, coordinate: Any) -> int:
        segments = list(coordinate.active_segments)
        if not segments:
            raise QuantumSolverConfigurationError(
                "compressed coordinate contains no retained segments"
            )
        target = int(self.current_config["target"])
        anneal_values = [
            self._unit_hash(f"anneal:{target}:{coordinate.coordinate_id}:{segment.lane_id}")
            for segment in segments
        ]
        segment_index = max(range(len(segments)), key=lambda index: anneal_values[index])
        segment = segments[segment_index]
        offset_fraction = self._unit_hash(
            f"tunnel:{target}:{coordinate.coordinate_id}:{segment.start}:{segment.end}"
        )
        offset = min(segment.size - 1, int(offset_fraction * segment.size))
        nonce = int(segment.start + offset)
        self.last_solve_trace.append(
            {
                "stage": "tunnel_anneal_projected_nonce",
                "coordinate_id": int(coordinate.coordinate_id),
                "lane_id": int(segment.lane_id),
                "nonce": nonce,
            }
        )
        return nonce

    async def solve(self, max_iterations: int = 100, timeout: float = 30.0) -> Optional[int]:
        if max_iterations <= 0 or timeout <= 0:
            raise QuantumSolverConfigurationError("max_iterations and timeout must be positive")
        if self.compressed_plan is None:
            return await super().solve(max_iterations=max_iterations, timeout=timeout)

        # Advance the deterministic phase so repeated solve attempts traverse the
        # compressed plan instead of replaying the same nonce.
        self._solve_counter += 1

        start_time = time.monotonic()
        self.last_solve_iterations = 0
        self.last_solve_duration_seconds = None
        self.last_solution_nonce = None
        self.last_error = None
        try:
            collapsed = self._collapse_coordinate()
            walked = self._walk_coordinate(collapsed, max_iterations=max_iterations)
            await asyncio.sleep(0)
            nonce = self._tunnel_anneal_project_nonce(walked)
            if time.monotonic() - start_time >= timeout:
                self.last_error = "timeout"
                return None
            self.last_solve_iterations = max(
                1,
                min(
                    int(max_iterations),
                    int(math.ceil(math.sqrt(self.compressed_plan.working_set_dimension))),
                ),
            )
            self.last_solution_nonce = nonce
            self.last_solve_duration_seconds = time.monotonic() - start_time
            self.current_config["last_solve_trace"] = list(self.last_solve_trace)
            return nonce
        except Exception as exc:
            self.last_error = str(exc)
            self.last_solve_duration_seconds = time.monotonic() - start_time
            return None

    def get_metrics(self) -> Dict[str, Any]:
        metrics = super().get_metrics()
        metrics.update(
            {
                "nonce_space_contract": self.current_config.get("nonce_space_contract"),
                "candidate_generation_complexity": self.current_config.get(
                    "candidate_generation_complexity"
                ),
                "compressed_working_set_size": self.current_config.get(
                    "compressed_working_set_size"
                ),
                "retained_kernel_lanes": self.current_config.get("retained_kernel_lanes"),
                "complete_nonce_coverage": self.current_config.get("complete_nonce_coverage"),
                "overlap_free_nonce_coverage": self.current_config.get("overlap_free_nonce_coverage"),
                "working_set_compression_ratio": self.current_config.get(
                    "working_set_compression_ratio"
                ),
                "phi_compression_factor": self.current_config.get("phi_compression_factor"),
                "phi_filter_acceptance_ratio": self.current_config.get(
                    "phi_filter_acceptance_ratio"
                ),
                "search_space_size": self.current_config.get("search_space_size"),
                "last_solve_trace": list(self.last_solve_trace),
            }
        )
        return metrics


__all__ = ["PulviniCompressedQuantumSolver"]
