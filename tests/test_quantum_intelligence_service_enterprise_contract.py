"""Enterprise contract tests for the HYBA Quantum Intelligence API surface.

These tests intentionally validate the API source contract without importing the
full FastAPI application. That keeps the guard fast and prevents unrelated
runtime integrations from masking QIaaS product-boundary regressions.
"""

from __future__ import annotations

import ast
from pathlib import Path


QI_SERVICE = Path("python_backend/hyba_genesis_api/api/quantum_intelligence_service.py")


def _source() -> str:
    return QI_SERVICE.read_text(encoding="utf-8")


def test_quantum_intelligence_service_is_parseable_and_defines_evidence_envelope():
    source = _source()
    ast.parse(source)

    for symbol in (
        "class EvidencePacket",
        "class UsageMeter",
        "class TraceContext",
        "class QuantumIntelligenceEnvelope",
        "QIaaSResponse = QuantumIntelligenceEnvelope",
        "QI_CLAIM_BOUNDARY",
        "QI_PRODUCT_BOUNDARY",
    ):
        assert symbol in source


def test_quantum_intelligence_api_uses_shared_customer_gate_and_single_metering_path():
    source = _source()

    assert "require_customer_api_key" in source
    assert "customer_access.meter" in source
    assert "execute_with_billing" in source
    assert "async def require_qiaas_api_key" not in source
    assert "def meter_qiaas_usage" not in source
    assert "_fastapi" not in source


def test_quantum_intelligence_feature_gate_is_imported_and_enforced_on_customer_endpoints():
    source = _source()

    assert "from hyba_genesis_api.core.feature_flags import require_feature" in source
    assert source.count('require_feature("qiaas_enabled")') >= 4
    for endpoint in (
        '@router.post("/query"',
        '@router.get("/metrics"',
        '@router.get("/health"',
        '@router.post("/bootstrap"',
    ):
        assert endpoint in source


def test_quantum_intelligence_healing_is_event_loop_safe():
    source = _source()

    assert "async def heal" in source
    assert "await service.heal" in source
    assert "await self.regeneration_manager.trigger_regeneration" in source
    assert "asyncio.run" not in source
    assert "import asyncio" not in source


def test_quantum_intelligence_product_boundary_blocks_customer_visible_mining_surface():
    source = _source()

    banned_customer_surface_terms = (
        "Connect mining engine to create knowledge from successful shares",
        '"requires": "real_mining_operations"',
        "This would be called by the mining engine after successful shares",
        "hebbian_learning_from_outcomes",
    )
    for term in banned_customer_surface_terms:
        assert term not in source

    assert "not_mining_not_hardware_quantum" in source
    assert "private-validation data is never required" in source
    assert "evidence_sealed_substrate_bootstrap" in source


def test_quantum_intelligence_capabilities_are_enterprise_grade():
    source = _source()

    for capability in (
        '"predict"',
        '"explain"',
        '"optimize"',
        '"heal"',
        '"simulate"',
        '"counterfactual"',
        '"evidence"',
        '"quantum-finance"',
    ):
        assert capability in source

    assert (
        "Quantum Intelligence healing requires production or enterprise entitlement"
        in source
    )
    assert (
        "Quantum Intelligence bootstrap requires production or enterprise entitlement"
        in source
    )
    assert "sovereign_quantum_intelligence_execution" in source
