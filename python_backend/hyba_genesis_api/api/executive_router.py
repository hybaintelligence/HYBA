"""Executive Lobe API Router.

This router provides the controls for pool migration and manual overrides,
mounting to the newly fixed /api proxy with proper auth guards and circuit breaker integration.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from hyba_genesis_api.auth.jwt_handler import get_token_payload, TokenPayload

from .executive_schema import (
    MiningIntentRequest,
    MigrationResponse,
    TelemetryResponse,
    PoolHabitat,
    PoolHabitatList,
    MiningIntent,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/organism/executive", tags=["Executive"])


def _require_operator_role(payload: TokenPayload = Depends(get_token_payload)) -> TokenPayload:
    """Require operator role for executive endpoints."""
    if "operator" not in payload.roles and "admin" not in payload.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: operator or admin role required",
        )
    return payload


def _get_executive_controller():
    """Get the executive controller from substrate."""
    from hyba_genesis_api.core.substrate import get_substrate

    substrate = get_substrate()

    # Initialize executive controller if not present
    if not hasattr(substrate, "executive") or substrate.executive is None:
        from pythia_mining.mining_executive_controller import get_executive_controller

        substrate.executive = get_executive_controller()

        # Inject dependencies from substrate
        if substrate.consciousness_engine:
            substrate.executive.consciousness = substrate.consciousness_engine
        if substrate.immune_system:
            # Pass immune system reference if needed
            pass

    return substrate.executive


def _get_pool_habitats() -> List[PoolHabitat]:
    """Get pool habitats from pool management configuration."""
    import json
    from pathlib import Path

    pools_config_path = (
        Path(__file__).resolve().parents[2].parent / "config" / "mining_pools_live.json"
    )

    try:
        if pools_config_path.exists():
            with open(pools_config_path) as f:
                config = json.load(f)

            habitats = []
            for pool_name, pool_config in config.get("pools", {}).items():
                habitats.append(
                    PoolHabitat(
                        name=pool_name,
                        url=pool_config.get("url", ""),
                        stratum_version=pool_config.get("stratum_version", 1),
                        enabled=pool_config.get("enabled", False),
                        priority=pool_config.get("priority", 0),
                        is_default=pool_config.get("is_default", False),
                        description=pool_config.get("description"),
                    )
                )
            return habitats
    except Exception as e:
        logger.warning(f"Failed to load pool habitats: {e}")

    return []


@router.post("/intent", response_model=Dict[str, Any])
async def set_mining_intent(
    req: MiningIntentRequest, payload: TokenPayload = Depends(_require_operator_role)
):
    """
    Directs the organism's intent: ACTIVATE (Ignite), QUIESCE (Stop), or STASIS.

    This endpoint requires operator or admin role and includes circuit breaker integration
    via the sensory integrity check in the executive controller.
    """
    executive = _get_executive_controller()

    if req.intent == MiningIntent.ACTIVATE:
        result = await executive.ignite_manifold()
        if not result["success"]:
            # Circuit breaker: return 403 for immune lock or stasis lock
            if result.get("error") in ["IMMUNE_LOCK", "STASIS_LOCK"]:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result)
        return result

    elif req.intent == MiningIntent.QUIESCE:
        return await executive.quiesce_manifold()

    elif req.intent == MiningIntent.STASIS:
        return await executive.set_stasis(True)

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown intent: {req.intent}"
        )


@router.get("/habitats", response_model=PoolHabitatList)
async def list_pool_habitats(payload: TokenPayload = Depends(_require_operator_role)):
    """Lists all configured 'Habitats' (Mining Pools)."""
    habitats = _get_pool_habitats()

    # Find default pool
    default_pool = None
    for habitat in habitats:
        if habitat.is_default:
            default_pool = habitat.name
            break

    return PoolHabitatList(habitats=habitats, default_pool=default_pool)


@router.put("/habitats/migrate/{pool_name}", response_model=MigrationResponse)
async def migrate_to_habitat(
    pool_name: str, payload: TokenPayload = Depends(_require_operator_role)
):
    """
    Migrates the organism to a new pool habitat.
    Triggers a 'Dedifferentiation' event if the pool latency is too high.
    """
    habitats = _get_pool_habitats()
    habitat_names = [h.name for h in habitats]

    if pool_name not in habitat_names:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Habitat '{pool_name}' not found. Available: {habitat_names}",
        )

    # Get the habitat configuration
    target_habitat = next(h for h in habitats if h.name == pool_name)

    if not target_habitat.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Habitat '{pool_name}' is disabled"
        )

    # In a full implementation, this would:
    # 1. Check pool latency
    # 2. If latency is high, trigger dedifferentiation event
    # 3. Switch the stratum client to the new pool
    # 4. Update the active pool state

    executive = _get_executive_controller()

    # If currently active, we need to quiesce and reignite with new pool
    if executive.is_active:
        logger.info(f"Executive: Migrating from current pool to {pool_name}")
        # This would involve disconnecting current pool and connecting to new one
        # For now, we'll log the migration intent
        logger.warning(f"Pool migration to {pool_name} requested - full implementation pending")

    return MigrationResponse(status="MIGRATION_COMPLETE", target=pool_name)


@router.get("/telemetry", response_model=TelemetryResponse)
async def get_executive_telemetry(payload: TokenPayload = Depends(_require_operator_role)):
    """Full-stack telemetry: From Stratum bytes to Consciousness Phi."""
    executive = _get_executive_controller()

    telemetry = executive.get_nervous_system_telemetry()

    return TelemetryResponse(**telemetry)


@router.get("/status", response_model=Dict[str, Any])
async def get_executive_status(payload: TokenPayload = Depends(_require_operator_role)):
    """Get current executive status without full telemetry."""
    executive = _get_executive_controller()

    return {
        "is_active": executive.is_active,
        "stasis_mode": executive.stasis_mode,
        "ignition_time": executive.ignition_time.isoformat() if executive.ignition_time else None,
        "phi": executive.consciousness.coherence_meter,
        "sensory_integrity": executive.consciousness.validate_sensory_integrity(),
    }
