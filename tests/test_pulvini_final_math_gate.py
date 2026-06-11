from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.pulvini_choi import choi_certificate, kraus_operators_for_step  # noqa: E402
from pythia_mining.pulvini_gamma import EmpiricalGammaLedger, jump_operators_from_gamma  # noqa: E402
from pythia_mining.pulvini_group import adjacency_sets, compute_graph_automorphisms, compute_node_orbits  # noqa: E402
from pythia_mining.pulvini_manifold import PulviniManifold  # noqa: E402
from pythia_mining.pulvini_overlay import ADJACENCY_MAP  # noqa: E402
from pythia_mining.pulvini_variational import trace_zero_hermitian_projection, variational_certificate  # noqa: E402


class PulviniFinalMathGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifold = PulviniManifold(ADJACENCY_MAP)

    def test_variational_certificate_is_not_falsely_closed(self) -> None:
        self.manifold.entropy_gradient = 0.75
        cert = variational_certificate(self.manifold.rho, self.manifold.entropy_gradient)
        self.assertIn("candidate", cert.functional)
        self.assertIn("trace-zero", cert.tangent_space)
        self.assertGreater(cert.control_energy, 0.0)
        self.assertGreater(cert.tangent_gradient_norm, 0.0)
        self.assertFalse(cert.closed)
        self.assertIn("no proof", cert.blocker)
        self.assertIn("Bures", cert.required_derivation)

    def test_trace_zero_hermitian_projection_stays_on_density_tangent_space(self) -> None:
        raw = np.zeros((32, 32), dtype=np.complex128)
        raw[0, 1] = 1.0 + 2.0j
        raw[2, 2] = 7.0
        projected = trace_zero_hermitian_projection(raw)
        self.assertTrue(np.allclose(projected, projected.conj().T))
        self.assertAlmostEqual(float(np.trace(projected).real), 0.0, places=10)

    def test_empirical_gamma_controls_jump_strength(self) -> None:
        ledger = EmpiricalGammaLedger(num_nodes=32, alpha_prior=1.0, beta_prior=31.0)
        before = ledger.estimate(0).gamma
        for _ in range(8):
            ledger.record(0, nack=True)
        after = ledger.estimate(0).gamma
        self.assertGreater(after, before)

        jumps = jump_operators_from_gamma(
            node_id=0,
            neighbors=self.manifold.neighbors,
            gamma=after,
            num_nodes=32,
        )
        self.assertEqual(len(self.manifold.neighbors[0]), len(jumps))
        self.assertGreater(sum(float(np.linalg.norm(op)) for op in jumps), 0.0)

    def test_choi_certificate_is_positive_for_gamma_channel(self) -> None:
        ledger = EmpiricalGammaLedger(num_nodes=32)
        for _ in range(4):
            ledger.record(0, nack=True)
        gamma = ledger.estimate(0).gamma
        jumps = jump_operators_from_gamma(
            node_id=0,
            neighbors=self.manifold.neighbors,
            gamma=gamma,
            num_nodes=32,
        )
        kraus = kraus_operators_for_step(self.manifold.hamiltonian, jumps, dt=1.0)
        cert = choi_certificate(kraus)
        self.assertTrue(cert.positive_semidefinite)
        self.assertGreaterEqual(cert.min_eigenvalue, -1e-9)
        self.assertLess(cert.trace_preservation_error, 1e-8)

    def test_automorphism_order_is_computed_from_runtime_adjacency_map_with_timing(self) -> None:
        neighbors = adjacency_sets(ADJACENCY_MAP)
        started = time.perf_counter()
        automorphisms = compute_graph_automorphisms(ADJACENCY_MAP)
        elapsed = time.perf_counter() - started
        orbits = compute_node_orbits(len(ADJACENCY_MAP), automorphisms)
        degree_histogram: dict[int, int] = {}
        for node_neighbors in neighbors.values():
            degree_histogram[len(node_neighbors)] = degree_histogram.get(len(node_neighbors), 0) + 1

        self.assertEqual(120, len(automorphisms))
        self.assertLess(elapsed, 1.0)
        self.assertEqual([20, 12], [len(orbit) for orbit in orbits])
        self.assertEqual({6: 20, 10: 12}, degree_histogram)
        for sigma in automorphisms:
            for source, source_neighbors in neighbors.items():
                mapped_neighbors = {sigma[neighbor] for neighbor in source_neighbors}
                self.assertEqual(mapped_neighbors, neighbors[sigma[source]])


if __name__ == "__main__":
    unittest.main()
