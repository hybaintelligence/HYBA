"""Anti-simulation invariants for the MassGapShield telemetry gate.

The MassGapShield is documented as an operational heuristic/invariant gate. The
claim under test is deterministic spoofing/chaos rejection, not a proof of the
Yang-Mills Millennium problem.
"""

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
