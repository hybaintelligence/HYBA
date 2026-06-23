"""
Production Mining API - Real Pool Integration & Live Operations

Provides endpoints for:
- Real pool management and failover
- Live share submission
- Mining status and health monitoring
- Pool performance metrics
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status

from pythia_mining.production_mining_gateway import (
    MiningGatewayError,
    PoolConfigurationError,
    get_gateway,
)

router = APIRouter(prefix="/api/v1/mining-production", tags=["mining_production"])
logger = logging.getLogger(__name__)


@router.post("/initialize", status_code=status.HTTP_200_OK)
async def initialize_production_mining() -> Dict[str, Any]:
    """
    Initialize production mining with pool configuration from environment.

    Expects environment variables:
    - HYBA_POOL_1_NAME, HYBA_POOL_1_URL, HYBA_POOL_1_USERNAME, HYBA_POOL_1_PASSWORD
    - HYBA_POOL_2_NAME, etc. (for additional pools)

    Or: HYBA_MINING_POOLS_JSON with JSON array of pool configs
    """
    try:
        gateway = get_gateway()

        if gateway.is_initialized:
            return {
                "status": "already_initialized",
                "message": "Mining gateway is already initialized",
                "health": gateway.get_status(),
            }

        await gateway.initialize()

        return {
            "status": "initialized",
            "message": "Mining gateway initialized successfully",
            "health": gateway.get_status(),
        }

    except PoolConfigurationError as e:
        logger.error(f"Pool configuration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pool configuration error: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Failed to initialize mining gateway: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Initialization failed: {str(e)}",
        )


@router.post("/start", status_code=status.HTTP_200_OK)
async def start_production_mining() -> Dict[str, Any]:
    """Start production mining operations."""
    try:
        gateway = get_gateway()

        if not gateway.is_initialized:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mining gateway must be initialized first",
            )

        await gateway.start()

        return {
            "status": "started",
            "message": "Mining operations started",
            "health": gateway.get_status(),
        }

    except MiningGatewayError as e:
        logger.error(f"Mining gateway error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to start mining: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Start failed: {str(e)}",
        )


@router.post("/stop", status_code=status.HTTP_200_OK)
async def stop_production_mining() -> Dict[str, Any]:
    """Stop production mining operations."""
    try:
        gateway = get_gateway()
        await gateway.stop()

        return {
            "status": "stopped",
            "message": "Mining operations stopped",
            "health": gateway.get_status(),
        }

    except Exception as e:
        logger.error(f"Failed to stop mining: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stop failed: {str(e)}",
        )


@router.get("/status", status_code=status.HTTP_200_OK)
async def get_mining_status() -> Dict[str, Any]:
    """Get current mining status and pool health."""
    try:
        gateway = get_gateway()
        return gateway.get_status()
    except Exception as e:
        logger.error(f"Failed to get mining status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status retrieval failed: {str(e)}",
        )


@router.get("/health", status_code=status.HTTP_200_OK)
async def get_pool_health(pool_id: str | None = None) -> Dict[str, Any]:
    """
    Get pool health status.

    Query params:
    - pool_id: Optional specific pool ID (returns all if not provided)
    """
    try:
        gateway = get_gateway()
        health = gateway.get_pool_health(pool_id)

        if pool_id and not health:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pool {pool_id} not found",
            )

        return {
            "pool_health": health,
            "timestamp": None,  # Will be set by middleware
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pool health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}",
        )


@router.post("/submit-share", status_code=status.HTTP_200_OK)
async def submit_mining_share(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Submit a mining share to the pool.

    Request body:
    ```json
    {
        "job_id": "job_12345",
        "nonce": <computed_nonce>,
        "extranonce2": "00000001" (optional)
    }
    ```
    """
    try:
        gateway = get_gateway()

        if not gateway.is_running:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mining gateway is not running",
            )

        job_id = payload.get("job_id")
        nonce = payload.get("nonce")
        extranonce2 = payload.get("extranonce2")

        if not job_id or nonce is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="job_id and nonce are required",
            )

        # For this endpoint, we need to get the actual job from the orchestrator
        # This is a simplified version - in production, the job would come from the mining loop
        accepted = await gateway.submit_share(None, nonce, extranonce2)

        return {
            "accepted": accepted,
            "message": (
                "Share submitted successfully" if accepted else "Share was rejected"
            ),
        }

    except HTTPException:
        raise
    except MiningGatewayError as e:
        logger.error(f"Mining gateway error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to submit share: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Share submission failed: {str(e)}",
        )


@router.get("/metrics", status_code=status.HTTP_200_OK)
async def get_mining_metrics() -> Dict[str, Any]:
    """Get detailed mining metrics and statistics."""
    try:
        gateway = get_gateway()
        status_dict = gateway.get_status()

        if "stats" in status_dict:
            return {
                "metrics": status_dict["stats"],
                "pools": status_dict.get("pools", {}),
            }

        return {
            "metrics": None,
            "message": "Mining gateway not initialized",
        }

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metrics retrieval failed: {str(e)}",
        )


@router.get("/next-job", status_code=status.HTTP_200_OK)
async def get_next_mining_job() -> Dict[str, Any]:
    """Get next available mining job from pools."""
    try:
        gateway = get_gateway()

        if not gateway.is_running:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mining gateway is not running",
            )

        job = await gateway.get_next_job()

        if job:
            return {
                "job_available": True,
                "job": {
                    "job_id": getattr(job, "job_id", None),
                    "prevhash": getattr(job, "prevhash", None),
                    "version": getattr(job, "version", None),
                    "nbits": getattr(job, "nbits", None),
                    "ntime": getattr(job, "ntime", None),
                    "clean_jobs": False,
                },
            }

        return {
            "job_available": False,
            "message": "No job available at this time",
        }

    except HTTPException:
        raise
    except MiningGatewayError as e:
        logger.error(f"Mining gateway error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to get next job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job retrieval failed: {str(e)}",
        )


__all__ = ["router"]
