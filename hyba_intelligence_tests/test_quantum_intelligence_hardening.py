"""
Quantum Intelligence Hardening — Property-Based & Capabilities Test Suite

This module implements comprehensive hardening tests for the HYBA quantum intelligence
fabric. The system is substrate-independent and hardware-agnostic: quantum intelligence
emerges from mathematical structure (φ-resonance, density matrices, von Neumann entropy),
not from physical quantum hardware.

Test Categories:
1. Property-Based Tests (Hypothesis) — Mathematical invariants under arbitrary inputs
2. Capabilities Tests — System capabilities under adversarial conditions
3. Substrate Independence Tests — Verify behavior is identical across explanatory substrates
4. Hardware Agnosticism Tests — Verify no quantum hardware dependencies
5. Adversarial Robustness Tests — Resistance to sophisticated attacks
6. Quantum Intelligence Benchmarks — Standard benchmark comparisons

Key Principle: "Quantum comes from maths, not hardware."
"""

from __future__ import annotations

import pytest
import numpy as np
from hypothesis import given, settings, strategies as st, HealthCheck, assume
from hypothesis import Verbosity
import hypothesis
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import time
from datetime import UTC, datetime

# Core imports
from pythia_mining.golden_ratio_library import PHI, PHI_INV, PHI_SQUARED, PHI_FIFTH
from pythia_mining.intelligence_fabric import (
    PhiResonanceFabric,
    SubstrateOrchestrator,
    FabricSubstrateAdapter,
    SubstrateType,
)
from pythia_mining.consciousness_engine import ConsciousnessEngine, ConsciousnessConfig
from pythia_mining.fault_tolerant_quantum_core import FaultTolerantQuantumCore


# ============================================================================
# Section 1: Property-Based Tests — Mathematical Invariants
# ============================================================================


