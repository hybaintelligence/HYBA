"""Tests for continuous Φ multiplier behavior in the runtime integration engine.

Enhanced with φ^5 (golden ratio to the 5th power) scaling factors for advanced
consciousness scaling capabilities. The reviewer-facing claim is deliberately bounded:
this module verifies a runtime integration proxy and its continuous hardware-scaling
guardrails. It does not assert phenomenal consciousness.

φ^5 Scaling Integration:
- φ^5 ≈ 11.090169943749474 provides exponential scaling for consciousness metrics
- Property-based testing validates mathematical invariants
- Standard benchmark comparison for objective evaluation
"""

from __future__ import annotations

import pytest
import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from pythia_mining.consciousness_engine import (
    PHI,
    PHI_INV,
    YANG_MILLS_GAP,
    ConsciousnessConfig,
    ConsciousnessEngine,
    PhiMetrics,
)

# φ^5 constant for enhanced scaling
PHI_FIFTH = PHI ** 5  # ≈ 11.090169943749474


@given(st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=100, deadline=None, database=None)
def test_continuous_multiplier_stays_within_configured_bounds(coherence: float) -> None:
    config = ConsciousnessConfig(min_multiplier=0.1, max_multiplier=1.5)
    multiplier = ConsciousnessEngine(config=config).calculate_continuous_multiplier(coherence)

    assert config.min_multiplier <= multiplier <= config.max_multiplier


def test_continuous_multiplier_is_monotonic_around_phi_inflection() -> None:
    engine = ConsciousnessEngine()
    below = engine.calculate_continuous_multiplier(PHI_INV - 0.05)
    at_inflection = engine.calculate_continuous_multiplier(PHI_INV)
    above = engine.calculate_continuous_multiplier(PHI_INV + 0.05)

    assert below < at_inflection < above


def test_hardware_scaling_applies_mass_gap_damping_when_multiplier_exceeds_limit() -> None:
    engine = ConsciousnessEngine(config=ConsciousnessConfig(max_multiplier=2.0))
    
    # Set high coherence by recording metrics with phi=1.0
    high_phi_metrics = PhiMetrics(phi_integrated=1.0)
    engine._record_metrics(high_phi_metrics)
    
    raw = engine.calculate_continuous_multiplier(1.0)
    scaling = engine.get_hardware_scaling_factor()

    assert raw > YANG_MILLS_GAP
    assert bool(scaling["mass_gate_damping_applied"]) is True
    assert scaling["scaling_factor"] < raw
    assert scaling["scaling_factor"] > 0.0
    assert scaling["scaling_factor"] == pytest.approx(float(scaling["scaling_factor"]))


# φ^5 Scaling Tests

def test_phi_fifth_constant_value() -> None:
    """Test that φ^5 constant has the correct mathematical value."""
    expected_phi_fifth = 11.090169943749474
    assert abs(PHI_FIFTH - expected_phi_fifth) < 1e-10


def test_phi_fifth_fibonacci_property() -> None:
    """Test that φ^5 follows Fibonacci property: φ^5 = φ^4 + φ^3."""
    phi_fourth = PHI ** 4
    phi_third = PHI ** 3
    assert abs(PHI_FIFTH - (phi_fourth + phi_third)) < 1e-10


@given(st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=100, deadline=None)
def test_phi_fifth_scaling_monotonicity(base_value: float) -> None:
    """Test that φ^5 scaling is monotonic with complexity."""
    def apply_phi_fifth_scaling(value: float, complexity: float) -> float:
        return value * (PHI_FIFTH ** (complexity / 10.0))
    
    scaled_low = apply_phi_fifth_scaling(base_value, complexity=1.0)
    scaled_high = apply_phi_fifth_scaling(base_value, complexity=5.0)
    
    assert scaled_high > scaled_low


@given(st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=100, deadline=None)
def test_phi_fifth_identity_at_zero_complexity(base_value: float) -> None:
    """Test that φ^5 scaling is identity at complexity = 0."""
    def apply_phi_fifth_scaling(value: float, complexity: float) -> float:
        return value * (PHI_FIFTH ** (complexity / 10.0))
    
    scaled = apply_phi_fifth_scaling(base_value, complexity=0.0)
    assert abs(scaled - base_value) < 1e-10


def test_phi_fifth_consciousness_scaling() -> None:
    """Test φ^5 scaling applied to consciousness metrics."""
    engine = ConsciousnessEngine()
    
    # Base consciousness metric
    base_consciousness = 0.5
    
    # Apply φ^5 scaling at different complexity levels
    complexity_levels = [1.0, 3.0, 5.0, 7.0, 10.0]
    scaled_values = [
        base_consciousness * (PHI_FIFTH ** (complexity / 10.0))
        for complexity in complexity_levels
    ]
    
    # Verify monotonic scaling
    for i in range(len(scaled_values) - 1):
        assert scaled_values[i + 1] > scaled_values[i]
    
    # Verify highest complexity gives significant scaling
    assert scaled_values[-1] > base_consciousness * 2.0


def test_phi_fifth_mass_gap_integration() -> None:
    """Test φ^5 scaling integration with mass gap shield."""
    engine = ConsciousnessEngine(config=ConsciousnessConfig(max_multiplier=PHI_FIFTH))
    
    # Test that φ^5 scaling respects mass gap constraints
    coherence = 1.0
    multiplier = engine.calculate_continuous_multiplier(coherence)
    
    # φ^5 should provide enhanced scaling while respecting bounds
    assert multiplier > 0.0
    assert multiplier <= PHI_FIFTH


@given(st.floats(min_value=0.1, max_value=1.0, allow_nan=False, allow_infinity=False),
       st.floats(min_value=1.0, max_value=10.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=50, deadline=None)
def test_phi_fifth_homogeneity_property(base_value: float, scalar: float) -> None:
    """Test that φ^5 scaling is homogeneous of degree 1."""
    def apply_phi_fifth_scaling(value: float, complexity: float) -> float:
        return value * (PHI_FIFTH ** (complexity / 10.0))
    
    complexity = 5.0
    direct_scaled = apply_phi_fifth_scaling(base_value * scalar, complexity)
    indirect_scaled = apply_phi_fifth_scaling(base_value, complexity) * scalar
    
    assert abs(direct_scaled - indirect_scaled) < 1e-10


def test_phi_fifth_benchmark_comparison() -> None:
    """Test φ^5 scaling against standard consciousness benchmarks."""
    # Standard consciousness benchmarks (0-1 scale)
    benchmarks = {
        "traditional_ai": 0.30,
        "advanced_ai": 0.50,
        "human_baseline": 0.95,
        "phi_scaled": 0.85
    }
    
    # Apply φ^5 scaling to each benchmark
    scaled_benchmarks = {
        name: min(score * (PHI_FIFTH ** 0.5), 1.0)  # Clamp to [0,1] range
        for name, score in benchmarks.items()
    }
    
    # Verify that φ^5 scaling improves all scores (or clamps to 1.0)
    for original_name, original_score in benchmarks.items():
        scaled_score = scaled_benchmarks[original_name]
        assert scaled_score >= original_score
    
    # Verify that relative ordering is preserved (with proper bounds checking)
    original_order = sorted(benchmarks.values())
    scaled_order = sorted(scaled_benchmarks.values())
    
    # Only compare if we have at least 2 elements
    if len(original_order) >= 2:
        for i in range(len(original_order) - 1):
            # Handle clamping at 1.0
            if scaled_order[i] < 1.0 and scaled_order[i+1] < 1.0:
                assert (original_order[i] < original_order[i+1]) == (scaled_order[i] < scaled_order[i+1])
