from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.mining_knowledge_base import (  # noqa: E402
    MiningKnowledgeBase,
    MiningPitfallsKnowledge,
    MiningRulesKnowledge,
    OperationalExpectationsKnowledge,
    OperationalThreshold,
    SuccessCriteria,
)
from pythia_mining.phi_scaling_engine import (  # noqa: E402
    PHI,
    MassGapShield,
    PhiOptimizedFeatures,
    PhiResonanceAnalyzer,
    PhiScaledEnsemble,
    benchmark_vs_asic,
    calculate_phi_performance,
)
from pythia_mining.pulvini_memory_compression_proof import (  # noqa: E402
    phi_folding_mathematical_proof,
    prove_lane_surface_coverage,
    prove_phi_folding_reversibility,
    verify_memory_compression_gate,
)
from pythia_mining.pulvini_phi_memory import (
    PulviniPhiMemoryCompressionEngine,
)  # noqa: E402


def deterministic_dense_payload(size: int = 64) -> np.ndarray:
    index = np.arange(size, dtype=np.float64)
    return np.sin(index / PHI) + np.cos((index + 1.0) / (PHI * PHI))


class TestAgent4PhiFoldingCompression:
    def test_phi_folding_compression_ratio_reduces_working_set(self) -> None:
        result = PulviniPhiMemoryCompressionEngine(fold_depth=2).compress(
            deterministic_dense_payload(89)
        )

        assert result.compression_strategy == "phi_fold"
        assert result.working_set_compression_ratio > 1.0
        assert result.folded_dimension < np.prod(result.original_shape)

    def test_phi_folding_reversibility_guarantee_for_dense_payload(self) -> None:
        payload = deterministic_dense_payload(55)
        engine = PulviniPhiMemoryCompressionEngine(fold_depth=3)
        result = engine.compress(payload)

        assert result.reversible
        assert result.reconstruction_error <= engine.tolerance
        assert np.allclose(
            engine.decompress(result), payload, atol=engine.tolerance, rtol=0
        )

    def test_phi_folding_reports_matrix_error_bounds(self) -> None:
        base = deterministic_dense_payload(16).reshape(4, 4)
        matrix = (base + base.T) / 2.0
        result = PulviniPhiMemoryCompressionEngine(fold_depth=1).compress(matrix)

        assert result.trace_distance is not None
        assert result.hermiticity_error is not None
        assert result.entropy is not None
        assert result.trace_distance <= 1e-9
        assert result.hermiticity_error <= 1e-9

    def test_phi_folding_sparse_payload_uses_sparse_strategy(self) -> None:
        payload = np.zeros(64, dtype=np.float64)
        payload[[3, 21, 34]] = [1.0, -2.0, 3.0]
        result = PulviniPhiMemoryCompressionEngine(fold_depth=2).compress(payload)

        assert result.sparse_optimized
        assert result.compression_strategy == "sparse_fib_packed"
        assert result.reversible
        assert np.allclose(result.reconstructed, payload)

    def test_phi_folding_recursive_depth_changes_fold_count(self) -> None:
        payload = deterministic_dense_payload(144)
        shallow = PulviniPhiMemoryCompressionEngine(fold_depth=1).compress(payload)
        deep = PulviniPhiMemoryCompressionEngine(fold_depth=3).compress(payload)

        assert shallow.fold_depth == 1
        assert deep.fold_depth == 3
        assert deep.folded_dimension < shallow.folded_dimension


class TestAgent4CompressionEngine:
    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"tolerance": 0.0}, "tolerance"),
            ({"fold_depth": 0}, "fold_depth"),
            ({"sparse_skip_threshold": 1.5}, "sparse_skip_threshold"),
        ],
    )
    def test_compression_engine_initialization_rejects_invalid_config(
        self, kwargs: dict[str, float], message: str
    ) -> None:
        with pytest.raises(ValueError, match=message):
            PulviniPhiMemoryCompressionEngine(**kwargs)

    def test_compression_result_as_dict_omits_large_arrays(self) -> None:
        result = PulviniPhiMemoryCompressionEngine().compress(
            deterministic_dense_payload()
        )
        payload = result.as_dict()

        assert "folded" not in payload
        assert "kernels" not in payload
        assert "reconstructed" not in payload
        assert payload["original_shape"] == (64,)

    def test_unfold_reconstruction_returns_copy_not_internal_state(self) -> None:
        engine = PulviniPhiMemoryCompressionEngine()
        result = engine.compress(deterministic_dense_payload())
        restored = engine.decompress(result)
        restored[0] = 999.0

        assert not np.isclose(restored[0], result.reconstructed[0])

    def test_kernel_storage_efficiency_tracks_retained_bytes(self) -> None:
        result = PulviniPhiMemoryCompressionEngine(fold_depth=2).compress(
            deterministic_dense_payload(128)
        )

        assert result.retained_kernel_bytes == sum(
            kernel.nbytes for kernel in result.kernels
        )
        assert result.retained_state_compression_ratio > 0.0
        assert result.retained_kernel.size == sum(
            kernel.size for kernel in result.kernels
        )

    def test_stream_compression_consistency_across_chunks(self) -> None:
        chunks = [deterministic_dense_payload(32), deterministic_dense_payload(48)]
        result = PulviniPhiMemoryCompressionEngine(fold_depth=1).compress_stream(chunks)

        assert result.chunks == 2
        assert result.input_elements == 80
        assert result.folded_elements < result.input_elements
        assert result.max_reconstruction_error <= 1e-9


