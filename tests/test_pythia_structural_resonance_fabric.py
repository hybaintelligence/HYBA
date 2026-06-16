from __future__ import annotations

import pytest

from pythia_mining.resonance_fabric import (
    CriticismLedger,
    ImmutableInvariantGuard,
    RefactorDecision,
    RefactorMode,
    ResonanceMatrix,
    simulate_epoch10_structural_resonance,
)


def test_corpus_callosum_resonance_matrix_matches_epoch10_signature() -> None:
    matrix = ResonanceMatrix()

    assert matrix.active_links() == 3
    assert matrix.coherence() == pytest.approx(0.8921)
    assert matrix.get_weight("penrose_or", "iit_4") == pytest.approx(0.7250)
    assert matrix.trust_route(
        penrose_signal=0.98,
        iit_phi=0.70,
        deutsch_confidence=0.60,
    ) == "penrose_or"


def test_penrose_event_without_iit_partition_generates_handshake_criticism() -> None:
    matrix = ResonanceMatrix()
    handshake = matrix.evaluate_handshake(
        penrose_event_detected=True,
        iit_phi_partition=0.41,
    )

    assert handshake.accepted is False
    assert handshake.criticism_generated is True
    assert handshake.source == "penrose_or"
    assert handshake.target == "iit_4"
    assert "without informational integration" in handshake.reason


def test_deutsch_criticism_blocks_failed_phi_scaling_pathway() -> None:
    ledger = CriticismLedger()
    criticism = ledger.criticize_if_prediction_failed(
        target="phi_scaling_engine",
        predicted_delta_phi=0.0400,
        realised_delta_phi=0.0289,
    )

    assert criticism is not None
    assert criticism.target == "phi_scaling_engine"
    assert criticism.status == "Pathway Blocked"
    assert criticism.new_strategy == "Exponential-Asymptotic Scaling"
    assert ledger.is_blocked("phi_scaling_engine") is True


def test_immutable_invariant_guard_blocks_self_edit_of_validation_boundary() -> None:
    guard = ImmutableInvariantGuard()
    decision = guard.evaluate(
        target_module="autonomous_mining_controller",
        target_symbol="validate_constraints",
        requested_mode=RefactorMode.AUTONOMOUS_APPLY,
    )

    assert decision.decision is RefactorDecision.BLOCK
    assert decision.allowed_mode is RefactorMode.PROPOSE_ONLY
    assert decision.protected is True
    assert "immutable" in decision.reason


def test_stable_core_refactor_is_staged_not_autonomously_applied() -> None:
    guard = ImmutableInvariantGuard()
    decision = guard.evaluate(
        target_module="consciousness_engine",
        target_symbol="integration_regime",
        requested_mode=RefactorMode.AUTONOMOUS_APPLY,
    )

    assert decision.decision is RefactorDecision.STAGE_FOR_SUPERVISION
    assert decision.allowed_mode is RefactorMode.SUPERVISED_PATCH
    assert decision.protected is True


def test_epoch10_structural_report_is_claim_manifest_ready() -> None:
    report = simulate_epoch10_structural_resonance().to_dict()

    assert report["resonance"]["active_resonance_links"] == 3
    assert report["resonance"]["resonance_coherence"] == pytest.approx(0.8921)
    assert report["phi_density"] == pytest.approx(0.9642)
    assert report["structural_gain"] == pytest.approx(0.0289)
    assert report["logical_consistency"] == pytest.approx(0.94)
    assert report["criticism"]["target"] == "phi_scaling_engine"
    assert report["guard"]["decision"] == "stage_for_supervision"
