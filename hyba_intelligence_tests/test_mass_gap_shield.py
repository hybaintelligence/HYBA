"""Tests for the MassGapShield — Yang-Mills operationalized mass gap shield.

These tests exercise the authenticity verification logic of the
``MassGapShield``, which operationalises the golden-ratio gauge-coupling
fixed-point relation Δ_eff / Λ_QCD ≈ 3 - φ as a deterministic
anti-simulation gate.

They construct telemetry streams that are either too perfect (precisely
matching the expected jitter from the operationalised YM mass gap) or
too chaotic, and confirm that the shield flags them as inauthentic.
The goal is to ensure the anti‑simulation gate behaves deterministically
and yields coherent diagnostic metadata — the same mathematical rigour we
apply to Coxeter H3 certificates, A5 character orthogonality, and
phi-folding compression invariants.
"""

from __future__ import annotations

from pythia_mining.phi_scaling_engine import (
    YANG_MILLS_GAP,
    MassGapShield,
)


def test_mass_gap_shield_too_perfect() -> None:
    """Telemetry matching the expected jitter exactly should be flagged as spoofing."""
    shield = MassGapShield(tolerance=1e-9, chaos_threshold=0.1)
    expected_jitter = 1.0 / YANG_MILLS_GAP
    telemetry = [0.0, expected_jitter, expected_jitter * 2.0, expected_jitter * 3.0]
    result = shield.verify_authenticity(telemetry)
    assert result["authentic"] is False
    assert result["reason"] == "too_perfect_likely_spoofing"


def test_mass_gap_shield_too_chaotic() -> None:
    """Highly variable telemetry should be flagged as chaotic attack."""
    shield = MassGapShield(tolerance=1e-9, chaos_threshold=0.05)
    telemetry = [0.0, 10.0, -5.0, 20.0, -15.0]
    result = shield.verify_authenticity(telemetry)
    assert result["authentic"] is False
    assert result["reason"] == "too_chaotic_likely_attack"


def test_mass_gap_shield_insufficient_data() -> None:
    """Fewer than 2 points should return 'insufficient_data'."""
    shield = MassGapShield()
    result = shield.verify_authenticity([42.0])
    assert result["authentic"] is False
    assert result["reason"] == "insufficient_data"


def test_mass_gap_shield_authentic_stream() -> None:
    """A stream with moderate jitter between tolerance and chaos threshold passes."""
    shield = MassGapShield(tolerance=1e-3, chaos_threshold=0.8)
    telemetry = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    result = shield.verify_authenticity(telemetry)
    assert result["authentic"] is True
    assert result["reason"] == "organic_hardware_detected"