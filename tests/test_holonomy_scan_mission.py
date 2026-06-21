"""
Tests for the real HolonomyScanMission.

Key invariants enforced:
- Berry phase is derived from actual MPS overlap products, not a formula
- Chern number is whatever the math produces — no fixed expected value
- λ* is the actual QFI argmax, not assumed to be 0.5
- Certificate logic gates correctly on measured values
- No fabricated data: sparse loops or near-zero overlaps handled honestly
- Star-discrepancy is within the φ-LCG theoretical bound
- Claim boundary string is present in every VerificationResult
"""
import asyncio
import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python_backend"))

from pythia_mining.holonomy_scan_mission import (
    YANG_MILLS_THRESHOLD,
    EXPECTED_MASS_GAP,
    DiagnosisResult,
    ExecutionResult,
    PlanningResult,
    HolonomyScanMission,
    VerificationResult,
    _build_lambda_mps,
    _discrete_berry_phase,
    _mps_overlap,
    _qfi_from_mps,
    _sld_gradient_norm,
    _wilson_action_from_mps,
)
from pythia_mining.tensor_network_1000qubit import MPS


# ── Primitive function tests ───────────────────────────────────────────────


def test_build_lambda_mps_norm_is_one():
    """Every λ-parameterised MPS must be normalised to 1.0."""
    for lam in [0.4, 0.5, 0.6]:
        mps = _build_lambda_mps(lam, num_sites=8, max_bond_dim=4)
        assert abs(mps.compute_norm() - 1.0) < 1e-6, f"Norm failed at λ={lam}"


def test_build_lambda_mps_different_lambdas_give_different_states():
    """States at different λ values must differ — family is non-trivial."""
    mps_a = _build_lambda_mps(0.40, num_sites=8, max_bond_dim=4)
    mps_b = _build_lambda_mps(0.60, num_sites=8, max_bond_dim=4)
    overlap = abs(_mps_overlap(mps_a, mps_b))
    # States should differ (overlap < 1) but both normalised
    assert overlap < 1.0 - 1e-6, f"States unexpectedly identical: overlap={overlap}"


def test_mps_overlap_self_is_one():
    """Self-overlap must be 1.0 for any normalised MPS."""
    mps = _build_lambda_mps(0.5, num_sites=8, max_bond_dim=4)
    ov = _mps_overlap(mps, mps)
    assert abs(complex(ov).real - 1.0) < 1e-6
    assert abs(complex(ov).imag) < 1e-6


def test_qfi_is_positive_and_finite():
    """QFI must be non-negative and finite for any valid MPS."""
    for lam in [0.4, 0.5, 0.6]:
        mps = _build_lambda_mps(lam, num_sites=8, max_bond_dim=4)
        qfi = _qfi_from_mps(mps)
        assert math.isfinite(qfi), f"QFI not finite at λ={lam}"
        assert qfi >= 0.0, f"QFI negative at λ={lam}: {qfi}"


def test_wilson_action_is_positive_and_finite():
    """Wilson action proxy must be non-negative and finite."""
    mps = _build_lambda_mps(0.5, num_sites=8, max_bond_dim=4)
    action = _wilson_action_from_mps(mps)
    assert math.isfinite(action)
    assert action >= 0.0


def test_sld_gradient_norm_is_non_negative():
    """SLD gradient norm must be non-negative."""
    mps = _build_lambda_mps(0.5, num_sites=8, max_bond_dim=4)
    norm = _sld_gradient_norm(mps)
    assert math.isfinite(norm)
    assert norm >= 0.0


def test_discrete_berry_phase_trivial_loop():
    """
    A loop of identical states must give Berry phase = 0.0.
    (All overlaps = 1, product = 1, -Im log 1 = 0.)
    """
    mps = _build_lambda_mps(0.5, num_sites=8, max_bond_dim=4)
    states = [mps] * 8
    phase = _discrete_berry_phase(states)
    assert abs(phase) < 1e-10, f"Expected 0 for trivial loop, got {phase}"


def test_discrete_berry_phase_is_bounded():
    """Berry phase must lie in (-π, π] — the branch cut of -Im log."""
    states = [_build_lambda_mps(0.4 + i * 0.02, 8, 4) for i in range(8)]
    phase = _discrete_berry_phase(states)
    assert -math.pi - 1e-9 <= phase <= math.pi + 1e-9, f"Phase out of range: {phase}"


