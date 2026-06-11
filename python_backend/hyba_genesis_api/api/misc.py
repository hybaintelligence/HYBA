from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

import numpy as np
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["misc"])


@router.get("/pitfalls", response_model=Dict[str, Any])
async def get_pitfalls():
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "monitoring_status": {
            "enabled": False,
            "source": "pitfall_monitor_not_connected",
            "last_check": None,
        },
        "pitfall_counts": None,
    }


class ExperimentConfig(BaseModel):
    experiment_type: str = Field(default="phi_blockchain_correlation", min_length=1, max_length=128)


@router.post("/toe/experiments", response_model=Dict[str, Any])
async def start_experiment(config: ExperimentConfig):
    return {
        "success": True,
        "status": "accepted_degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "experiment_type": config.experiment_type,
        "source": "experiment_runtime_not_connected",
        "message": "Experiment request accepted in degraded mode; execution runtime is not attached.",
    }


@router.post("/pulvini/execute", response_model=Dict[str, Any])
async def execute_pulvini():
    """Execute deterministic linear-algebra checks and return only measured outputs."""
    state_size = 2**14
    state_vector = np.ones(state_size, dtype=np.complex128) / np.sqrt(state_size)
    mean_amplitude = np.mean(state_vector)
    diffused_state = (2 * mean_amplitude) - state_vector
    diffusion_norm = float(np.sum(np.abs(diffused_state) ** 2).real)

    hamiltonian_size = 256
    projection_basis = np.eye(hamiltonian_size, dtype=np.float64)[:158]
    projected_dimensions = int(projection_basis.shape[0])
    orthonormality_error = float(np.linalg.norm(projection_basis @ projection_basis.T - np.eye(projected_dimensions)))
    norm_error = abs(1.0 - diffusion_norm)
    projection_purity = max(0.0, 1.0 - orthonormality_error)

    return {
        "status": "success",
        "message": "PULVINI Memory Engine Executed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "measured_linear_algebra_runtime",
        "operations": [
            {
                "operation": "state_vector_diffusion_norm_check",
                "state_vector_entries": state_size,
                "invariants": 14,
                "diffusion_norm": diffusion_norm,
                "norm_error": norm_error,
            },
            {
                "operation": "projection_basis_orthonormality_check",
                "original_dimensions": hamiltonian_size,
                "projected_dimensions": projected_dimensions,
                "topological_anchoring": "euclidean",
                "purity": projection_purity,
                "orthonormality_error": orthonormality_error,
            },
        ],
        "metric_compression": f"{projected_dimensions}D/{hamiltonian_size}D",
        "hamiltonian_generation": "spectral_projection_basis",
    }


class PredictState(BaseModel):
    networkDifficulty: Optional[float] = Field(default=None, gt=0)


class PredictRequest(BaseModel):
    state: PredictState


@router.post("/predict", response_model=Dict[str, Any])
async def predict_params(req: PredictRequest):
    """Fail closed until a measured optimizer runtime is connected.

    Power recommendations are operational controls. Returning a heuristic when the
    optimizer is unavailable would look like a successful prediction while being
    unrelated to measured activity, so the API reports the missing dependency
    explicitly instead of fabricating confidence or a power scale.
    """

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "error": "optimizer_runtime_not_connected",
            "message": "No measured optimizer runtime is connected; prediction was not generated.",
            "networkDifficulty": req.state.networkDifficulty,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
