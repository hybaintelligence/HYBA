from __future__ import annotations

from pythia_finance_audit.advanced_capability_map import (
    BOUNDARY_STATEMENT,
    capability_ids,
    list_advanced_finance_capabilities,
    prohibited_terms,
    validate_advanced_capability_boundaries,
)


def test_advanced_finance_capabilities_cover_core_hyba_substrates() -> None:
    ids = set(capability_ids())

    assert "PULVINI_PORTFOLIO_EVIDENCE_COMPRESSION" in ids
    assert "QUANTUM_STYLE_SCENARIO_SEARCH" in ids
    assert "PHI_SCALING_GOVERNANCE_SCHEDULER" in ids
    assert "AI_MEMORY_MODEL_RISK_TRACE" in ids
    assert "INTELLIGENCE_FABRIC_CONTROL_ROOM" in ids
    assert "MILLENNIUM_STYLE_PROOF_OBLIGATION_ENGINE" in ids


def test_advanced_finance_capabilities_preserve_no_authority_boundary() -> None:
    report = validate_advanced_capability_boundaries()

    assert report["valid"] is True
    assert report["violations"] == []
    assert report["capability_count"] >= 6
    assert "must not be exposed as autonomous finance authority" in BOUNDARY_STATEMENT


def test_advanced_finance_capabilities_are_evidence_products_not_execution_products() -> (
    None
):
    capabilities = list_advanced_finance_capabilities()
    forbidden = prohibited_terms()

    for capability in capabilities:
        assert capability["human_owner"]
        assert capability["evidence_required"]
        permitted_outputs = " | ".join(capability["permitted_outputs"]).lower()
        prohibited_outputs = " | ".join(capability["prohibited_outputs"]).lower()
        for term in forbidden:
            assert term not in permitted_outputs
        assert any(
            marker in prohibited_outputs
            for marker in ("approval", "execution", "conclusion", "capital calculation")
        )
