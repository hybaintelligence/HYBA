"""Contract tests for HYBA executable proof windows."""

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
    "platform-overview": "/api/proofs/platform-overview",
    "intelligence-fabric": "/api/proofs/intelligence-fabric",
    "qaas": "/api/proofs/qaas",
    "ciaas": "/api/proofs/ciaas",
    "quantum-finance": "/api/proofs/quantum-finance",
    "commercial-access": "/api/proofs/commercial-access",
    "fair-governance": "/api/proofs/fair-governance",
    "regeneration": "/api/proofs/regeneration",
    "observability": "/api/proofs/observability",
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

EXPECTED_PLATFORM_DOMAINS = {
    "platform",
    "intelligence",
    "quantum_as_a_service",
    "computational_intelligence_as_a_service",
    "quantum_finance",
    "commercial",
    "fairness_governance",
    "salamander_regeneration",
    "observability",
    "verification",
    "mining",
    "autonomy",
    "pulvini_memory",
    "mathematical_runtime",
    "security",
    "evidence_governance",
    "runtime",
}

FORBIDDEN_POSTURE = (
    "trust andre",
    "trust the story",
    "trust the vision",
    "believe hyba",
    "nothing is unproven",
    "mining-only",
    "standalone product",
    "independent mini-system",
    "severable module",
)


def _assert_unified_platform(payload: dict) -> None:
    unity = payload["platform_unity"]
    assert unity["name"] == "HYBA_FULLSTACK"
    assert unity["unity"] == "one_non_severable_platform"
    assert unity["severability"] == "not_severable"
    assert "same HYBA_FULLSTACK platform substrate" in payload["projection_rule"]


def _assert_no_forbidden_posture(payload: dict) -> None:
    encoded = json.dumps(payload, sort_keys=True).lower()
    for forbidden in FORBIDDEN_POSTURE:
        assert forbidden not in encoded


def _assert_contract_payload(payload: dict) -> None:
    assert payload["claim"]
    assert payload["status"] in {"verified", "evidence_linked", "runtime_required"}
    assert payload["domain"]
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
    _assert_unified_platform(payload)
    _assert_no_forbidden_posture(payload)


def test_proof_surface_index_exposes_required_unified_platform_posture() -> None:
    index = list_proof_surfaces()

    assert index["surface_count"] >= len(EXPECTED_ENDPOINTS)
    assert index["verification_chain"] == CLAIM_CHAIN
    assert "Run the proof" in index["claim_boundary"]
    assert "Every material operational claim" in index["material_claim_standard"]
    assert index["platform_identity"]["unity"] == "one_non_severable_platform"
    assert index["platform_identity"]["severability"] == "not_severable"
    assert "one non-severable platform" in index["platform_boundary"]
    assert "verification windows into the same substrate" in index["platform_boundary"]
    assert set(index["domains"]) >= EXPECTED_PLATFORM_DOMAINS
    assert index["domain_count"] >= len(EXPECTED_PLATFORM_DOMAINS)
    _assert_no_forbidden_posture(index)

    endpoints = {surface["endpoint"] for surface in index["surfaces"]}
    for endpoint in EXPECTED_ENDPOINTS.values():
        assert endpoint in endpoints


def test_domains_are_dimensions_not_separate_platforms() -> None:
    index = list_proof_surfaces()
    domains = set(index["domains"])

    assert "mining" in domains
    assert "intelligence" in domains
    assert "quantum_as_a_service" in domains
    assert "computational_intelligence_as_a_service" in domains
    assert "commercial" in domains
    assert "observability" in domains
    assert len(domains - {"mining"}) >= 10
    assert all(
        surface["platform_unity"]["unity"] == "one_non_severable_platform"
        for surface in index["surfaces"]
    )


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
        "platform-overview": proofs.platform_overview_proof,
        "intelligence-fabric": proofs.intelligence_fabric_proof,
        "qaas": proofs.qaas_proof,
        "ciaas": proofs.ciaas_proof,
        "quantum-finance": proofs.quantum_finance_proof,
        "commercial-access": proofs.commercial_access_proof,
        "fair-governance": proofs.fair_governance_proof,
        "regeneration": proofs.regeneration_proof,
        "observability": proofs.observability_proof,
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


def test_audit_ledger_digest_covers_all_windows_and_preserves_platform_unity() -> None:
    ledger = build_runtime_evidence_ledger()

    assert ledger["ledger"] == "hyba_material_claim_verification_windows"
    assert ledger["status"] == "audit_ledger_available"
    assert ledger["surface_count"] == len(PROOF_SURFACES)
    assert ledger["domain_count"] >= len(EXPECTED_PLATFORM_DOMAINS)
    assert set(ledger["domains"]) >= EXPECTED_PLATFORM_DOMAINS
    assert ledger["platform_identity"]["unity"] == "one_non_severable_platform"
    assert "one non-severable platform" in ledger["platform_boundary"]
    assert len(ledger["head_hash"]) == 64
    assert {item["key"] for item in ledger["items"]} == set(PROOF_SURFACES)
    assert all(item["domain"] for item in ledger["items"])
    assert all(
        item["platform_unity"]["unity"] == "one_non_severable_platform"
        for item in ledger["items"]
    )
    _assert_no_forbidden_posture(ledger)


def test_fastapi_routes_are_wired() -> None:
    from hyba_genesis_api.main import app

    route_paths = {getattr(route, "path", None) for route in app.routes}
    for endpoint in EXPECTED_ENDPOINTS.values():
        assert endpoint in route_paths


@given(st.sampled_from(sorted(PROOF_SURFACES)))
def test_surface_contract_is_stable_under_key_selection(key: str) -> None:
    payload = get_proof_surface(key)

    assert payload["endpoint"].startswith("/api/proofs/")
    assert payload["domain"]
    assert payload["claim"].strip()
    assert payload["invariants"]
    assert payload["executable_commands"]
    assert payload["verification_chain"] == CLAIM_CHAIN
    _assert_unified_platform(payload)