class TestAgent4Proofs:
    def test_lane_surface_coverage_proof_is_complete(self) -> None:
        proof = prove_lane_surface_coverage(32, fold_depth=1)

        assert proof.reversible
        assert proof.complete_coverage
        assert proof.original_size == 32
        assert proof.folded_size < proof.original_size

    def test_compression_reversibility_proof_is_deterministic(self) -> None:
        data = deterministic_dense_payload(34)
        first = prove_phi_folding_reversibility(data, fold_depth=2).to_dict()
        second = prove_phi_folding_reversibility(data, fold_depth=2).to_dict()

        assert first == second
        assert first["deterministic"] is True

    def test_proof_mathematical_soundness_verifies_inverse(self) -> None:
        proof = phi_folding_mathematical_proof()

        assert proof["invertible"]
        assert proof["determinant_non_zero"]
        assert proof["inverse_verification"]
        assert math.isclose(proof["w1"] + proof["w2"], 1.0, rel_tol=0, abs_tol=1e-12)

    def test_memory_compression_gate_closes(self) -> None:
        gate = verify_memory_compression_gate()

        assert gate["status"] == "CLOSED"
        assert gate["lane_surface_32"]["complete_coverage"]
        assert gate["density_matrix_32x32"]["complete_coverage"]
        assert gate["algebraic_proof"]["inverse_verification"]


class TestAgent4PhiScaling:
    def test_phi_scaled_ensemble_initialization_respects_memory_limit_alias(
        self,
    ) -> None:
        engine = PhiScaledEnsemble({"max_memory": 2})
        for score in [0.2, 0.4, 0.6]:
            engine.predict_with_phi_scaling({"model": {"score": score}}, {})

        assert engine.policy.memory_limit == 2
        assert len(engine.memory) == 2

    def test_phi_harmonized_weight_calculation_normalizes_weights(self) -> None:
        decision = PhiScaledEnsemble().predict_with_phi_scaling(
            {"a": {"score": 0.2}, "b": {"score": 0.7}, "c": {"score": 0.9}},
            {"ratios": {"x": 1.0, "y": PHI, "z": PHI * PHI}},
        )

        assert math.isclose(sum(decision["phi_weights"]), 1.0, abs_tol=1e-12)
        assert 0.0 <= decision["final_score"] <= 1.0
        assert decision["indicator_harmony"] > 0.99

    def test_golden_ratio_resonance_detection_identifies_fibonacci_like_series(
        self,
    ) -> None:
        result = PhiResonanceAnalyzer().analyze_phi_resonance(
            {"fib": [1, 2, 3, 5, 8, 13, 21]}
        )

        assert "fib_resonance" in result
        assert result["fib_resonance"]["is_fibonacci"]
        assert result["fib_resonance"]["harmony_score"] > 0.6

    def test_phi_scaling_robustness_returns_conservative_mode_for_spoofed_stream(
        self,
    ) -> None:
        shield = MassGapShield()
        expected = 1.0 / shield.resonance_gap
        telemetry = [0.0, expected, expected * 2.0]
        result = PhiScaledEnsemble().predict_with_phi_scaling(
            {"a": {"score": 0.9}}, {}, telemetry_stream=telemetry
        )

        assert result["scaling_mode"] == "conservative_due_to_simulation_detected"
        assert result["authenticity"]["reason"] == "too_perfect_likely_spoofing"
        assert result["decision"]["final_score"] == 0.0

    def test_phi_scaling_performance_impact_uses_measured_input_only_when_supplied(
        self,
    ) -> None:
        projection = benchmark_vs_asic(measured_hashes_per_second=None)
        measured = benchmark_vs_asic(measured_hashes_per_second=1000.0)

        assert projection["benchmark_mode"] == "projection_only"
        assert projection["projected_vs_asic_ratio"] is None
        assert measured["benchmark_mode"] == "measured_input"
        assert measured["effective_hashes_per_second"] is not None


