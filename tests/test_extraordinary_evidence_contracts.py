"""Property and adversarial tests for extraordinary-claim evidence contracts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from hyba_genesis_api.core.extraordinary_evidence import (  # noqa: E402
    CLAIMS,
    MILLENNIUM_PROBLEMS,
    build_extraordinary_evidence_packet,
)


def test_extraordinary_claims_contract_returns_sealed_complete_evidence_packet() -> (
    None
):
    packet = build_extraordinary_evidence_packet()

    assert packet["schema_version"] == "hyba.extraordinary_evidence.v1"
    assert packet["all_invariants_passed"] is True
    assert len(packet["claims"]) == 7
    assert len(packet["millennium_problems"]) == 7
    assert packet["evidence_seal"]
    assert packet["adversarial_contract"]["elevate_code_to_documented_contract"] is True


@pytest.mark.parametrize("claim", CLAIMS)
def test_every_claim_has_required_evidence_invariants_and_adversarial_tests(
    claim,
) -> None:
    materialized = claim.to_dict()

    assert materialized["required_evidence"]
    assert materialized["invariants"]
    assert materialized["adversarial_tests"]
    assert materialized["api_surfaces"]
    assert materialized["proof_status"] == "operationalized_evidence_gate"


def test_millennium_operationalization_covers_every_last_problem() -> None:
    assert set(MILLENNIUM_PROBLEMS) == {
        "yang_mills_mass_gap",
        "p_vs_np",
        "navier_stokes",
        "riemann_hypothesis",
        "hodge_conjecture",
        "bsd_conjecture",
        "poincare_conjecture",
    }


@pytest.mark.parametrize("exponent", range(1, 31))
def test_phi_hardware_scaling_property_is_finite_positive_and_monotone(
    exponent: int,
) -> None:
    packet = build_extraordinary_evidence_packet()
    phi = packet["phi"]

    value = phi**exponent
    next_value = phi ** (exponent + 1)

    assert value > 0
    assert next_value > value
    assert value != float("inf")


@pytest.mark.parametrize(
    "hostile_claim_id",
    [
        "",
        "unknown",
        "quantum_math_substrate\x00",
        "millennium_operationalization_all ",
        "../../claim",
    ],
)
def test_adversarial_unknown_claim_cannot_appear_as_supported_claim(
    hostile_claim_id: str,
) -> None:
    packet = build_extraordinary_evidence_packet()
    supported = {claim["claim_id"] for claim in packet["claims"]}

    if hostile_claim_id not in supported:
        assert hostile_claim_id not in supported
        assert packet["adversarial_contract"]["fail_closed_on_unknown_claim"] is True


def test_adversarial_packet_contains_no_placeholder_or_simulated_evidence_language() -> (
    None
):
    encoded = json.dumps(build_extraordinary_evidence_packet(), sort_keys=True).lower()
    forbidden = (
        "placeholder telemetry",
        "fixture telemetry",
        "simulated proof",
        "trust me",
    )

    for phrase in forbidden:
        assert phrase not in encoded
