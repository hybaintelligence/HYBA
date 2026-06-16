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
    orthonormality_error = float(
        np.linalg.norm(projection_basis @ projection_basis.T - np.eye(projected_dimensions))
    )
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
    """Generate power and strategy predictions from live optimizer measurements.

    Power recommendations are operational controls. This endpoint returns predictions
    only when a measured optimizer runtime is connected. When unavailable, it reports
    the missing dependency explicitly rather than fabricating confidence or power scale.
    """
    
    try:
        from pythia_mining.genesis_ai_service import GenesisAIServiceRegistry
        
        optimizer = GenesisAIServiceRegistry.get_ai_optimizer()
        
        if optimizer is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "optimizer_runtime_not_connected",
                    "message": "No measured optimizer runtime is connected; prediction was not generated.",
                    "networkDifficulty": req.state.networkDifficulty,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        
        # Get current optimizer state and meta-learning snapshot
        meta_snapshot = optimizer.meta_learning_snapshot()
        strategy_probs = meta_snapshot.get("strategy_probabilities", {})
        recent_performance = meta_snapshot.get("recent_performance", [])
        
        # Calculate recommendation based on measured optimizer state
        recommended_strategy = max(strategy_probs.items(), key=lambda x: x[1])[0] if strategy_probs else "phi_scaled_compressed_solver_search"
        
        # Derive power scale recommendation from recent performance
        recent_accepted = [p for p in recent_performance[-10:] if p.get("accepted", False)]
        acceptance_rate = len(recent_accepted) / max(1, len(recent_performance[-10:]))
        
        # Conservative power scaling based on acceptance rate
        if acceptance_rate > 0.7:
            recommended_power_scale = 1.0  # Stable
        elif acceptance_rate > 0.4:
            recommended_power_scale = 1.1  # Slight increase
        else:
            recommended_power_scale = 1.2  # Increase exploration
        
        # Calculate confidence from strategy entropy
        if strategy_probs:
            strategy_values = list(strategy_probs.values())
            entropy = -sum(p * np.log(p + 1e-12) for p in strategy_values if p > 0)
            max_entropy = np.log(len(strategy_probs))
            confidence = 1.0 - (entropy / max(max_entropy, 1e-12))
        else:
            confidence = 0.0
        
        return {
            "success": True,
            "status": "predicted",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "measured_optimizer_runtime",
            "networkDifficulty": req.state.networkDifficulty,
            "recommendation": {
                "strategy": recommended_strategy,
                "power_scale": recommended_power_scale,
                "confidence": float(confidence),
            },
            "optimizer_state": {
                "acceptance_rate": float(acceptance_rate),
                "strategy_probabilities": strategy_probs,
                "recent_performance_samples": len(recent_performance),
            },
        }
        
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "optimizer_module_not_available",
                "message": "Optimizer module is not available in this environment.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
