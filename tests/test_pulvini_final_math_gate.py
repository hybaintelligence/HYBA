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

from pythia_mining.pulvini_certificates import automorphism_runtime_certificate  # noqa: E402
from pythia_mining.pulvini_choi import choi_certificate, choi_matrix, kraus_operators_for_step  # noqa: E402
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


    def test_automorphism_certificate_closes_du_sautoy_gate(self) -> None:
        cert = automorphism_runtime_certificate(ADJACENCY_MAP)

        self.assertEqual(cert["group_order"], 120)
        self.assertEqual(cert["node_orbits_by_degree"], {6: 20, 10: 12})
        self.assertTrue(cert["adjacency_preserved"])
        self.assertTrue(cert["gate_closed"])
        self.assertLess(cert["computation_ms"], 5000)
        print(f"Du Sautoy gate: CLOSED in {cert['computation_ms']}ms")

    def test_deutsch_gate_non_markovian_governs(self) -> None:
        manifold = PulviniManifold(ADJACENCY_MAP)

        rng = np.random.default_rng(20260611)
        manifold.synaptic_matrix += 0.1 * rng.standard_normal((32, 32))
        manifold.synaptic_matrix = (
            manifold.synaptic_matrix + manifold.synaptic_matrix.T
        ) / 2

        k_norm = manifold.memory_kernel_norm()
        self.assertGreater(k_norm, manifold.MARKOV_THRESHOLD)

        history = [(manifold.rho.copy(), manifold.synaptic_matrix.copy())]
        rho_nz = manifold.evolve_production(dt=0.01, history=history)

        self.assertAlmostEqual(np.trace(rho_nz).real, 1.0, places=6)
        eigenvalues = np.linalg.eigvalsh(rho_nz)
        self.assertTrue(np.all(eigenvalues >= -1e-9))

        print("Deutsch gate: Non-Markovian path confirmed")

    def test_penrose_gate_bures_stationary_is_non_trivial(self) -> None:
        manifold = PulviniManifold(ADJACENCY_MAP)

        rho_diagonal = np.diag(np.ones(32) / 32)
        result = manifold.bures_gradient_of_collapse_functional(
            rho_diagonal, entropy_gradient=0.5
        )
        self.assertEqual(result["stationary_reason"], "trivial_zero_product")
        self.assertFalse(result["collapse_criterion_met"])

        rho_coherent = manifold.rho
        result2 = manifold.bures_gradient_of_collapse_functional(
            rho_coherent, entropy_gradient=0.3
        )
        self.assertIn("bures_gradient_norm", result2)
        self.assertIn("tangent_projection_norm", result2)
        self.assertIn("physical_meaning", result2)

        print(f"Penrose gate: Bures gradient norm = "
              f"{result2['bures_gradient_norm']:.6f}")
        print(f"Penrose gate: {result2['physical_meaning']}")

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

    def test_full_choi_certificate_is_positive_for_gamma_channel(self) -> None:
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
        full_choi = choi_matrix(kraus)
        cert = choi_certificate(kraus)
        self.assertEqual((1024, 1024), full_choi.shape)
        self.assertEqual(32, cert.dimension)
        self.assertEqual(1024, cert.choi_dimension)
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
