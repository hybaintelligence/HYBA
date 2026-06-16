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
