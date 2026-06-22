"""API-level proof endpoints for executable verification surfaces."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from hyba_genesis_api.core.proof_surfaces import (
    build_runtime_evidence_ledger,
    get_proof_surface,
    list_proof_surfaces,
)

router = APIRouter(prefix="/api/proofs", tags=["proofs"])


@router.get("", response_model=Dict[str, Any])
async def proof_surface_index() -> Dict[str, Any]:
    """Return all executable verification surfaces and their evidence links."""

    return list_proof_surfaces()


@router.get("/platform-overview", response_model=Dict[str, Any])
async def platform_overview_proof() -> Dict[str, Any]:
    """Return the full-platform proof overview surface."""

    return get_proof_surface("platform-overview")


@router.get("/intelligence-fabric", response_model=Dict[str, Any])
async def intelligence_fabric_proof() -> Dict[str, Any]:
    """Return the intelligence-fabric proof surface."""

    return get_proof_surface("intelligence-fabric")


@router.get("/qaas", response_model=Dict[str, Any])
async def qaas_proof() -> Dict[str, Any]:
    """Return the QaaS product proof surface."""

    return get_proof_surface("qaas")


@router.get("/ciaas", response_model=Dict[str, Any])
async def ciaas_proof() -> Dict[str, Any]:
    """Return the CIaaS product proof surface."""

    return get_proof_surface("ciaas")


@router.get("/quantum-finance", response_model=Dict[str, Any])
async def quantum_finance_proof() -> Dict[str, Any]:
    """Return the quantum-finance proof surface."""

    return get_proof_surface("quantum-finance")


@router.get("/commercial-access", response_model=Dict[str, Any])
async def commercial_access_proof() -> Dict[str, Any]:
    """Return the commercial access proof surface."""

    return get_proof_surface("commercial-access")


@router.get("/fair-governance", response_model=Dict[str, Any])
async def fair_governance_proof() -> Dict[str, Any]:
    """Return the fair-governance proof surface."""

    return get_proof_surface("fair-governance")


@router.get("/regeneration", response_model=Dict[str, Any])
async def regeneration_proof() -> Dict[str, Any]:
    """Return the Salamander/regeneration proof surface."""

    return get_proof_surface("regeneration")


@router.get("/observability", response_model=Dict[str, Any])
async def observability_proof() -> Dict[str, Any]:
    """Return the observability proof surface."""

    return get_proof_surface("observability")


@router.get("/property-tests", response_model=Dict[str, Any])
async def property_tests_proof() -> Dict[str, Any]:
    """Return the property-test proof surface."""

    return get_proof_surface("property-tests")


@router.get("/adversarial", response_model=Dict[str, Any])
async def adversarial_proof() -> Dict[str, Any]:
    """Return the adversarial-boundary proof surface."""

    return get_proof_surface("adversarial")


@router.get("/invariants", response_model=Dict[str, Any])
async def invariants_proof() -> Dict[str, Any]:
    """Return the invariant proof surface."""

    return get_proof_surface("invariants")


@router.get("/mining-readiness", response_model=Dict[str, Any])
async def mining_readiness_proof() -> Dict[str, Any]:
    """Return the mining-readiness proof surface."""

    return get_proof_surface("mining-readiness")


@router.get("/autonomy", response_model=Dict[str, Any])
async def autonomy_proof() -> Dict[str, Any]:
    """Return the bounded-autonomy proof surface."""

    return get_proof_surface("autonomy")


@router.get("/memory-compression", response_model=Dict[str, Any])
async def memory_compression_proof() -> Dict[str, Any]:
    """Return the PULVINI memory-compression proof surface."""

    return get_proof_surface("memory-compression")


@router.get("/phi-scaling", response_model=Dict[str, Any])
async def phi_scaling_proof() -> Dict[str, Any]:
    """Return the φ-scaling proof surface."""

    return get_proof_surface("phi-scaling")


@router.get("/security", response_model=Dict[str, Any])
async def security_proof() -> Dict[str, Any]:
    """Return the security proof surface."""

    return get_proof_surface("security")


@router.get("/audit-ledger", response_model=Dict[str, Any])
async def audit_ledger_proof() -> Dict[str, Any]:
    """Return the cross-claim evidence ledger."""

    return build_runtime_evidence_ledger()


@router.get("/runtime-evidence", response_model=Dict[str, Any])
async def runtime_evidence_proof() -> Dict[str, Any]:
    """Return the runtime-evidence proof surface."""

    return get_proof_surface("runtime-evidence")


@router.get("/{surface_key}", response_model=Dict[str, Any])
async def proof_surface_by_key(surface_key: str) -> Dict[str, Any]:
    """Return any registered proof surface by key for programmatic interrogation."""

    try:
        return get_proof_surface(surface_key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
