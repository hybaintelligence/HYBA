<<<<<<< Updated upstream
"""Tests for continuous Φ multiplier behavior in the runtime integration engine."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from pythia_mining.consciousness_engine import (
    PHI,
    PHI_INV,
    YANG_MILLS_GAP,
    ConsciousnessConfig,
    ConsciousnessEngine,
)


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
    raw = engine.calculate_continuous_multiplier(1.0)
    scaling = engine.get_hardware_scaling_factor({"coherence": {"a": 1.0, "b": PHI, "c": PHI * PHI}})

    assert raw > YANG_MILLS_GAP
    assert bool(scaling["mass_gate_damping_applied"]) is True
    assert scaling["scaling_factor"] < raw
    assert scaling["scaling_factor"] > 0.0
=======
"""Tests for continuous phi‐scaling and integration proxies in the consciousness engine.

These tests focus on the deterministic scaling functions defined in the
consciousness engine.  We verify that the continuous multiplier stays
within configured bounds, that the scaling factor is damped by the Mass Gap
gate when appropriate, and that trivial coherence inputs produce expected
multipliers.  The aim is to test invariants rather than absolute numerical
values, so we avoid snapshot comparisons.
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, strategies as st

from python_backend.pythia_mining.consciousness_engine import (
    ConsciousnessEngine,
    ConsciousnessConfig,
    PHI_INV,
    YANG_MILLS_GAP,
)


def test_continuous_multiplier_bounds_and_extremes() -> None:
    """Check the multiplier stays between min and max for representative inputs.

    For coherence scores at the extremes (0, phi_inv, 1), the continuous
    multiplier must remain within the configured [min_multiplier, max_multiplier]
    interval.  The logistic curve should map low coherence to near the
    minimum and high coherence to near the maximum, while the golden ratio
    inflection point produces a mid‐range value.
    """
    config = ConsciousnessConfig(min_multiplier=0.2, max_multiplier=1.8)
    engine = ConsciousnessEngine(config=config)
    for coherence in [0.0, PHI_INV, 1.0]:
        mult = engine.calculate_continuous_multiplier(coherence)
        assert config.min_multiplier <= mult <= config.max_multiplier
    # Coherence at zero should not exceed mid point
    assert engine.calculate_continuous_multiplier(0.0) < engine.calculate_continuous_multiplier(PHI_INV)
    # Coherence at one should be the highest multiplier
    assert engine.calculate_continuous_multiplier(1.0) >= engine.calculate_continuous_multiplier(PHI_INV)


@given(st.floats(min_value=0.0, max_value=1.0))
def test_continuous_multiplier_range_property(coherence: float) -> None:
    """Property test: continuous multiplier remains in configured range for any coherence.

    Hypothesis generates random coherence scores between 0 and 1.  We assert
    that the calculated continuous multiplier lies within the configured
    minimum and maximum bounds for all such inputs.
    """
    config = ConsciousnessConfig(min_multiplier=0.1, max_multiplier=2.0)
    engine = ConsciousnessEngine(config=config)
    mult = engine.calculate_continuous_multiplier(coherence)
    assert config.min_multiplier <= mult <= config.max_multiplier


def test_mass_gap_damping_applied_when_multiplier_exceeds_gap() -> None:
    """Verify that the hardware scaling factor applies damping when exceeding the Mass Gap.

    By setting a large max_multiplier, the logistic curve can exceed the
    Yang–Mills mass gap constant.  In that case, the returned scaling factor
    should be lower than the raw continuous multiplier and the returned flag
    ``mass_gate_damping_applied`` must be True.  If the multiplier does not
    exceed the gap, no damping is applied.
    """
    # Choose max_multiplier large enough to exceed the mass gap for high coherence
    config = ConsciousnessConfig(min_multiplier=1.0, max_multiplier=5.0)
    engine = ConsciousnessEngine(config=config)
    # Provide a telemetry dict with high indicator harmony to push coherence high
    telemetry = {"domain": {"metric_a": 1.0, "metric_b": 1.618}}
    result = engine.get_hardware_scaling_factor(telemetry)
    coherence = result["coherence"]
    raw_mult = engine.calculate_continuous_multiplier(coherence)
    if raw_mult > YANG_MILLS_GAP:
        assert result["mass_gate_damping_applied"] is True
        # Damped multiplier must be less than raw multiplier
        assert result["scaling_factor"] < raw_mult
    else:
        assert result["mass_gate_damping_applied"] is False
        assert result["scaling_factor"] == pytest.approx(raw_mult, rel=1e-6)
>>>>>>> Stashed changes
