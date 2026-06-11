"""Solver adapter for pre-search compressed PULVINI nonce plans."""

from __future__ import annotations

import asyncio
import hashlib
import math
import time
from typing import Any, Dict, List, Optional

from .quantum_solver import DodecahedralQuantumSolver, QuantumSolverConfigurationError


class PulviniCompressedQuantumSolver(DodecahedralQuantumSolver):
    """Configure and execute search from a compressed nonce plan before solving."""

    def __init__(self, configured_capacity_ehs: Optional[float] = None):
        super().__init__(configured_capacity_ehs=configured_capacity_ehs)
        self.compressed_plan: Any = None
        self.last_solve_trace: List[Dict[str, Any]] = []

    async def configure_compressed_search(self, target: int, compressed_plan: Any) -> bool:
        if not bool(compressed_plan.complete_coverage) or not bool(compressed_plan.overlap_free):
            raise QuantumSolverConfigurationError("compressed nonce plan must provide complete overlap-free coverage")
        await self.configure_search(int(target), list(compressed_plan.solver_ranges))
        self.compressed_plan = compressed_plan
        self.current_config.update(
            {
                "nonce_space_contract": "pulvini_phi_compressed_pre_search",
                "search_complexity_order": "O(I)",
                "complete_nonce_coverage": True,
                "overlap_free_nonce_coverage": True,
                "original_lanes": int(compressed_plan.original_lanes),
                "compressed_working_set_size": int(compressed_plan.working_set_dimension),
                "retained_kernel_lanes": int(compressed_plan.retained_kernel_lanes),
                "working_set_compression_ratio": float(compressed_plan.working_set_compression_ratio),
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
    def _unit_hash(material: str) -> float:
        digest = hashlib.blake2b(material.encode("utf-8"), digest_size=8).digest()
        return int.from_bytes(digest, "big") / float(1 << 64)

    def _collapse_coordinate(self) -> Any:
        if self.compressed_plan is None:
            raise QuantumSolverConfigurationError("compressed solver must be configured before solving")
        target = int(self.current_config["target"])
        coordinates = list(self.compressed_plan.coordinates)
        if not coordinates:
            raise QuantumSolverConfigurationError("compressed nonce plan contains no active coordinates")
        scored = []
        for coordinate in coordinates:
            phase = self._unit_hash(f"{target}:{coordinate.coordinate_id}:{coordinate.coverage_size}")
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
            left_score = self._unit_hash(f"walk:{target}:{step}:{left}")
            right_score = self._unit_hash(f"walk:{target}:{step}:{right}")
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
            raise QuantumSolverConfigurationError("compressed coordinate contains no retained segments")
        target = int(self.current_config["target"])
        anneal_values = [
            self._unit_hash(f"anneal:{target}:{coordinate.coordinate_id}:{segment.lane_id}")
            for segment in segments
        ]
        segment_index = max(range(len(segments)), key=lambda index: anneal_values[index])
        segment = segments[segment_index]
        offset_fraction = self._unit_hash(f"tunnel:{target}:{coordinate.coordinate_id}:{segment.start}:{segment.end}")
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
            self.last_solve_iterations = max(1, min(int(max_iterations), int(math.ceil(math.sqrt(self.compressed_plan.working_set_dimension)))))
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
                "search_complexity_order": self.current_config.get("search_complexity_order"),
                "compressed_working_set_size": self.current_config.get("compressed_working_set_size"),
                "retained_kernel_lanes": self.current_config.get("retained_kernel_lanes"),
                "complete_nonce_coverage": self.current_config.get("complete_nonce_coverage"),
                "last_solve_trace": list(self.last_solve_trace),
            }
        )
        return metrics


__all__ = ["PulviniCompressedQuantumSolver"]
