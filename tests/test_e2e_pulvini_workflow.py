from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.pulvini_certificates import automorphism_runtime_certificate  # noqa: E402
from pythia_mining.pulvini_compressed_solver import PulviniCompressedQuantumSolver  # noqa: E402
from pythia_mining.pulvini_manifold import PulviniManifold  # noqa: E402
from pythia_mining.pulvini_overlay import ADJACENCY_MAP, PulviniOverlayConcentrator  # noqa: E402
from pythia_mining.pulvini_propagation import CancelFlood, PROXY_GATEWAY, SharePropagationController  # noqa: E402
from pythia_mining.stratum_client import MiningJob, ShareResult  # noqa: E402


class PulviniProductionWorkflowTests(unittest.TestCase):
    def test_full_workflow_pool_arrival_to_share_acceptance(self) -> None:
        """
        End-to-end sequence:
        0. Manifold initialised
        1. Pool connection announced
        2. Job arrives
        3. Nonce space compressed
        4. 32 assignments created from compressed plan
        5. Solver configured from tensor coordinates
        6. Nonce found (simulated)
        7. Share signal routed to H31
        8. Pool submission (mocked)
        9. Cancel flood propagated
        10. All nodes confirm job cancelled
        11. Memory fabric updated
        12. Manifold evolved via NZ stepper
        13. Gate certificates checked
        """
        manifold = PulviniManifold(ADJACENCY_MAP)
        self.assertAlmostEqual(np.trace(manifold.rho).real, 1.0, places=6)

        overlay = PulviniOverlayConcentrator(manifold=manifold)
        overlay.mark_pool_bound("test-pool", "stratum+tcp://localhost:3333", 1)
        self.assertEqual(overlay.topology_report["pool_visible_workers"], 1)

        job = MiningJob(
            job_id="test_job_001",
            prevhash="0" * 64,
            coinbase_parts=("00", "ff"),
            merkle_branch=[],
            version="00000001",
            nbits="1d00ffff",
            ntime="deadbeef",
            target=(1 << 256) - 1,
            extranonce2_size=4,
        )

        assignments = overlay.register_pool_job(job, pool_name="test-pool")
        plan = overlay.nonce_plan
        self.assertTrue(plan.complete_coverage)
        self.assertTrue(plan.overlap_free)
        self.assertEqual(plan.coverage_size, 2**32)
        self.assertEqual(plan.working_set_dimension, 20)
        self.assertEqual(plan.retained_kernel_lanes, 12)

        self.assertEqual(len(assignments), 32)
        unique_en2 = {assignment.extranonce2 for assignment in assignments.values()}
        self.assertEqual(len(unique_en2), 32)

        solver = PulviniCompressedQuantumSolver()
        asyncio.run(solver.configure_compressed_search(job.target, plan))
        self.assertEqual(
            solver.current_config["nonce_space_contract"],
            "pulvini_phi_compressed_pre_search",
        )

        test_nonce = plan.solver_ranges[0][0]
        assignment = overlay.assignment_for_nonce(test_nonce)
        self.assertIsNotNone(assignment)
        test_node_id = assignment.node_id

        controller = SharePropagationController(manifold)

        async def submitter(submit_job: MiningJob, nonce: int, extranonce2: str) -> ShareResult:
            return ShareResult(
                accepted=True,
                job_id=submit_job.job_id,
                nonce=nonce,
                block_hash="0" * 64,
                target=submit_job.target,
            )

        result = asyncio.run(
            controller.handle_share_found(
                job=job,
                finder_id=test_node_id,
                nonce=test_nonce,
                extranonce2=assignments[test_node_id].extranonce2,
                submitter=submitter,
                hash_bytes=b"\x00" * 32,
            )
        )
        self.assertEqual(result.route[-1], PROXY_GATEWAY)
        self.assertTrue(result.share_result.accepted)

        cancel_signal = result.cancel_signal
        reached, max_hop = CancelFlood(manifold).flood(cancel_signal)
        self.assertEqual(len(reached), 32)
        self.assertLessEqual(max_hop, 3)

        snapshot = controller.memory_fabric.compressed_kernel_snapshot()
        self.assertIsNotNone(snapshot.kernel)
        self.assertTrue(snapshot.compression["reversible"])

        history = [(manifold.rho.copy(), manifold.synaptic_matrix.copy())]
        rho_evolved = manifold.evolve_production(dt=0.01, history=history)
        self.assertAlmostEqual(np.trace(rho_evolved).real, 1.0, places=5)

        auto_cert = automorphism_runtime_certificate(ADJACENCY_MAP)
        self.assertTrue(auto_cert["gate_closed"])

        bures_result = manifold.bures_gradient_of_collapse_functional(
            rho_evolved, entropy_gradient=0.1
        )
        self.assertIn("bures_gradient_norm", bures_result)

        print("E2E WORKFLOW: PASS")
        print(f"  Route hops: {len(result.route)}")
        print(f"  Cancel reach: {len(reached)}/32 nodes")
        print(f"  Memory kernel norm: {snapshot.kernel["kernel_norm"]:.6f}")
        print(f"  Bures gradient: {bures_result['bures_gradient_norm']:.6f}")
        print(f"  Aut(G) order: {auto_cert['group_order']}")


if __name__ == "__main__":
    unittest.main()