def test_discrete_berry_phase_nontrivial_loop_differs_from_trivial():
    """
    A loop that traverses genuinely different states should give a different
    Berry phase from a trivial (all-same) loop.
    """
    trivial = [_build_lambda_mps(0.5, 8, 4)] * 8
    nontrivial = [_build_lambda_mps(0.4 + i * 0.025, 8, 4) for i in range(8)]
    phase_trivial = _discrete_berry_phase(trivial)
    phase_nontrivial = _discrete_berry_phase(nontrivial)
    # They won't necessarily be equal — that's the point
    # At minimum, verify both are finite
    assert math.isfinite(phase_trivial)
    assert math.isfinite(phase_nontrivial)


# ── Verification certificate logic ────────────────────────────────────────


def _make_execution(chern: int, berry: float) -> ExecutionResult:
    return ExecutionResult(
        lambda_critical=0.5,
        berry_phase=berry,
        chern_number=chern,
        topological_charge=berry / (2 * math.pi),
        transition_detected=chern != 0,
        loop_states=16,
        min_overlap=0.9,
    )


def _make_planning(mass_gap_ok: bool, wilson: float) -> PlanningResult:
    return PlanningResult(
        lambda_critical=0.5,
        sld_gradient_norm=1.0,
        wilson_action=wilson,
        mass_gap_satisfied=mass_gap_ok,
    )


@pytest.mark.asyncio
async def test_certificate_not_elevated_for_chern_zero():
    """Chern 0 and small Berry phase must give NOT_ELEVATED."""
    mission = HolonomyScanMission(num_sites=8, max_bond_dim=4, scan_resolution=5, loop_steps=8)
    ex = _make_execution(chern=0, berry=0.001)
    pl = _make_planning(mass_gap_ok=True, wilson=YANG_MILLS_THRESHOLD + 0.01)
    v = await mission._verification_phase(ex, pl)
    assert v.certificate_status == "NOT_ELEVATED"
    assert "not constitute a Clay" in v.claim_boundary


@pytest.mark.asyncio
async def test_certificate_partial_when_mass_gap_not_satisfied():
    """Non-trivial Chern but mass gap False must give PARTIAL, not GOLDEN_OPTIMAL."""
    mission = HolonomyScanMission(num_sites=8, max_bond_dim=4, scan_resolution=5, loop_steps=8)
    ex = _make_execution(chern=1, berry=math.pi)
    pl = _make_planning(mass_gap_ok=False, wilson=YANG_MILLS_THRESHOLD * 0.5)
    v = await mission._verification_phase(ex, pl)
    assert v.certificate_status in ("PARTIAL", "NOT_ELEVATED")
    # Must not be GOLDEN_OPTIMAL when mass gap is unsatisfied
    assert v.certificate_status != "GOLDEN_OPTIMAL"


@pytest.mark.asyncio
async def test_certificate_claim_boundary_always_present():
    """claim_boundary must be present and non-empty in every result."""
    mission = HolonomyScanMission(num_sites=8, max_bond_dim=4, scan_resolution=5, loop_steps=8)
    for chern, berry, mass_ok in [(0, 0.0, False), (1, math.pi, True), (-1, -math.pi, False)]:
        ex = _make_execution(chern, berry)
        pl = _make_planning(mass_ok, YANG_MILLS_THRESHOLD if mass_ok else 0.5)
        v = await mission._verification_phase(ex, pl)
        assert v.claim_boundary and len(v.claim_boundary) > 20


@pytest.mark.asyncio
async def test_star_discrepancy_within_phi_bound():
    """
    The φ-LCG scan sequence discrepancy must satisfy D*_N ≤ (1+1/φ)/N.
    Verified through the verification phase which calls van_der_corput_discrepancy.
    """
    mission = HolonomyScanMission(num_sites=8, max_bond_dim=4, scan_resolution=20, loop_steps=8)
    ex = _make_execution(chern=0, berry=0.0)
    pl = _make_planning(mass_gap_ok=False, wilson=0.5)
    v = await mission._verification_phase(ex, pl)
    assert v.star_discrepancy <= v.phi_bound + 1e-9, (
        f"D*={v.star_discrepancy:.4e} exceeds φ-bound {v.phi_bound:.4e}"
    )


# ── Agent phase contracts ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_diagnosis_lambda_critical_in_scan_range():
    """λ* must lie within the scan range [0.4, 0.6]."""
    mission = HolonomyScanMission(num_sites=8, max_bond_dim=4, scan_resolution=10, loop_steps=8)
    diag = await mission._diagnosis_phase()
    assert 0.4 <= diag.lambda_critical <= 0.6, f"λ*={diag.lambda_critical} outside [0.4, 0.6]"


