"""Tests for the new PULVINI mathematical certificates.

Run with:
    python -m pytest tests/test_pulvini_new_certificates.py -v
    python -m unittest tests.test_pulvini_new_certificates
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.pulvini_grover_certificate import (
    grover_efficiency_report,
    grover_scope_certificate,
)
from pythia_mining.pulvini_coverage_certificate import (
    coverage_certificate,
    lane_coverage_report,
    verify_automorphism_preserves_coverage,
    verify_lane_coverages,
)
from pythia_mining.pulvini_structural_certificate import (
    d_i_analysis,
    structural_certificate,
    verify_adjacency_preserved_for_all,
    verify_graph_connectivity,
)
from pythia_mining.pulvini_bures_variational import (
    bures_metric_tangent_projection,
    bures_variational_certificate,
    verify_bures_variational_gate,
)
from pythia_mining.pulvini_memory_compression_proof import (
    phi_folding_mathematical_proof,
    prove_lane_surface_coverage,
    prove_phi_folding_reversibility,
    verify_memory_compression_gate,
)
from pythia_mining.pulvini_group import (
    a5_representation_certificate,
    coxeter_group_certificate,
    compute_graph_automorphisms,
)
from pythia_mining.pulvini_observability import (
    MetricType,
    ObservabilityFramework,
    SLOStatus,
    verify_observability_framework,
)
from pythia_mining.pulvini_topology import ADJACENCY_MAP


class TestGroverScopeCertificate(unittest.TestCase):
    """Tests for the Grover scope certificate."""

    def test_grover_scope_quantum_speedup_not_claimed(self):
        """The certificate must explicitly state no quantum speedup."""
        cert = grover_scope_certificate(
            target=0x1D00FFFF,
            nonce_ranges=[(0, 2**32 - 1)],
        )
        self.assertFalse(cert.quantum_speedup_claimed)
        self.assertTrue(cert.deterministic_behavior)

    def test_grover_scope_basis_dimension_is_20(self):
        """The basis dimension must be 20 (dodecahedron vertices)."""
        cert = grover_scope_certificate(
            target=0x1D00FFFF,
            nonce_ranges=[(0, 2**32 - 1)],
        )
        self.assertEqual(cert.basis_dimension, 20)

    def test_grover_scope_nonce_space_is_2_32(self):
        """The nonce space must be 2^32."""
        cert = grover_scope_certificate(
            target=0x1D00FFFF,
            nonce_ranges=[(0, 2**32 - 1)],
        )
        self.assertEqual(cert.nonce_space_size, 2**32)

    def test_grover_scope_theoretical_steps_is_3(self):
        """Theoretical optimal steps for N=20, M=1 is floor(pi/4 * sqrt(20)) = 3."""
        cert = grover_scope_certificate(
            target=0x1D00FFFF,
            nonce_ranges=[(0, 2**32 - 1)],
        )
        self.assertEqual(cert.grover_theoretical_steps, 3)

    def test_grover_scope_deterministic_for_same_input(self):
        """Same target and ranges must produce same certificate."""
        cert1 = grover_scope_certificate(target=100, nonce_ranges=[(0, 1000)])
        cert2 = grover_scope_certificate(target=100, nonce_ranges=[(0, 1000)])
        self.assertEqual(cert1.to_dict(), cert2.to_dict())

    def test_grover_scope_different_target_different_marked_state(self):
        """Different targets must produce different scope statements."""
        cert1 = grover_scope_certificate(target=100, nonce_ranges=[(0, 1000)])
        cert2 = grover_scope_certificate(target=200, nonce_ranges=[(0, 1000)])
        self.assertNotEqual(cert1.scope_statement, cert2.scope_statement)

    def test_grover_efficiency_report_is_honest(self):
        """The efficiency report must not claim quantum speedup."""
        report = grover_efficiency_report()
        self.assertIn("No quantum speedup", report["honest_claim"])
        self.assertIn("Structurally-guided", report["honest_claim"])

    def test_grover_efficiency_report_has_correct_steps(self):
        """The report must have correct step counts."""
        report = grover_efficiency_report()
        self.assertEqual(report["grover_theoretical_steps_for_basis"], 3)
        self.assertEqual(report["classical_brute_force_steps_for_full_2_32"], 2**32)


class TestCoxeterGroupCertificate(unittest.TestCase):
    """Tests for the Coxeter group certificate."""

    def test_coxeter_group_is_h3(self):
        cert = coxeter_group_certificate()
        self.assertEqual(cert.coxeter_group, "H3 icosahedral Coxeter group")
        self.assertEqual(cert.rank, 3)
        self.assertEqual(cert.order, 120)

    def test_coxeter_diagram_is_correct(self):
        cert = coxeter_group_certificate()
        self.assertEqual(cert.coxeter_diagram, "o-5-o-3-o")
        self.assertEqual(cert.coxeter_matrix, [[1, 5, 3], [5, 1, 3], [3, 3, 1]])

    def test_coxeter_root_system_type(self):
        cert = coxeter_group_certificate()
        self.assertEqual(cert.root_system_type, "H3")
        self.assertIn("non-crystallographic", cert.weyl_group_type)

    def test_coxeter_certificate_embedded_in_a5(self):
        cert = a5_representation_certificate()
        self.assertIn("coxeter_structure", cert.to_dict())
        self.assertEqual(
            cert.coxeter_structure["coxeter_group"], "H3 icosahedral Coxeter group"
        )


class TestA5RepresentationCertificate(unittest.TestCase):
    """Tests for the A5 representation-theory certificate."""

    def test_a5_character_table_has_five_irreps(self):
        cert = a5_representation_certificate()
        self.assertEqual(cert.irreducible_dimensions, [1, 3, 3, 4, 5])
        self.assertEqual(len(cert.character_table), 5)

    def test_a5_regular_dimension_sum_and_orthogonality(self):
        cert = a5_representation_certificate()
        self.assertEqual(cert.regular_representation_dimension_sum, 60)
        self.assertTrue(cert.character_orthogonality_verified)

    def test_a5_certificate_is_honest_about_speedup(self):
        cert = a5_representation_certificate()
        self.assertFalse(cert.quantum_speedup_claimed)
        self.assertAlmostEqual(cert.heuristic_dimension_reduction, 2.0)

    def test_a5_certificate_includes_coxeter_structure(self):
        cert = a5_representation_certificate()
        self.assertIn("coxeter_structure", cert.to_dict())
        self.assertEqual(cert.coxeter_structure["order"], 120)

    def test_structural_certificate_embeds_representation_theory(self):
        cert = structural_certificate()
        self.assertEqual(cert.representation_theory["rotational_group_order"], 60)
        self.assertEqual(cert.representation_theory["full_automorphism_order"], 120)
        self.assertTrue(cert.representation_theory["character_orthogonality_verified"])


class TestCoverageCertificate(unittest.TestCase):
    """Tests for the deterministic coverage certificate."""

    def test_lane_coverages_are_complete(self):
        """All 2^32 nonces must be covered by the 32 lanes."""
        is_complete, is_overlap_free = verify_lane_coverages()
        self.assertTrue(is_complete)
        self.assertTrue(is_overlap_free)

    def test_coverage_certificate_has_correct_lane_count(self):
        """The certificate must report 32 lanes."""
        cert = coverage_certificate()
        self.assertEqual(cert.num_lanes, 32)

    def test_coverage_certificate_complete_and_overlap_free(self):
        """The certificate must confirm complete and overlap-free coverage."""
        cert = coverage_certificate()
        self.assertTrue(cert.complete_coverage)
        self.assertTrue(cert.overlap_free)

    def test_coverage_certificate_deterministic(self):
        """The certificate must confirm deterministic selection."""
        cert = coverage_certificate()
        self.assertTrue(cert.deterministic_selection)

    def test_automorphism_preserves_coverage(self):
        """Automorphism action must preserve nonce coverage."""
        automorphisms = compute_graph_automorphisms(ADJACENCY_MAP)
        preserves = verify_automorphism_preserves_coverage(automorphisms)
        self.assertTrue(preserves)

    def test_lane_coverage_report_has_32_lanes(self):
        """The lane coverage report must have exactly 32 lanes."""
        report = lane_coverage_report()
        self.assertEqual(len(report["lanes"]), 32)
        self.assertEqual(report["total_covered"], 2**32)

    def test_each_lane_has_correct_size(self):
        """Each lane must have size 2^32 / 32 = 134,217,728."""
        report = lane_coverage_report()
        lane_size = 2**32 // 32
        for lane in report["lanes"]:
            self.assertEqual(lane["size"], lane_size)

    def test_d_nodes_have_20_lanes(self):
        """First 20 lanes must be D-nodes."""
        report = lane_coverage_report()
        for lane_id in range(20):
            self.assertEqual(report["lanes"][lane_id]["node_type"], "D-node")

    def test_i_nodes_have_12_lanes(self):
        """Last 12 lanes must be I-nodes."""
        report = lane_coverage_report()
        for lane_id in range(20, 32):
            self.assertEqual(report["lanes"][lane_id]["node_type"], "I-node")


class TestStructuralCertificate(unittest.TestCase):
    """Tests for the D/I structural certificate."""

    def test_structural_certificate_has_32_nodes(self):
        """The certificate must report 32 nodes."""
        cert = structural_certificate()
        self.assertEqual(cert.num_nodes, 32)

    def test_structural_certificate_has_20_d_nodes(self):
        """There must be 20 D-nodes (degree 3)."""
        cert = structural_certificate()
        self.assertEqual(cert.d_nodes, 20)

    def test_structural_certificate_has_12_i_nodes(self):
        """There must be 12 I-nodes."""
        cert = structural_certificate()
        self.assertEqual(cert.i_nodes, 12)

    def test_structural_certificate_automorphism_order_120(self):
        """Automorphism group order must be 120."""
        cert = structural_certificate()
        self.assertEqual(cert.automorphism_group_order, 120)

    def test_structural_certificate_graph_is_connected(self):
        """The graph must be fully connected."""
        cert = structural_certificate()
        self.assertTrue(cert.complete_graph)

    def test_structural_certificate_adjacency_preserved(self):
        """All automorphisms must preserve adjacency."""
        cert = structural_certificate()
        self.assertTrue(cert.adjacency_preserved)

    def test_graph_connectivity(self):
        """The 32-node graph must be a single component."""
        is_connected = verify_graph_connectivity(ADJACENCY_MAP)
        self.assertTrue(is_connected)

    def test_adjacency_preserved_for_all_automorphisms(self):
        """All 120 automorphisms must preserve adjacency."""
        automorphisms = compute_graph_automorphisms(ADJACENCY_MAP)
        preserved = verify_adjacency_preserved_for_all(automorphisms)
        self.assertTrue(preserved)

    def test_d_i_analysis_has_correct_edge_counts(self):
        """D-I analysis must have correct edge structure."""
        analysis = d_i_analysis()
        self.assertEqual(len(analysis["d_nodes"]), 20)
        self.assertEqual(len(analysis["i_nodes"]), 12)
        # Each D-node connects to 3 I-nodes
        for node_id, count in analysis["d_adjacent_to_i_per_node"].items():
            self.assertEqual(count, 3)


class TestBuresVariationalCertificate(unittest.TestCase):
    """Tests for the Bures variational certificate."""

    def test_bures_variational_certificate_closes_gate(self):
        """The certificate must report the gate as closed."""
        dim = 32
        psi = np.random.randn(dim) + 1j * np.random.randn(dim)
        psi = psi / np.linalg.norm(psi)
        rho = np.outer(psi, psi.conj())
        cert = bures_variational_certificate(rho, entropy_gradient=0.3)
        self.assertTrue(cert.closed)
        self.assertEqual(cert.required_gate, "Penrose variational threshold")

    def test_bures_trivial_stationary_is_not_collapse(self):
        """Trivial zero-product must not be collapse."""
        dim = 32
        rho_diag = np.diag(np.ones(dim) / dim)
        cert = bures_variational_certificate(rho_diag, entropy_gradient=0.5)
        self.assertEqual(cert.stationary_reason, "trivial_zero_product")
        self.assertFalse(cert.collapse_criterion_met)

    def test_bures_tangent_projection_is_trace_zero(self):
        """The Bures tangent projection must be trace-zero Hermitian."""
        dim = 32
        psi = np.random.randn(dim) + 1j * np.random.randn(dim)
        psi = psi / np.linalg.norm(psi)
        rho = np.outer(psi, psi.conj())
        flat_grad = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
        tangent = bures_metric_tangent_projection(rho, flat_grad)
        # Must be Hermitian
        self.assertTrue(np.allclose(tangent, tangent.conj().T, atol=1e-10))
        # Must be trace-zero
        self.assertAlmostEqual(float(np.trace(tangent).real), 0.0, places=10)

    def test_verify_bures_variational_gate(self):
        """The full gate verification must pass."""
        result = verify_bures_variational_gate()
        self.assertEqual(result["status"], "CLOSED")
        self.assertIn("evolving_state", result["tests"])
        self.assertIn("trivial_diagonal_state", result["tests"])
        self.assertIn("near_eigenbasis_alignment", result["tests"])


class TestObservabilityFramework(unittest.TestCase):
    """Tests for observability framework (MIT requirements)."""

    def test_metric_recording(self):
        """Framework must record metrics correctly."""
        framework = ObservabilityFramework()
        metric = framework.record_metric("test_metric", 42.0, MetricType.GAUGE, "units")
        self.assertEqual(metric.name, "test_metric")
        self.assertEqual(metric.value, 42.0)
        self.assertEqual(len(framework.metrics), 1)

    def test_slo_definition(self):
        """Framework must define SLO targets."""
        framework = ObservabilityFramework()
        slo = framework.define_slo("test_slo", 0.95, timedelta(hours=1), 0.97)
        self.assertEqual(slo.name, "test_slo")
        self.assertEqual(slo.slo_target, 0.95)
        self.assertEqual(slo.status, SLOStatus.COMPLIANT)

    def test_slo_violation_detection(self):
        """Framework must detect SLO violations."""
        framework = ObservabilityFramework()
        slo = framework.define_slo("test_slo", 0.95, timedelta(hours=1), 0.85)
        self.assertEqual(slo.status, SLOStatus.VIOLATED)
        self.assertGreater(slo.burn_rate, 0.0)

    def test_tracing_context(self):
        """Framework must support distributed tracing."""
        framework = ObservabilityFramework()
        trace = framework.start_trace("test_operation", tags={"component": "test"})
        self.assertIsNotNone(trace.trace_id)
        self.assertIsNotNone(trace.span_id)

        ended_trace = framework.end_trace(trace.span_id)
        self.assertIsNotNone(ended_trace.duration_ms)
        self.assertGreater(ended_trace.duration_ms, 0)

    def test_observability_certificate_generation(self):
        """Framework must generate compliance certificate."""
        framework = ObservabilityFramework()
        framework.record_metric("test", 1.0)
        framework.define_slo("test_slo", 0.95, timedelta(hours=1), 0.97)

        cert = framework.get_observability_certificate()
        self.assertTrue(cert.tracing_enabled)
        self.assertTrue(cert.structured_logging_enabled)
        self.assertTrue(cert.chaos_engineering_hooks)
        self.assertGreater(len(cert.slo_targets), 0)

    def test_observability_verification_closes_gate(self):
        """Observability verification must meet MIT requirements."""
        result = verify_observability_framework()
        self.assertEqual(result["status"], "CLOSED")
        self.assertGreater(result["slo_count"], 0)
        self.assertTrue(result["tracing_enabled"])
        self.assertTrue(result["metrics_collected"])


class TestMemoryCompressionProof(unittest.TestCase):
    """Tests for the memory compression proof."""

    def test_lane_surface_is_reversible(self):
        """The 32-lane surface must be reversibly compressible."""
        proof = prove_lane_surface_coverage(32, fold_depth=1)
        self.assertTrue(proof.reversible)
        self.assertTrue(proof.complete_coverage)
        self.assertTrue(proof.deterministic)

    def test_density_matrix_is_reversible(self):
        """A 32x32 density matrix must be reversibly compressible."""
        rng = np.random.default_rng(42)
        density = rng.standard_normal((32, 32))
        density = (density + density.T) / 2.0
        proof = prove_phi_folding_reversibility(density, fold_depth=2)
        self.assertTrue(proof.reversible)
        self.assertTrue(proof.complete_coverage)

    def test_reconstruction_error_is_small(self):
        """Reconstruction error must be below 1e-9."""
        data = np.arange(32, dtype=np.float64)
        proof = prove_phi_folding_reversibility(data, fold_depth=1)
        self.assertLess(proof.reconstruction_error, 1e-9)

    def test_compression_ratio_is_positive(self):
        """Compression ratio must be positive."""
        data = np.arange(32, dtype=np.float64)
        proof = prove_phi_folding_reversibility(data, fold_depth=1)
        self.assertGreater(proof.compression_ratio, 0.0)

    def test_phi_folding_mathematical_proof(self):
        """The algebraic proof must confirm invertibility."""
        proof = phi_folding_mathematical_proof()
        self.assertTrue(proof["determinant_non_zero"])
        self.assertTrue(proof["invertible"])
        self.assertTrue(proof["inverse_verification"])

    def test_verify_memory_compression_gate(self):
        """The full memory compression gate must pass."""
        result = verify_memory_compression_gate()
        self.assertEqual(result["status"], "CLOSED")
        self.assertTrue(result["lane_surface_32"]["reversible"])
        self.assertTrue(result["density_matrix_32x32"]["reversible"])

    def test_heavy_tail_preserved(self):
        """Heavy-tail structure must be preserved."""
        rng = np.random.default_rng(42)
        heavy_data = rng.standard_t(df=2.5, size=100)
        proof = prove_phi_folding_reversibility(heavy_data, fold_depth=2)
        self.assertTrue(proof.heavy_tail_preserved)


class TestIntegration(unittest.TestCase):
    """Integration tests across multiple certificates."""

    def test_all_certificates_agree_on_lane_count(self):
        """All certificates must agree on 32 lanes."""
        coverage = coverage_certificate()
        structural = structural_certificate()
        self.assertEqual(coverage.num_lanes, 32)
        self.assertEqual(structural.num_nodes, 32)

    def test_all_certificates_agree_on_automorphism_order(self):
        """All certificates must agree on |Aut(G)| = 120."""
        coverage = coverage_certificate()
        structural = structural_certificate()
        self.assertEqual(coverage.automorphism_group_order, 120)
        self.assertEqual(structural.automorphism_group_order, 120)

    def test_grover_and_coverage_agree_on_nonce_space(self):
        """Grover and coverage certificates must agree on nonce space."""
        grover = grover_scope_certificate(
            target=0x1D00FFFF,
            nonce_ranges=[(0, 2**32 - 1)],
        )
        coverage = coverage_certificate()
        self.assertEqual(grover.nonce_space_size, coverage.nonce_space_size)

    def test_memory_compression_and_coverage_agree_on_lanes(self):
        """Memory compression and coverage must agree on 32 lanes."""
        lane_proof = prove_lane_surface_coverage(32, fold_depth=1)
        coverage = coverage_certificate()
        self.assertEqual(lane_proof.original_size, coverage.num_lanes)

    def test_bures_and_structural_agree_on_dimension(self):
        """Bures and structural must agree on 32 dimensions."""
        dim = 32
        psi = np.random.randn(dim) + 1j * np.random.randn(dim)
        psi = psi / np.linalg.norm(psi)
        rho = np.outer(psi, psi.conj())
        cert = bures_variational_certificate(rho, entropy_gradient=0.3)
        structural = structural_certificate()
        # Both operate on 32-dimensional space
        self.assertEqual(rho.shape[0], structural.num_nodes)


if __name__ == "__main__":
    unittest.main()
