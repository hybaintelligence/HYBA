"""Contract tests for HYBA executable proof surfaces."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from hypothesis import given, strategies as st

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from hyba_genesis_api.api import proofs  # noqa: E402
from hyba_genesis_api.core.proof_surfaces import (  # noqa: E402
    CLAIM_CHAIN,
    PROOF_SURFACES,
    build_runtime_evidence_ledger,
    get_proof_surface,
    list_proof_surfaces,
)

EXPECTED_ENDPOINTS = {
    "property-tests": "/api/proofs/property-tests",
    "adversarial": "/api/proofs/adversarial",
    "invariants": "/api/proofs/invariants",
    "mining-readiness": "/api/proofs/mining-readiness",
    "autonomy": "/api/proofs/autonomy",
    "memory-compression": "/api/proofs/memory-compression",
    "phi-scaling": "/api/proofs/phi-scaling",
    "security": "/api/proofs/security",
    "audit-ledger": "/api/proofs/audit-ledger",
    "runtime-evidence": "/api/proofs/runtime-evidence",
}

FORBIDDEN_POSTURE = (
    "trust andre",
    "trust the story",
    "trust the vision",
    "believe hyba",
    "nothing is unproven",
)


def _assert_contract_payload(payload: dict) -> None:
    assert payload["claim"]
    assert payload["status"] in {"verified", "evidence_linked", "runtime_required"}
    assert payload["test_suite"]
    assert isinstance(payload["passes"], int)
    assert isinstance(payload["failures"], int)
    assert payload["failures"] == 0
    assert payload["invariants"]
    assert payload["artifacts"]
    assert payload["artifact_records"]
    assert payload["executable_commands"]
    assert payload["verification_chain"] == CLAIM_CHAIN
    assert len(payload["ledger_digest"]) == 64

    encoded = json.dumps(payload, sort_keys=True).lower()
    for forbidden in FORBIDDEN_POSTURE:
        assert forbidden not in encoded


def test_proof_surface_index_exposes_required_buyer_posture() -> None:
    index = list_proof_surfaces()

    assert index["surface_count"] >= len(EXPECTED_ENDPOINTS)
    assert index["verification_chain"] == CLAIM_CHAIN
    assert "Run the proof" in index["claim_boundary"]
    assert "Every material operational claim" in index["material_claim_standard"]

    endpoints = {surface["endpoint"] for surface in index["surfaces"]}
    for endpoint in EXPECTED_ENDPOINTS.values():
        assert endpoint in endpoints


def test_each_required_surface_returns_contract_payload() -> None:
    for key, endpoint in EXPECTED_ENDPOINTS.items():
        if key == "audit-ledger":
            continue
        payload = get_proof_surface(key)
        assert payload["key"] == key
        assert payload["endpoint"] == endpoint
        _assert_contract_payload(payload)


def test_named_endpoint_functions_return_expected_surfaces() -> None:
    endpoint_calls = {
        "property-tests": proofs.property_tests_proof,
        "adversarial": proofs.adversarial_proof,
        "invariants": proofs.invariants_proof,
        "mining-readiness": proofs.mining_readiness_proof,
        "autonomy": proofs.autonomy_proof,
        "memory-compression": proofs.memory_compression_proof,
        "phi-scaling": proofs.phi_scaling_proof,
        "security": proofs.security_proof,
        "runtime-evidence": proofs.runtime_evidence_proof,
    }

    for key, call in endpoint_calls.items():
        payload = asyncio.run(call())
        assert payload["key"] == key
        assert payload["endpoint"] == EXPECTED_ENDPOINTS[key]
        _assert_contract_payload(payload)


def test_audit_ledger_digest_covers_all_surfaces() -> None:
    ledger = build_runtime_evidence_ledger()

    assert ledger["ledger"] == "hyba_material_claim_verification_surfaces"
    assert ledger["status"] == "audit_ledger_available"
    assert ledger["surface_count"] == len(PROOF_SURFACES)
    assert len(ledger["head_hash"]) == 64
    assert {item["key"] for item in ledger["items"]} == set(PROOF_SURFACES)


def test_fastapi_routes_are_wired() -> None:
    from hyba_genesis_api.main import app

    route_paths = {getattr(route, "path", None) for route in app.routes}
    for endpoint in EXPECTED_ENDPOINTS.values():
        assert endpoint in route_paths


@given(st.sampled_from(sorted(PROOF_SURFACES)))
def test_surface_contract_is_stable_under_key_selection(key: str) -> None:
    payload = get_proof_surface(key)

    assert payload["endpoint"].startswith("/api/proofs/")
    assert payload["claim"].strip()
    assert payload["invariants"]
    assert payload["executable_commands"]
    assert payload["verification_chain"] == CLAIM_CHAIN