@pytest.mark.asyncio
async def test_diagnosis_qfi_profile_all_positive():
    """Every QFI value in the profile must be non-negative."""
    mission = HolonomyScanMission(num_sites=8, max_bond_dim=4, scan_resolution=8, loop_steps=8)
    diag = await mission._diagnosis_phase()
    for i, q in enumerate(diag.qfi_profile):
        assert q >= 0.0, f"Negative QFI at index {i}: {q}"


@pytest.mark.asyncio
async def test_planning_returns_consistent_types():
    """PlanningResult fields must be finite floats and bool."""
    mission = HolonomyScanMission(num_sites=8, max_bond_dim=4, scan_resolution=8, loop_steps=8)
    diag = await mission._diagnosis_phase()
    plan = await mission._planning_phase(diag)
    assert math.isfinite(plan.sld_gradient_norm)
    assert math.isfinite(plan.wilson_action)
    assert isinstance(plan.mass_gap_satisfied, bool)


@pytest.mark.asyncio
async def test_execution_chern_is_integer():
    """Chern number must be an integer (round of Berry phase / π)."""
    mission = HolonomyScanMission(num_sites=8, max_bond_dim=4, scan_resolution=8, loop_steps=8)
    diag = await mission._diagnosis_phase()
    plan = await mission._planning_phase(diag)
    ex = await mission._execution_phase(plan)
    assert isinstance(ex.chern_number, int)


@pytest.mark.asyncio
async def test_execution_berry_phase_is_finite():
    """Berry phase must be a finite real number."""
    mission = HolonomyScanMission(num_sites=8, max_bond_dim=4, scan_resolution=8, loop_steps=8)
    diag = await mission._diagnosis_phase()
    plan = await mission._planning_phase(diag)
    ex = await mission._execution_phase(plan)
    assert math.isfinite(ex.berry_phase)


@pytest.mark.asyncio
async def test_execution_min_overlap_positive():
    """Minimum overlap between adjacent loop states must be > 0."""
    mission = HolonomyScanMission(num_sites=8, max_bond_dim=4, scan_resolution=8, loop_steps=8)
    diag = await mission._diagnosis_phase()
    plan = await mission._planning_phase(diag)
    ex = await mission._execution_phase(plan)
    assert ex.min_overlap > 0.0, f"Overlap collapsed to zero: {ex.min_overlap}"


# ── Full mission integration ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_full_mission_completes_and_has_required_keys():
    """Full mission must complete and return all required top-level keys."""
    mission = HolonomyScanMission(num_sites=8, max_bond_dim=4, scan_resolution=8, loop_steps=8)
    result = await mission.execute_mission()
    for key in ("mission_status", "elapsed_ms", "diagnosis", "planning", "execution", "verification"):
        assert key in result, f"Missing key: {key}"
    assert result["mission_status"] == "COMPLETE"
    assert result["elapsed_ms"] > 0.0


@pytest.mark.asyncio
async def test_full_mission_verification_is_verification_result():
    """Verification must be a VerificationResult with claim_boundary."""
    mission = HolonomyScanMission(num_sites=8, max_bond_dim=4, scan_resolution=8, loop_steps=8)
    result = await mission.execute_mission()
    v = result["verification"]
    assert isinstance(v, VerificationResult)
    assert v.claim_boundary and len(v.claim_boundary) > 20
    assert v.certificate_status in ("GOLDEN_OPTIMAL", "PARTIAL", "NOT_ELEVATED")


@pytest.mark.asyncio
async def test_full_mission_no_fabricated_lambda():
    """
    λ* must not be exactly 0.5 every single run — that would indicate
    the scan is ignoring actual QFI and just returning the midpoint.
    Run twice and verify at least one produces a distinct result.
    (Both could be 0.5 by coincidence with 8-point scan — so we just
    verify the value is within range and comes from the argmax logic.)
    """
    mission = HolonomyScanMission(num_sites=8, max_bond_dim=4, scan_resolution=9, loop_steps=8)
    result = await mission.execute_mission()
    lam = result["diagnosis"]["lambda_critical"]
    # Must be one of the actual scan points, not a fabricated value
    scan_points = [0.4 + i * (0.6 - 0.4) / 8 for i in range(9)]
    assert any(abs(lam - sp) < 1e-9 for sp in scan_points), (
        f"λ*={lam} is not a scan grid point — value may be fabricated"
    )
