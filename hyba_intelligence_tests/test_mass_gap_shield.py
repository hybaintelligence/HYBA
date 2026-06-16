<<<<<<< Updated upstream
"""Anti-simulation invariants for the MassGapShield telemetry gate."""

from __future__ import annotations

from pythia_mining.phi_scaling_engine import MassGapShield, YANG_MILLS_GAP


def test_mass_gap_shield_flags_too_perfect_spoofing_stream() -> None:
    shield = MassGapShield(tolerance=1e-9, chaos_threshold=0.1)
    expected_jitter = 1.0 / YANG_MILLS_GAP
    stream = [idx * expected_jitter for idx in range(12)]

    result = shield.verify_authenticity(stream)

    assert result["authentic"] is False
    assert result["reason"] == "too_perfect_likely_spoofing"
    assert result["irrational_alignment"] < shield.tolerance


def test_mass_gap_shield_flags_chaotic_attack_stream() -> None:
    shield = MassGapShield(tolerance=1e-9, chaos_threshold=0.1)
    stream = [0.0, 100.0, -50.0, 250.0, -125.0, 625.0]

    result = shield.verify_authenticity(stream)

    assert result["authentic"] is False
    assert result["reason"] == "too_chaotic_likely_attack"
    assert result["irrational_alignment"] > shield.chaos_threshold
=======
"""Tests for the MassGapShield anti‐simulation detector.

These tests exercise the authenticity verification logic of the `MassGapShield`.
They construct telemetry streams that are either too perfect (precisely matching
the expected jitter) or too chaotic, and confirm that the detector flags them
as inauthentic.  The goal is to ensure the anti‐simulation gate behaves
deterministically and yields coherent diagnostic metadata.
"""

from __future__ import annotations

import math

from python_backend.pythia_mining.phi_scaling_engine import (
    PHI,
    YANG_MILLS_GAP,
    MassGapShield,
)


def test_mass_gap_shield_too_perfect() -> None:
    """Telemetry matching the expected jitter exactly should be marked as spoofing.

    We construct a telemetry stream whose successive differences equal the
    expected jitter derived from the Yang–Mills gap.  The detector should
    interpret this as a precision attack and return authentic=False with the
    reason 'too_perfect_likely_spoofing'.
    """
    shield = MassGapShield(tolerance=1e-9, chaos_threshold=0.1)
    expected_jitter = 1.0 / (YANG_MILLS_GAP)
    telemetry = [0.0, expected_jitter, expected_jitter * 2.0, expected_jitter * 3.0]
    result = shield.verify_authenticity(telemetry)
    assert result["authentic"] is False
    assert result["reason"] == "too_perfect_likely_spoofing"


def test_mass_gap_shield_too_chaotic() -> None:
    """Highly variable telemetry should be marked as chaotic attack.

    A stream with wildly varying jitter should trip the chaos threshold,
    resulting in authentic=False and the reason 'too_chaotic_likely_attack'.
    """
    shield = MassGapShield(tolerance=1e-9, chaos_threshold=0.05)
    telemetry = [0.0, 10.0, -5.0, 20.0, -15.0]  # huge differences
    result = shield.verify_authenticity(telemetry)
    assert result["authentic"] is False
    assert result["reason"] == "too_chaotic_likely_attack"
>>>>>>> Stashed changes
