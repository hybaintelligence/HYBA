"""Solver adapter for pre-search compressed PULVINI nonce plans."""

from __future__ import annotations

from typing import Any

from .quantum_solver import DodecahedralQuantumSolver


class PulviniCompressedQuantumSolver(DodecahedralQuantumSolver):
    """Configure the solver from a compressed nonce plan before search."""

    async def configure_compressed_search(self, target: int, compressed_plan: Any) -> bool:
        await self.configure_search(int(target), list(compressed_plan.solver_ranges))
        self.current_config.update(
            {
                "nonce_space_contract": "pulvini_phi_compressed_pre_search",
                "search_complexity_order": "O(I)",
                "complete_nonce_coverage": bool(compressed_plan.complete_coverage),
                "overlap_free_nonce_coverage": bool(compressed_plan.overlap_free),
                "original_lanes": int(compressed_plan.original_lanes),
                "compressed_working_set_size": int(compressed_plan.working_set_dimension),
                "retained_kernel_lanes": int(compressed_plan.retained_kernel_lanes),
                "working_set_compression_ratio": float(compressed_plan.working_set_compression_ratio),
                "compressed_nonce_plan": compressed_plan.to_dict(),
            }
        )
        return True


__all__ = ["PulviniCompressedQuantumSolver"]
