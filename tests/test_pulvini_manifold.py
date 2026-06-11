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

from pythia_mining.pulvini_manifold import PulviniManifold, SharedManifoldBlackboard  # noqa: E402
from pythia_mining.pulvini_overlay import ADJACENCY_MAP, PulviniOverlayConcentrator  # noqa: E402
from pythia_mining.pulvini_propagation import SharePropagationController  # noqa: E402
from pythia_mining.stratum_client import ShareResult  # noqa: E402


class PulviniManifoldUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifold = PulviniManifold(ADJACENCY_MAP)

    def test_automorphism_group_and_orbits_are_computed(self) -> None:
        self.assertEqual(120, len(self.manifold.automorphisms))
        self.assertEqual([20, 12], [len(orbit) for orbit in self.manifold.node_orbits])
        sigma = self.manifold.automorphisms[1]
        for source, neighbors in self.manifold.neighbors.items():
            mapped_source = sigma[source]
            mapped_neighbors = {sigma[n] for n in neighbors}
            self.assertEqual(mapped_neighbors, self.manifold.neighbors[mapped_source])

    def test_nonce_orbits_follow_graph_group_action(self) -> None:
        d_orbit = self.manifold.nonce_orbit(2)
        i_orbit = self.manifold.nonce_orbit(31)
        self.assertEqual(20, len(d_orbit))
        self.assertEqual(12, len(i_orbit))
        self.assertTrue(all(value % 32 in self.manifold.node_orbits[0] for value in d_orbit))
        self.assertTrue(all(value % 32 in self.manifold.node_orbits[1] for value in i_orbit))

    def test_hebbian_update_preserves_hermitian_hamiltonian_and_unit_norm(self) -> None:
        before = self.manifold.edge_weight(0, 20)
        self.manifold.hebbian_fire([0, 20, 25, 30, 31], signal_type="SHARE_FOUND")
        self.assertGreater(self.manifold.edge_weight(0, 20), before)
        self.assertAlmostEqual(self.manifold.edge_weight(0, 20), self.manifold.edge_weight(20, 0))
        self.assertTrue(np.allclose(self.manifold.hamiltonian, self.manifold.hamiltonian.conj().T))
        self.manifold.evolve_closed_system(dt=0.25)
        self.assertAlmostEqual(float(np.linalg.norm(self.manifold.psi)), 1.0, places=10)
        self.assertAlmostEqual(float(np.trace(self.manifold.rho).real), 1.0, places=10)
        self.assertTrue(np.allclose(self.manifold.rho, self.manifold.rho.conj().T))

    def test_lindblad_nack_backaction_redistributes_amplitude(self) -> None:
        before = self.manifold.work_distribution().copy()
        event = self.manifold.nack_slice(0, "job-alpha", 0, 100)
        after = self.manifold.work_distribution()
        self.assertEqual("nack_slice_exhausted", event.event_type)
        self.assertLess(after[0], before[0])
        self.assertAlmostEqual(float(np.trace(self.manifold.rho).real), 1.0, places=10)
        self.assertGreaterEqual(float(np.min(np.linalg.eigvalsh(self.manifold.rho).real)), -1e-9)

    def test_threshold_projection_and_phi_projection_are_operational(self) -> None:
        self.assertFalse(self.manifold.collapse_if_threshold(found_node=3, critical_value=10.0))
        self.manifold.entropy_gradient = 10.0
        self.assertTrue(self.manifold.collapse_if_threshold(found_node=3, critical_value=0.1))
        self.assertEqual(3, int(np.argmax(self.manifold.work_distribution())))
        payload = self.manifold.calibrate_phi_projection(range(256), threshold=0.5, job_id="job-beta")
        self.assertEqual(256, payload["sample_size"])
        self.assertGreaterEqual(payload["acceptance_ratio"], 0.0)
        self.assertLessEqual(payload["acceptance_ratio"], 1.0)

    def test_shared_blackboard_exposes_state_vector(self) -> None:
        board = SharedManifoldBlackboard(create=True)
        try:
            self.manifold.attach_blackboard(board)
            observed = board.read_state()
            self.assertTrue(np.allclose(observed, self.manifold.psi))
        finally:
            board.close()
            board.unlink()


class PulviniManifoldIntegrationTests(unittest.TestCase):
    def test_overlay_assignments_include_tensor_coordinates_and_manifold_drift(self) -> None:
        overlay = PulviniOverlayConcentrator()
        job = SimpleNamespace(job_id="job-gamma", target=12345, extranonce2_size=4)
        assignments = overlay.register_pool_job(job, pool_name="Pool")
        self.assertEqual(32, len(assignments))
        self.assertEqual(32, len({assignment.extranonce2 for assignment in assignments.values()}))
        for assignment in assignments.values():
            self.assertIn("orbit_id", assignment.tensor_coordinate)
            self.assertIn("nonce_residue", assignment.tensor_coordinate)
        snapshot = overlay.snapshot()
        self.assertEqual(120, snapshot["manifold"]["automorphism_group"]["order"])
        self.assertEqual("sigma(q*N+r)=q*N+sigma(r)", snapshot["manifold"]["automorphism_group"]["nonce_action"])

    def test_share_propagation_uses_same_manifold_for_route_and_hebbian_update(self) -> None:
        async def run_case() -> dict:
            manifold = PulviniManifold(ADJACENCY_MAP)
            controller = SharePropagationController(manifold)
            job = SimpleNamespace(job_id="job-delta")
            before = manifold.edge_weight(0, 20)

            async def submitter(_job, nonce, extranonce2):
                return ShareResult(True, job_id=_job.job_id, nonce=nonce, block_hash="00" * 32)

            result = await controller.handle_share_found(
                job=job,
                finder_id=0,
                nonce=7,
                extranonce2="00000000",
                submitter=submitter,
            )
            return {
                "route": result.route,
                "cancelled": result.cancelled_nodes,
                "before": before,
                "after": manifold.edge_weight(result.route[0], result.route[1]),
                "history": controller.snapshot()["history"],
            }

        payload = asyncio.run(run_case())
        self.assertEqual(0, payload["route"][0])
        self.assertEqual(31, payload["route"][-1])
        self.assertEqual(32, len(payload["cancelled"]))
        self.assertGreater(payload["after"], payload["before"])
        self.assertEqual(1, len(payload["history"]))


class PulviniManifoldPropertyStyleTests(unittest.TestCase):
    def test_random_like_closed_evolution_preserves_invariants_across_steps(self) -> None:
        manifold = PulviniManifold(ADJACENCY_MAP)
        for index, dt in enumerate([0.01, 0.05, 0.1, 0.25, 0.5]):
            manifold.phase_heartbeat("job-epsilon", index)
            manifold.observe_high_difficulty_hash(index, 0.1 * (index + 1))
            manifold.evolve_closed_system(dt=dt)
            manifold.assert_invariants()

    def test_every_node_has_valid_gradient_route_and_broadcast_covers_all_nodes(self) -> None:
        manifold = PulviniManifold(ADJACENCY_MAP)
        for node_id in range(32):
            route = manifold.gradient_route_to_gateway(node_id)
            self.assertEqual(node_id, route[0])
            self.assertEqual(31, route[-1])
            for left, right in zip(route, route[1:]):
                self.assertIn(right, manifold.neighbors[left])
        self.assertEqual(32, len(manifold.gradient_broadcast_order()))


if __name__ == "__main__":
    unittest.main()
