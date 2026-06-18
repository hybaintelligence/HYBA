"""Regenerative lobe API for operator-visible lane healing state."""

from __future__ import annotations

from dataclasses import asdict
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from hyba_genesis_api.api.regeneration_schema import (
    BlastemaState,
    FidelityEvent,
    RegenerativeStatus,
)
from pythia_mining.regeneration_manager import (
    RegenerationManager,
    get_regeneration_manager,
)

router = APIRouter(prefix="/api/organism/regeneration", tags=["organism-regeneration"])


@router.get("/status", response_model=RegenerativeStatus)
async def get_regen_status(
    manager: RegenerationManager = Depends(get_regeneration_manager),
) -> RegenerativeStatus:
    """Return aggregate regenerative health for the 32-lane manifold."""
    return RegenerativeStatus(**manager.get_status())


@router.get("/blastema", response_model=List[BlastemaState])
async def get_blastema_pool(
    manager: RegenerationManager = Depends(get_regeneration_manager),
) -> List[BlastemaState]:
    """View lane progenitor templates and role-model state."""
    return [BlastemaState(**lane) for lane in manager.get_blastema_pool()]


@router.post("/dedifferentiate/{lane_id}", response_model=FidelityEvent)
async def manual_regrow(
    lane_id: int,
    manager: RegenerationManager = Depends(get_regeneration_manager),
) -> FidelityEvent:
    """Operator-triggered regeneration of a single search lane."""
    try:
        event = await manager.trigger_regeneration(lane_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=423, detail=str(exc)) from exc
    return FidelityEvent(**asdict(event))


@router.get("/fidelity-report", response_model=List[FidelityEvent])
async def get_fidelity_history(
    manager: RegenerationManager = Depends(get_regeneration_manager),
) -> List[FidelityEvent]:
    """Return the in-process audit log of lane regeneration events."""
    return [FidelityEvent(**asdict(event)) for event in manager.fidelity_history]
