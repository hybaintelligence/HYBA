from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Turn warnings into hard failures in test context
np.seterr(all="raise")

from pythia_mining.pulvini_compressed_solver import PulviniCompressedQuantumSolver  # noqa: E402
from pythia_mining.pulvini_nonce_compression import (  # noqa: E402
    NONCE_SPACE_SIZE,
    PulviniNonceSpaceCompressor,
)
from pythia_mining.pulvini_overlay import NUM_NODES, PulviniOverlayConcentrator  # noqa: E402


class PulviniNonceCompressionTests(unittest.TestCase):
    def test_phi_plan_compresses_working_set_and_keeps_full_coverage(self) -> None:
        plan = PulviniNonceSpaceCompressor().build_plan()

        self.assertEqual(NUM_NODES, plan.original_lanes)
        self.assertLess(plan.working_set_dimension, plan.original_lanes)
        self.assertEqual(20, plan.working_set_dimension)
        self.assertEqual(12, plan.retained_kernel_lanes)
        self.assertTrue(plan.complete_coverage)
        self.assertTrue(plan.overlap_free)
        self.assertEqual(NONCE_SPACE_SIZE, plan.coverage_size)
        self.assertEqual(32, len(plan.coverage_segments))
        self.assertEqual(20, len(plan.coordinates))

        covered = sum(segment.size for segment in plan.coverage_segments)
        self.assertEqual(NONCE_SPACE_SIZE, covered)
        for index in range(1, len(plan.coverage_segments)):
            self.assertEqual(
                plan.coverage_segments[index - 1].end + 1,
                plan.coverage_segments[index].start,
            )

    def test_compressed_coordinate_maps_nonce_to_retained_segments(self) -> None:
        plan = PulviniNonceSpaceCompressor().build_plan()
        first = plan.coordinate_for_nonce(0)
        last = plan.coordinate_for_nonce(NONCE_SPACE_SIZE - 1)

        self.assertIsNotNone(first)
        self.assertIsNotNone(last)
        assert first is not None
        assert last is not None
        self.assertEqual(0, first.coordinate_id)
        self.assertEqual(11, last.coordinate_id)
        self.assertGreater(first.coverage_size, plan.coverage_segments[0].size)
        self.assertGreater(last.coverage_size, plan.coverage_segments[-1].size)

    def test_overlay_assigns_from_compressed_nonce_plan(self) -> None:
        overlay = PulviniOverlayConcentrator()
        job = SimpleNamespace(job_id="job-compressed", target=1, extranonce2_size=4)
        overlay.register_pool_job(job, pool_name="Pool")
        snapshot = overlay.snapshot()
        plan = snapshot["nonce_compression_plan"]

        self.assertTrue(plan["complete_coverage"])
        self.assertTrue(plan["overlap_free"])
        self.assertEqual(20, plan["working_set_dimension"])
        self.assertEqual(12, plan["retained_kernel_lanes"])
        self.assertEqual(NONCE_SPACE_SIZE, plan["coverage_size"])
        self.assertEqual(32, len(snapshot["assignments"]))
        self.assertIn("compressed_coordinate", snapshot["assignments"][0])
        phases = [event["phase"] for event in snapshot["lifecycle"]]
        self.assertIn("work_configured", phases)

    def test_solver_is_configured_from_compressed_plan_before_search(self) -> None:
        async def run() -> None:
            plan = PulviniNonceSpaceCompressor().build_plan()
            solver = PulviniCompressedQuantumSolver()
            await solver.configure_compressed_search(1, plan)
            self.assertEqual(
                "O(1) deterministic per attempt, O(D/2^256) expected attempts to block",
                solver.current_config["candidate_generation_complexity"],
            )
            self.assertTrue(solver.current_config["complete_nonce_coverage"])
            self.assertTrue(solver.current_config["overlap_free_nonce_coverage"])
            self.assertEqual(20, solver.current_config["compressed_working_set_size"])
            self.assertEqual(12, solver.current_config["retained_kernel_lanes"])
            self.assertEqual(NONCE_SPACE_SIZE, solver.current_config["search_space_size"])

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