class TestAgent4KnowledgeBase:
    def test_success_criteria_evaluation_scores_optimal_metrics(self) -> None:
        result = SuccessCriteria().evaluate_success(
            {
                "hashrate": 120.0,
                "efficiency": 0.9,
                "temperature": 45.0,
                "error_rate": 0.05,
            }
        )

        assert result["metric_scores"] == {
            "hashrate": 1.0,
            "efficiency": 1.0,
            "temperature": 1.0,
            "error_rate": 1.0,
        }
        assert result["overall_score"] == pytest.approx(PHI)
        assert result["recommendations"] == []

    def test_pitfall_detection_accuracy_for_hot_low_hashrate_state(self) -> None:
        pitfalls = MiningPitfallsKnowledge().check_for_pitfall_indicators(
            {"temperature": 80.0, "hashrate": 20.0, "error_rate": 0.0}
        )
        names = {pitfall.name for pitfall in pitfalls}

        assert "thermal_throttling" in names
        assert "memory_exhaustion" in names
        assert "configuration_drift" in names

    def test_mining_rules_compliance_checking_exposes_mandatory_rules(self) -> None:
        rules = MiningRulesKnowledge()
        mandatory = rules.get_mandatory_rules()
        validation = rules.validate_against_rules("submit_share", {"nonce": 7})

        assert mandatory
        assert all(rule.compliance_level == "mandatory" for rule in mandatory)
        assert validation == {"compliant": True, "violations": [], "warnings": []}

    def test_operational_expectations_validation_reports_warnings_and_critical_alerts(
        self,
    ) -> None:
        status = OperationalExpectationsKnowledge().check_thresholds(
            {
                OperationalThreshold.HASHRATE_THRESHOLD.value: 20.0,
                OperationalThreshold.TEMPERATURE_THRESHOLD.value: 72.0,
                OperationalThreshold.ERROR_RATE_THRESHOLD.value: 4.0,
            }
        )

        assert not status["within_limits"]
        assert any(
            alert["threshold"] == "hashrate_threshold"
            for alert in status["critical_alerts"]
        )
        assert any(
            alert["threshold"] == "error_rate_threshold"
            for alert in status["critical_alerts"]
        )
        assert any(
            warning["threshold"] == "temperature_threshold"
            for warning in status["warnings"]
        )

    def test_knowledge_base_consistency_and_overall_assessment(self) -> None:
        kb = MiningKnowledgeBase()
        evaluation = kb.evaluate_current_state(
            {
                "hashrate": 120.0,
                "efficiency": 0.9,
                "temperature": 45.0,
                "error_rate": 0.0,
            }
        )

        assert len(kb.get_success_criteria().evaluate_success({})["metric_scores"]) == 4
        assert len(kb.get_pitfalls()) >= 8
        assert len(kb.get_rules()) >= 6
        assert len(kb.get_expectations()) >= 6
        assert evaluation["overall_assessment"]["status"] == "healthy"


class TestAgent4Integration:
    def test_knowledge_informed_mining_decisions_feed_phi_scaling(self) -> None:
        kb_result = MiningKnowledgeBase().evaluate_current_state(
            {
                "hashrate": 100.0,
                "efficiency": 0.8,
                "temperature": 50.0,
                "error_rate": 0.1,
            }
        )
        decision = PhiScaledEnsemble().predict_with_phi_scaling(
            {
                "knowledge": {
                    "score": min(
                        1.0, kb_result["overall_assessment"]["confidence"] / PHI
                    )
                }
            },
            {"ops": {"a": 1.0, "b": PHI, "c": PHI * PHI}},
        )

        assert decision["final_score"] > 0.5
        assert decision["coherence"] == pytest.approx(1.0)

    def test_compressed_state_and_proof_agree_on_retained_dimensions(self) -> None:
        payload = deterministic_dense_payload(32)
        compression = PulviniPhiMemoryCompressionEngine(fold_depth=1).compress(payload)
        proof = prove_phi_folding_reversibility(payload, fold_depth=1)

        assert proof.folded_size == compression.folded.size
        assert proof.kernel_size == sum(kernel.size for kernel in compression.kernels)
        assert proof.total_retained_size == proof.folded_size + proof.kernel_size

    def test_phi_feature_extraction_and_performance_summary_are_bounded(self) -> None:
        features = PhiOptimizedFeatures().extract_phi_optimized_features(
            {"ops": {"phi": PHI, "inverse": 1.0 / PHI, "off": 3.0}}
        )
        summary = calculate_phi_performance(0.4, 0.7, 1.5)

        assert len(features["ops"]) == 3
        assert features["ops"][0]["phi_alignment"] == pytest.approx(1.0)
        assert summary["phi_coherence"] == 1.0
        assert summary["improvement_percentage"] > 0.0
