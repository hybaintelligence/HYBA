"""
Admin Observability & Telemetry Router for QaaS/CIaaS Monitoring

Provides Redis-backed telemetry aggregation for:
- Tenant resource usage tracking across all instances
- Instance health monitoring and execution metrics
- System-wide compute unit consumption analysis
- Distributed state health diagnostics
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from hyba_genesis_api.api.admin import require_admin
from hyba_genesis_api.auth.jwt_handler import TokenPayload
from pythia_mining.redis_state_registry import get_redis_registry

router = APIRouter(prefix="/api/admin/observability", tags=["observability"])


class TenantUsageResponse(BaseModel):
    tenant_id: str
    total_compute_units: float
    total_execution_cycles: int
    instances_count: int


class SystemHealthResponse(BaseModel):
    redis_available: bool
    redis_host: str
    redis_port: int
    total_tenants_tracked: int
    total_instances_tracked: int


class InstanceTelemetryResponse(BaseModel):
    instance_id: str
    total_execution_cycles: int
    last_updated: str
    redis_backed: bool


@router.get("/tenants/{tenant_id}/usage", response_model=TenantUsageResponse)
async def get_tenant_resource_usage(
    tenant_id: str,
    payload: TokenPayload = Depends(require_admin),
):
    """
    Retrieve aggregated resource usage for a specific tenant across all instances.

    Returns:
        - total_compute_units: Cumulative compute units consumed
        - total_execution_cycles: Number of workloads executed
        - instances_count: Number of active/stopped instances
    """
    redis_registry = get_redis_registry()

    if not redis_registry.available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis telemetry backend unavailable; usage tracking disabled",
        )

    usage = redis_registry.get_tenant_usage(tenant_id)

    # Count instances for this tenant (would require scanning keys in production)
    # For now, return 0 as a placeholder
    instances_count = 0

    return TenantUsageResponse(
        tenant_id=tenant_id,
        total_compute_units=usage["total_compute_units"],
        total_execution_cycles=usage["total_execution_cycles"],
        instances_count=instances_count,
    )


@router.get("/system/health", response_model=SystemHealthResponse)
async def get_system_health(
    payload: TokenPayload = Depends(require_admin),
):
    """
    Retrieve system-wide health metrics for distributed state infrastructure.

    Returns:
        - redis_available: Whether Redis is connected
        - redis_host/port: Connection details
        - total_tenants_tracked: Number of tenants with usage data
        - total_instances_tracked: Number of instances with topology state
    """
    redis_registry = get_redis_registry()

    # In production, these would scan Redis keys with SCAN command
    total_tenants = 0
    total_instances = 0

    return SystemHealthResponse(
        redis_available=redis_registry.available,
        redis_host=redis_registry.host,
        redis_port=redis_registry.port,
        total_tenants_tracked=total_tenants,
        total_instances_tracked=total_instances,
    )


@router.get(
    "/instances/{instance_id}/telemetry", response_model=InstanceTelemetryResponse
)
async def get_instance_telemetry(
    instance_id: str,
    payload: TokenPayload = Depends(require_admin),
):
    """
    Retrieve execution telemetry for a specific QaaS/CIaaS instance.

    Returns:
        - total_execution_cycles: Number of workloads executed
        - last_updated: Timestamp of last topology update
        - redis_backed: Whether instance state is persisted to Redis
    """
    redis_registry = get_redis_registry()

    if not redis_registry.available:
        return InstanceTelemetryResponse(
            instance_id=instance_id,
            total_execution_cycles=0,
            last_updated="unknown",
            redis_backed=False,
        )

    topology = redis_registry.get_instance_topology(instance_id)

    if not topology:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instance not found in distributed state registry",
        )

    return InstanceTelemetryResponse(
        instance_id=instance_id,
        total_execution_cycles=topology.get(
            "executions", topology.get("workload_count", 0)
        ),
        last_updated=topology.get("updated_at", "unknown"),
        redis_backed=True,
    )


@router.delete("/instances/{instance_id}")
async def delete_instance_state(
    instance_id: str,
    payload: TokenPayload = Depends(require_admin),
):
    """
    Delete instance topology and telemetry from distributed state.

    This removes:
    - Instance topology metadata
    - Distributed execution locks
    - Instance-level metering counters

    Note: Does not delete tenant-level usage aggregates.
    """
    redis_registry = get_redis_registry()

    if not redis_registry.available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis backend unavailable; cannot delete distributed state",
        )

    success = redis_registry.delete_instance(instance_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete instance state from Redis",
        )

    return {"status": "deleted", "instance_id": instance_id}
