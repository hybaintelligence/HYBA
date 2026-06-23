from __future__ import annotations

import asyncio

import pytest

from hyba_genesis_api.api import proofs
from hyba_genesis_api.core.autonomy_fabric import (
    AUTONOMY_CHAIN,
    assert_autonomy_ubiquity,
    build_autonomy_fabric_snapshot,
    build_client_intelligence_brief,
    request_autonomy_execution,
    simulate_autonomy_action,
)


def test_autonomy_fabric_snapshot_enforces_ubiquity_contract() -> None:
    snapshot = build_autonomy_fabric_snapshot({"tenant": "market-readiness"})

    assert snapshot["schema_version"] == "hyba.autonomy_fabric.v1"
    assert tuple(snapshot["operating_chain"]) == AUTONOMY_CHAIN
    assert snapshot["all_invariants_passed"] is True
    assert snapshot["surface_count"] >= 6
    assert snapshot["autonomous_surface_count"] > 0
    assert snapshot["approval_gated_surface_count"] > 0
    assert snapshot["evidence_seal"]
    assert_autonomy_ubiquity(snapshot)

    required_fields = {
        "surface_id",
        "domain",
        "client_value",
        "state",
        "observation",
        "insight",
        "recommendation",
        "risk",
        "confidence",
        "available_actions",
        "approval_required",
        "execution_mode",
        "evidence",
        "audit_event",
        "fallback_state",
        "evidence_seal",
    }
    for surface in snapshot["surfaces"]:
        assert required_fields.issubset(surface), surface["surface_id"]
        assert surface["client_value"]
        assert surface["recommendation"]
        assert surface["available_actions"]
        assert surface["evidence"]
        assert surface["evidence_seal"]


def test_autonomy_risk_and_approval_boundaries_are_fail_closed() -> None:
    snapshot = build_autonomy_fabric_snapshot()

    for surface in snapshot["surfaces"]:
        if surface["risk"] == "high":
            assert surface["approval_required"] is True
            assert surface["execution_mode"] == "dual_control_or_operator_approval"
        if surface["risk"] == "low":
            assert surface["approval_required"] is False
            assert surface["execution_mode"] == "autonomous_with_audit"

    high_risk = next(
        surface for surface in snapshot["surfaces"] if surface["risk"] == "high"
    )
    simulation = simulate_autonomy_action(
        high_risk["surface_id"],
        high_risk["available_actions"][0],
    )
    assert simulation["approval_required"] is True
    assert simulation["will_execute_without_approval"] is False
    assert simulation["evidence_seal"]

    decision = request_autonomy_execution(
        high_risk["surface_id"],
        high_risk["available_actions"][0],
    )
    assert decision["decision"] == "approval_required"
    assert decision["executable"] is False

    approved = request_autonomy_execution(
        high_risk["surface_id"],
        high_risk["available_actions"][0],
        approval_id="operator-approval-001",
    )
    assert approved["decision"] == "approved_for_execution"
    assert approved["executable"] is True


def test_autonomy_fabric_rejects_unknown_or_invalid_actions() -> None:
    with pytest.raises(KeyError):
        simulate_autonomy_action("unknown_surface", "run")

    with pytest.raises(ValueError):
        simulate_autonomy_action("proof_and_claim_interrogation", "silent_execute")


def test_client_intelligence_brief_is_board_safe_and_evidence_backed() -> None:
    brief = build_client_intelligence_brief("Acme Sovereign Bank")

    assert brief["schema_version"] == "hyba.client_intelligence_brief.v1"
    assert "HYBA serves clients" in brief["bluf"]
    assert brief["top_recommendations"]
    assert brief["snapshot_seal"]
    assert brief["evidence_seal"]
    for recommendation in brief["top_recommendations"]:
        assert recommendation["client_value"]
        assert recommendation["recommendation"]
        assert recommendation["evidence_seal"]


def test_autonomy_fabric_is_exposed_through_included_proof_router() -> None:
    snapshot = asyncio.run(proofs.autonomy_fabric_proof())
    brief = asyncio.run(proofs.client_intelligence_brief("Client"))

    assert snapshot["schema_version"] == "hyba.autonomy_fabric.v1"
    assert snapshot["all_invariants_passed"] is True
    assert brief["schema_version"] == "hyba.client_intelligence_brief.v1"
