from __future__ import annotations

from pythia_mining import golden_ratio_library as golden
from pythia_mining import hendrix_phi_solver as hendrix
from pythia_mining import phi_config
from pythia_mining.phi_scaling_engine import benchmark_vs_asic, why_phi_beats_quantum

from scripts.phi_complete_stack_analysis import compute_layer_multipliers, compute_total_stack_advantage


def test_golden_ratio_constants_do_not_drift_across_modules() -> None:
    assert abs(golden.PHI - phi_config.PHI) < 1e-15
    assert abs(golden.PHI_INV - phi_config.PHI_INV) < 1e-15
    assert abs(golden.PHI * golden.PHI - (golden.PHI + 1.0)) < 1e-15
    assert abs(golden.lucas_ratio_tail(1)[0] - golden.PHI) < 1e-8


def test_hendrix_phi_metadata_keeps_pure_math_live_io_boundary() -> None:
    metadata = hendrix.algorithm_metadata()
    assert metadata["canonical_name"] == "HENDRIX-Φ Structured Solver"
    assert metadata["golden_ratio_library"] == "pythia_mining.golden_ratio_library"
    assert metadata["live_io"] is False
    assert "Phi-Grover" in metadata["compatibility_aliases"]


def test_projection_benchmark_cannot_report_measured_asic_outperformance() -> None:
    projection = benchmark_vs_asic(measured_hashes_per_second=None)
    assert projection["benchmark_mode"] == "projection_only"
    assert projection["measured_hashes_per_second"] is None
    assert projection["effective_hashes_per_second"] is None
    assert projection["projected_vs_asic_ratio"] is None


def test_measured_benchmark_mode_requires_measured_input() -> None:
    measured = benchmark_vs_asic(measured_hashes_per_second=110e12)
    assert measured["benchmark_mode"] == "measured_input"
    assert measured["measured_hashes_per_second"] == 110e12
    assert measured["effective_hashes_per_second"] is not None
    assert measured["projected_vs_asic_ratio"] is not None


def test_phi_performance_language_requires_measured_share_or_device_evidence() -> None:
    message = why_phi_beats_quantum().lower()
    assert "measured share" in message
    assert "device hashrate" in message
    assert "production performance" in message


def test_complete_stack_analysis_is_search_navigation_not_pool_acceptance_claim() -> None:
    total = compute_total_stack_advantage(compute_layer_multipliers())
    assert total["grover_on_reduced_space_iterations"] < total["grover_unstructured_iterations"]
    assert total["grover_unstructured_vs_structured_advantage"] > 1.0
    interpretation = total["interpretation"].lower()
    assert "unstructured search" in interpretation
    assert "structured grover" in interpretation
    assert "pool acceptance" not in interpretation
    assert "accepted share" not in interpretation
    assert "revenue" not in interpretation