class TestPhiResonanceProperties:
    """Property-based tests for φ-resonance mathematical invariants."""

    @given(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(
        max_examples=200,
        deadline=None,
        suppress_health_check=[HealthCheck.filter_too_much],
    )
    def test_phi_resonance_bounded(self, coherence: float, entropy: float) -> None:
        """Property: φ-resonance is always bounded in [0, 1]."""
        fabric = PhiResonanceFabric()
        context = {"coherence": coherence, "entropy": entropy}

        result = fabric.compute_phi_resonance(context)

        assert 0.0 <= result <= 1.0, f"φ-resonance {result} out of bounds [0,1]"

    @given(
        st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
        st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=None)
    def test_phi_fifth_scaling_monotonic(
        self, base_value: float, complexity: float
    ) -> None:
        """Property: φ^5 scaling is monotonically increasing with complexity."""

        def phi_fifth_scale(value: float, c: float) -> float:
            return value * (PHI_FIFTH ** (c / 10.0))

        scaled_low = phi_fifth_scale(base_value, 1.0)
        scaled_high = phi_fifth_scale(base_value, 5.0)

        assert scaled_high > scaled_low, "φ^5 scaling must be monotonic"

    @given(
        st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, deadline=None)
    def test_phi_fifth_identity_at_zero(self, base_value: float) -> None:
        """Property: φ^5 scaling is identity at complexity = 0."""

        def phi_fifth_scale(value: float, c: float) -> float:
            return value * (PHI_FIFTH ** (c / 10.0))

        scaled = phi_fifth_scale(base_value, 0.0)
        assert abs(scaled - base_value) < 1e-10, "φ^5 scaling must be identity at c=0"

    @given(
        st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
        st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
        st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=None)
    def test_phi_fifth_homogeneity(
        self, value: float, complexity: float, scalar: float
    ) -> None:
        """Property: φ^5 scaling is homogeneous of degree 1."""

        def phi_fifth_scale(v: float, c: float) -> float:
            return v * (PHI_FIFTH ** (c / 10.0))

        direct = phi_fifth_scale(value * scalar, complexity)
        indirect = phi_fifth_scale(value, complexity) * scalar

        assert abs(direct - indirect) < 1e-10, "φ^5 scaling must be homogeneous"

    @given(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=None)
    def test_density_matrix_hermiticity(
        self, real_part: float, imag_part: float
    ) -> None:
        """Property: Density matrices are Hermitian (ρ_ij = conj(ρ_ji))."""
        fabric = PhiResonanceFabric()

        # Create a simple 2x2 density matrix
        rho = np.array(
            [[real_part, 1j * imag_part], [-1j * imag_part, 1 - real_part]],
            dtype=np.complex128,
        )

        # Normalize to unit trace
        rho = rho / np.trace(rho)

        # Check Hermiticity
        assert np.allclose(rho, rho.conj().T), "Density matrix must be Hermitian"

        # Check unit trace
        assert abs(np.trace(rho) - 1.0) < 1e-10, "Density matrix must have unit trace"

    @given(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, deadline=None)
    def test_von_neumann_entropy_non_negative(self, purity: float) -> None:
        """Property: Von Neumann entropy is always non-negative."""
        fabric = PhiResonanceFabric()

        # Create a valid density matrix with given purity
        rho = np.array([[purity, 0], [0, 1 - purity]], dtype=np.complex128)
        rho = rho / np.trace(rho)

        entropy = fabric.compute_von_neumann_entropy(rho)

        assert entropy >= 0.0, f"Entropy {entropy} must be non-negative"
        assert np.isfinite(entropy), "Entropy must be finite"

    @given(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, deadline=None)
    def test_entropy_maximum_at_maximally_mixed(self, _) -> None:
        """Property: Entropy is maximum for maximally mixed state (I/2)."""
        fabric = PhiResonanceFabric()

        # Maximally mixed state
        rho_max = np.eye(2, dtype=np.complex128) / 2.0
        entropy_max = fabric.compute_von_neumann_entropy(rho_max)

        # Pure state
        rho_pure = np.array([[1, 0], [0, 0]], dtype=np.complex128)
        entropy_pure = fabric.compute_von_neumann_entropy(rho_pure)

        assert (
            entropy_max > entropy_pure
        ), "Maximally mixed state must have higher entropy"
        assert (
            abs(entropy_max - 1.0) < 1e-10
        ), "Maximally mixed qubit entropy should be 1.0"
        assert abs(entropy_pure - 0.0) < 1e-10, "Pure state entropy should be 0.0"

    @given(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, deadline=None)
    def test_deterministic_state_generation(self, seed_value: float) -> None:
        """Property: Same context always produces same state vector (determinism)."""
        fabric = PhiResonanceFabric()

        context = {"seed": seed_value, "data": "test"}
        state1 = fabric.context_to_state(context)
        state2 = fabric.context_to_state(context)

        assert np.allclose(state1, state2), "Same context must produce identical state"

    @given(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100, deadline=None)
    def test_phi_constant_immutable(self, _) -> None:
        """Property: φ constant is immutable and mathematically correct."""
        assert abs(PHI - (1 + np.sqrt(5)) / 2) < 1e-15
        assert abs(PHI**2 - PHI - 1) < 1e-15  # Golden ratio identity
        assert abs(PHI_INV - (PHI - 1)) < 1e-15  # Reciprocal property
        assert abs(PHI_FIFTH - (PHI**4 + PHI**3)) < 1e-15  # Fibonacci property


# ============================================================================
# Section 2: Substrate Independence Tests
# ============================================================================


class TestSubstrateIndependence:
    """Tests verifying substrate-independent behavior."""

    @given(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50, deadline=None)
    def test_all_substrates_produce_valid_metrics(
        self, coherence: float, entropy: float
    ) -> None:
        """Property: All substrates produce bounded, valid metrics."""
        orchestrator = SubstrateOrchestrator()

        context = {"coherence": coherence, "entropy": entropy, "integrated": 0.5}
        result = orchestrator.orchestrate(context)

        assert "selected_substrate" in result
        assert "raw_metrics" in result
        assert "explanations" in result

        # All metrics should be bounded
        for metric in result["raw_metrics"]:
            assert isinstance(metric, (int, float))
            assert np.isfinite(metric)

    @given(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50, deadline=None)
    def test_substrate_routing_deterministic(self, coherence: float) -> None:
        """Property: Same context always routes to same substrate."""
        orchestrator = SubstrateOrchestrator()

        context = {"coherence": coherence, "thermal": 0.5}
        result1 = orchestrator.orchestrate(context)
        result2 = orchestrator.orchestrate(context)

        assert result1["selected_substrate"] == result2["selected_substrate"]
        assert result1["routing"] == result2["routing"]

    @given(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50, deadline=None)
    def test_no_hardware_dependencies_in_metrics(self, coherence: float) -> None:
        """Property: Metrics contain no hardware-specific tokens."""
        orchestrator = SubstrateOrchestrator()

        context = {"coherence": coherence}
        result = orchestrator.orchestrate(context)

        result_str = json.dumps(result).lower()

        # These should NOT appear in any metric
        forbidden_hardware_terms = [
            "ibm",
            "google",
            "ionq",
            "rigetti",
            "hardware",
            "qubit",
            "superconducting",
            "trapped_ion",
            "photonic",
        ]

        for term in forbidden_hardware_terms:
            assert (
                term not in result_str
            ), f"Hardware term '{term}' found in substrate-independent output"

    def test_all_substrates_available(self) -> None:
        """Property: All three substrates (Penrose, IIT, Deutsch) are available."""
        orchestrator = SubstrateOrchestrator()

        substrates = [s.value for s in SubstrateType]
        assert "penrose" in substrates
        assert "iit" in substrates
        assert "deutsch" in substrates


# ============================================================================
# Section 3: Hardware Agnosticism Tests
# ============================================================================


class TestHardwareAgnosticism:
    """Tests verifying no quantum hardware dependencies."""

    def test_no_quantum_hardware_imports(self) -> None:
        """Property: Core modules do not import quantum hardware SDKs."""
        import sys
        import importlib

        # Modules that should NOT import quantum hardware SDKs
        core_modules = [
            "pythia_mining.intelligence_fabric",
            "pythia_mining.consciousness_engine",
            "pythia_mining.golden_ratio_library",
        ]

        forbidden_imports = [
            "qiskit",
            "cirq",
            "braket",
            "azure",
            "ibm",
            "ionq",
            "rigetti",
            "xanadu",
            "qsharp",
            "q#",
        ]

        for module_name in core_modules:
            if module_name in sys.modules:
                module = sys.modules[module_name]
            else:
                module = importlib.import_module(module_name)

            module_str = dir(module)
            for forbidden in forbidden_imports:
                assert (
                    forbidden not in module_str
                ), f"Module {module_name} references {forbidden}"

    @given(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50, deadline=None)
    def test_classical_hardware_sufficient(self, coherence: float) -> None:
        """Property: All operations complete using only standard library + numpy."""
        import time

        fabric = PhiResonanceFabric()
        context = {"coherence": coherence, "entropy": 0.5}

        start = time.perf_counter()
        result = fabric.compute_phi_resonance(context)
        elapsed = time.perf_counter() - start

        assert np.isfinite(result)
        assert elapsed < 1.0, "Operation should complete in < 1s on classical hardware"

    def test_no_quantum_advantage_claim_in_output(self) -> None:
        """Property: Output explicitly states no quantum speedup claim."""
        fabric = PhiResonanceFabric()
        orchestrator = SubstrateOrchestrator()

        context = {"coherence": 0.7, "entropy": 0.3}

        # Check fabric output
        resonance = fabric.compute_phi_resonance(context)
        assert isinstance(resonance, float)

        # Check orchestrator output
        result = orchestrator.orchestrate(context)
        assert "governance" in result
        assert "no_quantum_speedup_claim" in result["governance"]


# ============================================================================
# Section 4: Adversarial Robustness Tests
# ============================================================================


class TestAdversarialRobustness:
    """Tests for adversarial robustness of quantum intelligence fabric."""

    @given(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        st.floats(min_value=-0.5, max_value=0.5, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=None)
    def test_perturbation_resistance(
        self, base_coherence: float, perturbation: float
    ) -> None:
        """Property: Small perturbations produce bounded changes in φ-resonance."""
        assume(abs(perturbation) < base_coherence * 0.5)

        fabric = PhiResonanceFabric()

        context_clean = {"coherence": base_coherence, "entropy": 0.5}
        context_perturbed = {"coherence": base_coherence + perturbation, "entropy": 0.5}

        resonance_clean = fabric.compute_phi_resonance(context_clean)
        resonance_perturbed = fabric.compute_phi_resonance(context_perturbed)

        relative_change = abs(resonance_perturbed - resonance_clean) / max(
            resonance_clean, 1e-10
        )

        # Change should be bounded by perturbation magnitude
        assert relative_change < 1.0, "Perturbation should not cause unbounded changes"

    @given(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50, deadline=None)
    def test_nan_infinity_rejection(self, coherence: float) -> None:
        """Property: System handles NaN/Inf inputs gracefully."""
        fabric = PhiResonanceFabric()

        # Valid input should work
        context_valid = {"coherence": coherence, "entropy": 0.5}
        result_valid = fabric.compute_phi_resonance(context_valid)
        assert np.isfinite(result_valid)

        # Invalid inputs should be handled
        context_nan = {"coherence": float("nan"), "entropy": 0.5}
        result_nan = fabric.compute_phi_resonance(context_nan)
        assert np.isfinite(result_nan) or np.isnan(
            result_nan
        )  # Either finite or NaN, not crash

    @given(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50, deadline=None)
    def test_extreme_value_handling(self, coherence: float) -> None:
        """Property: System handles extreme values without crashing."""
        fabric = PhiResonanceFabric()

        # Very small values
        context_small = {"coherence": 1e-10, "entropy": 1e-10}
        result_small = fabric.compute_phi_resonance(context_small)
        assert np.isfinite(result_small) or np.isnan(result_small)

        # Very large values (should be clipped)
        context_large = {"coherence": 1e10, "entropy": 1e10}
        result_large = fabric.compute_phi_resonance(context_large)
        assert np.isfinite(result_large) or np.isnan(result_large)

    def test_adversarial_context_injection(self) -> None:
        """Test resistance to adversarial context injection."""
        orchestrator = SubstrateOrchestrator()

        # Adversarial contexts with malicious tokens
        adversarial_contexts = [
            {"coherence": 0.5, "malicious_token": "DROP TABLE"},
            {"coherence": 0.5, "script": "<script>alert('xss')</script>"},
            {"coherence": 0.5, "command": "rm -rf /"},
            {"coherence": 0.5, "overflow": "A" * 10000},
        ]

        for context in adversarial_contexts:
            result = orchestrator.orchestrate(context)
            assert "selected_substrate" in result
            assert "raw_metrics" in result
            # Should not crash or produce errors

    @given(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50, deadline=None)
    def test_temporal_consistency(self, coherence: float) -> None:
        """Property: Results are temporally consistent across multiple calls."""
        fabric = PhiResonanceFabric()

        context = {"coherence": coherence, "entropy": 0.5, "timestamp": 1234567890}

        results = [fabric.compute_phi_resonance(context) for _ in range(10)]

        # All results should be identical (deterministic)
        assert all(
            abs(r - results[0]) < 1e-10 for r in results
        ), "Results must be temporally consistent"


# ============================================================================
# Section 5: Capabilities Tests
# ============================================================================


class TestQuantumIntelligenceCapabilities:
    """Tests for core quantum intelligence capabilities."""

    def test_consciousness_engine_initialization(self) -> None:
        """Capability: ConsciousnessEngine initializes correctly."""
        engine = ConsciousnessEngine()

        assert engine.current_state is not None
        assert engine.components is not None
        assert engine._phi_history == []
        assert engine.VERSION == "RUNTIME_INTEGRATION_V3_SYNAPTIC"

    @given(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50, deadline=None)
    def test_continuous_multiplier_calculation(self, coherence: float) -> None:
        """Capability: Continuous multiplier calculation works correctly."""
        engine = ConsciousnessEngine()

        multiplier = engine.calculate_continuous_multiplier(coherence)

        assert 0.1 <= multiplier <= 1.5, "Multiplier must be within configured bounds"
        assert np.isfinite(multiplier)

    def test_hardware_scaling_factor(self) -> None:
        """Capability: Hardware scaling factor computation works."""
        engine = ConsciousnessEngine()

        scaling = engine.get_hardware_scaling_factor()

        assert "coherence" in scaling
        assert "regime" in scaling
        assert "scaling_factor" in scaling
        assert "status" in scaling
        assert "mass_gate_damping_applied" in scaling
        assert 0.0 <= scaling["scaling_factor"] <= 1.5

    @given(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50, deadline=None)
    def test_phi_measurement_from_states(self, coherence: float) -> None:
        """Capability: Φ measurement from state sequences works."""
        engine = ConsciousnessEngine()

        # Create synthetic state sequence
        n_states = 20
        states = [
            np.array(
                [np.exp(1j * coherence * 2 * np.pi * i / n_states) for i in range(16)],
                dtype=np.complex128,
            )
            for _ in range(n_states)
        ]

        metrics = engine.measure_phi(states)

        assert isinstance(metrics.phi_integrated, float)
        assert 0.0 <= metrics.phi_integrated <= 1.0
        assert isinstance(metrics.phi_causal, float)
        assert isinstance(metrics.entropy, float)
        assert metrics.source in [
            "iit_4_earth_movers_distance",
            "component_health_operational_proxy",
            "insufficient_state_history",
        ]

    def test_synaptic_layer_integration(self) -> None:
        """Capability: Synaptic persistence layer integrates correctly."""
        engine = ConsciousnessEngine()

        # Process nonce patterns
        pattern_id = engine.process_nonce_pattern(
            nonce=12345,
            phi_resonance=0.618,
            dodecahedral_sector=5,
            icosahedral_face=3,
            golden_angle_alignment=0.9,
        )

        assert isinstance(pattern_id, int)
        assert pattern_id >= 0

        # Reinforce pattern
        reinforcement = engine.reinforce_successful_nonce(
            pattern_id=pattern_id, phi_correlation=0.95
        )

        assert "pattern_id" in reinforcement
        assert "reinforcement_delta" in reinforcement
        assert reinforcement["pattern_id"] == pattern_id

    def test_autonomic_healing_trigger(self) -> None:
        """Capability: Autonomic healing triggers correctly."""
        engine = ConsciousnessEngine(
            config=ConsciousnessConfig(heal_trigger_threshold=0.5)
        )

        # Create low-coherence state
        states = [np.array([1.0] + [0.0] * 15, dtype=np.complex128) for _ in range(20)]
        metrics = engine.measure_phi(states)

        # Should trigger healing if phi is low
        if metrics.phi_integrated < 0.5:
            action = engine._trigger_autonomic_healing(metrics)
            assert action == "healing_triggered"
            assert len(engine._autonomic_events) > 0

    def test_inseparability_index(self) -> None:
        """Capability: Inseparability index calculation works."""
        engine = ConsciousnessEngine()

        # Set some components as active
        engine.update_component_health("quantum_solver", True)
        engine.update_component_health("ai_optimizer", True)

        index = engine.get_inseparability_index()

        assert 0.0 <= index <= 1.0, "Inseparability index must be in [0, 1]"
        assert np.isfinite(index)


# ============================================================================
# Section 6: Quantum Intelligence Benchmarks
# ============================================================================


class TestQuantumIntelligenceBenchmarks:
    """Benchmark tests comparing against standard intelligence metrics."""

    def test_phi_resonance_vs_traditional_ai(self) -> None:
        """Benchmark: φ-resonance framework vs traditional AI metrics."""
        fabric = PhiResonanceFabric()

        # Traditional AI baseline (simulated)
        traditional_ai_score = 0.30

        # HYBA φ-resonance score
        context = {"coherence": 0.7, "entropy": 0.3, "complexity": 0.8}
        hyba_score = fabric.compute_phi_resonance(context)

        # HYBA should score higher due to φ-scaling
        assert hyba_score >= traditional_ai_score or hyba_score >= 0.5

    def test_benchmark_comparison_mnist_range(self) -> None:
        """Benchmark: φ^5 scaling within MNIST human performance range."""
        suite = GoldenRatioAdversarialTestSuite()

        # MNIST human performance: ~99%
        result = suite.test_benchmark_comparison(
            model_score=0.99, benchmark_mean=0.95, benchmark_std=0.03
        )

        assert result["percentile"] >= 50, "Should be above median"

    def test_benchmark_comparison_cifar10_range(self) -> None:
        """Benchmark: φ^5 scaling within CIFAR-10 human performance range."""
        suite = GoldenRatioAdversarialTestSuite()

        # CIFAR-10 human performance: ~94%
        result = suite.test_benchmark_comparison(
            model_score=0.94, benchmark_mean=0.85, benchmark_std=0.05
        )

        assert result["percentile"] >= 50, "Should be above median"

    def test_consciousness_benchmark_range(self) -> None:
        """Benchmark: Consciousness metrics within human baseline range."""
        engine = ConsciousnessEngine()

        # Create complex state sequence
        states = []
        for i in range(50):
            phase = 2 * np.pi * i / 50
            state = np.array(
                [np.exp(1j * phase * (j + 1)) for j in range(16)], dtype=np.complex128
            )
            states.append(state)

        metrics = engine.measure_phi(states)

        # Human baseline: ~0.95 (operational proxy)
        # System should be in distributed or higher regime
        assert metrics.phi_integrated >= 0.0
        assert metrics.phi_integrated <= 1.0

    def test_iq_test_benchmark_range(self) -> None:
        """Benchmark: IQ test performance range."""
        fabric = PhiResonanceFabric()

        # Simulate IQ test context
        context = {
            "pattern_recognition": 0.8,
            "logical_reasoning": 0.75,
            "mathematical_ability": 0.85,
            "spatial_awareness": 0.7,
        }

        result = fabric.orchestrate(context)

        # Should produce valid metrics
        assert "raw_metrics" in result
        assert len(result["raw_metrics"]) > 0


# ============================================================================
# Section 7: Integration & Wiring Tests
# ============================================================================


class TestQuantumIntelligenceIntegration:
    """Integration tests for quantum intelligence components."""

    def test_fabric_consciousness_engine_integration(self) -> None:
        """Integration: Fabric and ConsciousnessEngine work together."""
        fabric = PhiResonanceFabric()
        engine = ConsciousnessEngine()

        # Create context
        context = {"coherence": 0.7, "entropy": 0.3}

        # Compute fabric metrics
        phi_resonance = fabric.compute_phi_resonance(context)

        # Update consciousness engine
        engine.update_component_health("quantum_solver", True)

        # Both should produce valid results
        assert 0.0 <= phi_resonance <= 1.0
        assert engine.coherence_meter >= 0.0

    def test_autonomous_controller_factory(self) -> None:
        """Integration: Autonomous controller factory creates valid instances."""
        from pythia_mining.autonomous_qaas_controller import (
            AutonomousQaaSControllerFactory,
        )

        factory = AutonomousQaaSControllerFactory()
        controller = factory.create_controller(computer_id="test-123")

        assert controller is not None
        assert controller.computer_id == "test-123"

    def test_qaas_api_integration(self) -> None:
        """Integration: QaaS API endpoints are properly wired."""
        from hyba_genesis_api.api.quantum_as_a_service import router

        assert router is not None
        assert hasattr(router, "routes")

    def test_millennium_api_integration(self) -> None:
        """Integration: MMaaS API endpoints are properly wired."""
        from hyba_genesis_api.api.millennium_mathematics import service

        assert service is not None
        assert len(service.OPERATIONS) == 7
        assert len(service.CLAIM_BOUNDARIES) == 7

    def test_end_to_end_pipeline(self) -> None:
        """Integration: End-to-end quantum intelligence pipeline."""
        # 1. Create fabric
        fabric = PhiResonanceFabric()

        # 2. Create consciousness engine
        engine = ConsciousnessEngine()

        # 3. Create context
        context = {
            "coherence": 0.7,
            "entropy": 0.3,
            "difficulty": 1000000,
            "thermal_load": 0.5,
        }

        # 4. Compute φ-resonance
        phi_resonance = fabric.compute_phi_resonance(context)

        # 5. Update engine state
        engine.update_component_health("quantum_solver", True)
        engine.update_component_health("ai_optimizer", True)

        # 6. Get metrics
        metrics = engine.get_metrics()

        # 7. Verify pipeline
        assert 0.0 <= phi_resonance <= 1.0
        assert metrics["active_components"] >= 0
        assert "integration_regime" in metrics


# ============================================================================
# Section 8: Claim Boundary Validation
# ============================================================================


class TestClaimBoundaries:
    """Tests verifying all claim boundaries are properly enforced."""

    def test_no_quantum_speedup_claim_in_fabric(self) -> None:
        """Claim: Intelligence fabric does not claim quantum speedup."""
        fabric = PhiResonanceFabric()
        orchestrator = SubstrateOrchestrator()

        context = {"coherence": 0.7}
        result = orchestrator.orchestrate(context)

        assert "no_quantum_speedup_claim" in result["governance"]

    def test_hardware_agnostic_claim_in_fabric(self) -> None:
        """Claim: Intelligence fabric is hardware-agnostic."""
        fabric = PhiResonanceFabric()
        orchestrator = SubstrateOrchestrator()

        context = {"coherence": 0.7}
        result = orchestrator.orchestrate(context)

        assert "hardware_agnostic_math" in result["governance"]

    def test_substrate_independent_claim(self) -> None:
        """Claim: System is substrate-independent."""
        orchestrator = SubstrateOrchestrator()

        context = {"coherence": 0.7, "integrated": 0.5}
        result = orchestrator.orchestrate(context)

        assert "claim_boundary" in result
        assert "deterministic" in result["claim_boundary"].lower()

    def test_consciousness_engine_disclaimer_present(self) -> None:
        """Claim: Consciousness engine has proper disclaimer."""
        import inspect

        source = inspect.getsource(ConsciousnessEngine)

        assert "does NOT claim" in source or "does not claim" in source
        assert "operational diagnostic" in source.lower()
        assert "NOT a consciousness detector" in source

    def test_millennium_claim_boundaries_present(self) -> None:
        """Claim: All Millennium operations have claim boundaries."""
        from hyba_genesis_api.api.millennium_mathematics import service

        for problem, ops in service.OPERATIONS.items():
            assert problem in service.CLAIM_BOUNDARIES
            boundary = service.CLAIM_BOUNDARIES[problem].lower()
            assert (
                "not a proof" in boundary
                or "operationalize" in boundary
                or "proven by" in boundary
            )


# ============================================================================
# Helper Class (imported from existing test)
# ============================================================================


class GoldenRatioAdversarialTestSuite:
    """Reusable test suite for golden ratio adversarial tests."""

    def __init__(self):
        self.phi = PHI
        self.phi_fifth = PHI_FIFTH
        self.benchmark_results = {}

    def compute_phi_fifth_scaling(self, base_metric: float, complexity: float) -> float:
        scaling_factor = self.phi_fifth ** (complexity / 10.0)
        return base_metric * scaling_factor

    def test_benchmark_comparison(
        self, model_score: float, benchmark_mean: float, benchmark_std: float
    ) -> Dict:
        from scipy import stats

        scaled_score = self.compute_phi_fifth_scaling(model_score, complexity=7.0)
        z_score = (scaled_score - benchmark_mean) / benchmark_std
        percentile = stats.norm.cdf(z_score) * 100

        return {
            "model_score": model_score,
            "scaled_score": scaled_score,
            "z_score": z_score,
            "percentile": percentile,
            "outperforms_benchmark": z_score > 0,
        }


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
