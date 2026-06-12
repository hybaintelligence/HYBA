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

from pythia_mining.pulvini_bures import bures_certificate  # noqa: E402
from pythia_mining.pulvini_compressed_solver import PulviniCompressedQuantumSolver  # noqa: E402
from pythia_mining.pulvini_overlay import PulviniOverlayConcentrator  # noqa: E402
from pythia_mining.pulvini_propagation import SharePropagationController  # noqa: E402
from pythia_mining.stratum_client import MiningJob, ShareResult  # noqa: E402


class PulviniEndToEndShareFlowTests(unittest.TestCase):
    def test_job_to_compressed_search_to_accepted_share(self) -> None:
        async def run() -> None:
            overlay = PulviniOverlayConcentrator(worker_name="PULVINI.singularity")
            propagation = SharePropagationController(overlay.manifold)
            solver = PulviniCompressedQuantumSolver()
            submitted = []
            job = MiningJob(
                job_id="job-e2e",
                prevhash="00" * 32,
                coinbase_parts=("aa", "bb"),
                merkle_branch=[],
                version="20000000",
                nbits="1d00ffff",
                ntime="5e9a5c00",
                target=1,
                extranonce1="abcd",
                extranonce2_size=4,
            )

            async def submitter(submit_job: MiningJob, nonce: int, extranonce2: str) -> ShareResult:
                submitted.append((submit_job.job_id, nonce, extranonce2))
                return ShareResult(True, job_id=submit_job.job_id, nonce=nonce, block_hash="00" * 32, target=submit_job.target)

            assignments = overlay.register_pool_job(job, pool_name="Pool")
            plan = overlay.nonce_plan
            self.assertEqual(32, len(assignments))
            self.assertTrue(plan.complete_coverage)
            self.assertTrue(plan.overlap_free)
            self.assertEqual(20, plan.working_set_dimension)
            self.assertEqual(12, plan.retained_kernel_lanes)

            cert = bures_certificate(overlay.manifold.rho, overlay.manifold.entropy_gradient)
            self.assertTrue(cert.closed)
            self.assertEqual("Bures", cert.metric)
            # Numerical validity assertions for Bures certificate
            self.assertFalse(np.isnan(cert.bures_norm), "NaN in Bures norm — numerical corruption")
            self.assertFalse(np.isinf(cert.bures_norm), "Inf in Bures norm — overflow")
            self.assertFalse(np.isnan(cert.tangent_norm), "NaN in tangent norm — numerical corruption")
            self.assertFalse(np.isinf(cert.tangent_norm), "Inf in tangent norm — overflow")

            overlay.phase_heartbeat(1)
            overlay.manifold.evolve_closed_system(dt=0.05)
            # Numerical validity assertions for evolved state
            self.assertFalse(np.any(np.isnan(overlay.manifold.psi)), "NaN in evolved state vector — numerical corruption")
            self.assertFalse(np.any(np.isinf(overlay.manifold.psi)), "Inf in evolved state vector — overflow")
            self.assertFalse(np.any(np.isnan(overlay.manifold.rho)), "NaN in evolved density matrix — numerical corruption")
            self.assertFalse(np.any(np.isinf(overlay.manifold.rho)), "Inf in evolved density matrix — overflow")
            await solver.configure_compressed_search(job.target, plan)
            nonce = await solver.solve(max_iterations=16, timeout=5.0)
            self.assertIsNotNone(nonce)
            assert nonce is not None
            assignment = overlay.assignment_for_nonce(nonce)
            self.assertIsNotNone(assignment)
            assert assignment is not None
            compressed_coordinate = overlay.compressed_coordinate_for_nonce(nonce)
            self.assertIsNotNone(compressed_coordinate)

            overlay.record_share_candidate(assignment.node_id, nonce)
            propagation_result = await propagation.handle_share_found(
                job=job,
                finder_id=assignment.node_id,
                nonce=nonce,
                extranonce2=assignment.extranonce2,
                submitter=submitter,
            )
            ledger = overlay.record_share_outcome(assignment.node_id, nonce, propagation_result.share_result)
            snapshot = overlay.snapshot()
            propagation_snapshot = propagation.snapshot()

            self.assertEqual(1, len(submitted))
            self.assertTrue(propagation_result.share_result.accepted)
            self.assertTrue(propagation.is_job_cancelled(job.job_id))
            self.assertEqual(32, len(propagation_result.cancelled_nodes))
            self.assertEqual(nonce, submitted[0][1])
            self.assertEqual(assignment.extranonce2, submitted[0][2])
            self.assertEqual("job-e2e", snapshot["active_job_id"])
            self.assertEqual(1, snapshot["pool_visible_workers"])
            self.assertEqual(32, snapshot["internal_nodes"])
            self.assertTrue(snapshot["nonce_compression_plan"]["complete_coverage"])
            self.assertEqual(20, snapshot["nonce_compression_plan"]["working_set_dimension"])
            self.assertTrue(ledger["accepted"])
            self.assertIsNotNone(ledger["compressed_coordinate"])
            self.assertEqual("O(1) deterministic per attempt, O(D/2^256) expected attempts to block", solver.current_config["candidate_generation_complexity"])
            stages = [entry["stage"] for entry in solver.last_solve_trace]
            self.assertIn("compressed_nonce_space_received", stages)
            self.assertIn("search_space_collapsed", stages)
            self.assertIn("quantum_walk_completed", stages)
            self.assertIn("tunnel_anneal_projected_nonce", stages)
            self.assertGreater(propagation_snapshot["memory_fabric"]["kernel"]["kernel_norm"], 0.0)
            phases = [event["phase"] for event in snapshot["lifecycle"]]
            self.assertIn("job_received", phases)
            self.assertIn("work_configured", phases)
            self.assertIn("candidate_evaluated", phases)
            self.assertIn("share_submitted", phases)
            self.assertIn("share_outcome_recorded", phases)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
