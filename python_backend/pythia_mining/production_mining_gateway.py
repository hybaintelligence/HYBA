"""
Production Mining Gateway - Real Pool Integration & Deployment Validation

Validates pool configurations, manages connection lifecycle, and ensures
production-ready mining operations with comprehensive observability.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from pythia_mining.production_mining_orchestrator import (
    MiningStrategy,
    ProductionMiningOrchestrator,
)
from pythia_mining.pool_profiles import PoolProfile, build_profile
from pythia_mining.stratum_client import AllPoolsOfflineError


class MiningGatewayError(RuntimeError):
    """Base error for mining gateway operations."""

    pass


class PoolConfigurationError(MiningGatewayError):
    """Raised when pool configuration is invalid."""

    pass


class ProductionMiningGateway:
    """
    Enterprise mining gateway managing the complete lifecycle of mining
    operations including pool management, share submission, and monitoring.
    """

    def __init__(self):
        self.orchestrator: Optional[ProductionMiningOrchestrator] = None
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
        self.is_running = False

    @staticmethod
    def build_profiles_from_env() -> List[PoolProfile]:
        """
        Build pool profiles from environment variables.

        Expected environment variables:
        - HYBA_POOL_1_NAME, HYBA_POOL_1_URL, HYBA_POOL_1_USERNAME, HYBA_POOL_1_PASSWORD
        - HYBA_POOL_2_NAME, HYBA_POOL_2_URL, HYBA_POOL_2_USERNAME, HYBA_POOL_2_PASSWORD
        - etc.

        Or use HYBA_MINING_POOLS_JSON for JSON config array.
        """
        profiles: List[PoolProfile] = []

        # Check for JSON config first
        json_config = os.getenv("HYBA_MINING_POOLS_JSON")
        if json_config:
            import json

            try:
                pools_config = json.loads(json_config)
                for i, pool_cfg in enumerate(pools_config, 1):
                    try:
                        profile = build_profile(
                            f"pool_{i}",
                            name=pool_cfg.get("name", f"Pool {i}"),
                            url=pool_cfg.get("url", ""),
                            username=pool_cfg.get("username", ""),
                            password=pool_cfg.get("password", ""),
                            stratum_version=pool_cfg.get("stratum_version", 1),
                            priority=pool_cfg.get("priority", 100 - i),
                            tls_required=pool_cfg.get("tls_required", False),
                        )
                        profiles.append(profile)
                    except Exception as e:
                        logging.warning(f"Failed to build pool {i} from JSON config: {e}")
                return profiles
            except json.JSONDecodeError as e:
                logging.warning(f"Invalid JSON in HYBA_MINING_POOLS_JSON: {e}")

        # Fall back to environment variable pattern
        pool_index = 1
        while True:
            name = os.getenv(f"HYBA_POOL_{pool_index}_NAME")
            if not name:
                break

            url = os.getenv(f"HYBA_POOL_{pool_index}_URL", "")
            username = os.getenv(f"HYBA_POOL_{pool_index}_USERNAME", "")
            password = os.getenv(f"HYBA_POOL_{pool_index}_PASSWORD", "")
            stratum_version = int(os.getenv(f"HYBA_POOL_{pool_index}_STRATUM_VERSION", "1"))
            priority = int(os.getenv(f"HYBA_POOL_{pool_index}_PRIORITY", str(100 - pool_index)))
            tls_required = (
                os.getenv(f"HYBA_POOL_{pool_index}_TLS_REQUIRED", "false").lower() == "true"
            )

            try:
                profile = build_profile(
                    f"pool_{pool_index}",
                    name=name,
                    url=url,
                    username=username,
                    password=password,
                    stratum_version=stratum_version,
                    priority=priority,
                    tls_required=tls_required,
                )
                profiles.append(profile)
            except Exception as e:
                logging.warning(f"Failed to build pool {pool_index} from env: {e}")

            pool_index += 1

        return profiles

    @staticmethod
    def validate_profiles(profiles: List[PoolProfile]) -> None:
        """Validate pool profiles for production readiness."""
        if not profiles:
            raise PoolConfigurationError("At least one pool profile is required")

        for profile in profiles:
            if not profile.url or not profile.username:
                raise PoolConfigurationError(f"Pool {profile.name} is missing url or username")

            # Validate URL format
            if not profile.url.startswith(
                (
                    "stratum://",
                    "stratum+ssl://",
                    "stratum+tls://",
                    "stratum2://",
                    "stratum2+ssl://",
                    "stratum2+tls://",
                )
            ):
                raise PoolConfigurationError(
                    f"Pool {profile.name} has invalid URL scheme: {profile.url}"
                )

            # Validate Stratum version
            if profile.stratum_version not in (1, 2):
                raise PoolConfigurationError(
                    f"Pool {profile.name} has invalid Stratum version: {profile.stratum_version}"
                )

    async def initialize(
        self,
        profiles: Optional[List[PoolProfile]] = None,
        mining_strategy: MiningStrategy = MiningStrategy.FAILOVER,
    ) -> None:
        """
        Initialize the mining gateway.

        Args:
            profiles: Pool profiles (uses env vars if not provided)
            mining_strategy: Share submission strategy

        Raises:
            PoolConfigurationError: If configuration is invalid
            AllPoolsOfflineError: If no pools can be connected
        """
        if self.is_initialized:
            raise MiningGatewayError("Gateway is already initialized")

        # Build profiles from environment if not provided
        if profiles is None:
            profiles = self.build_profiles_from_env()

        # Validate profiles
        self.validate_profiles(profiles)

        self.logger.info(f"Initializing mining gateway with {len(profiles)} pools")

        try:
            # Create orchestrator
            self.orchestrator = ProductionMiningOrchestrator(
                profiles=profiles,
                mining_strategy=mining_strategy,
                health_check_interval=30.0,
            )

            # Initialize connections
            await self.orchestrator.initialize()
            self.is_initialized = True

            self.logger.info("Mining gateway initialized successfully")

        except AllPoolsOfflineError:
            self.logger.error("Failed to initialize: all pools are offline")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize gateway: {e}")
            raise MiningGatewayError(f"Initialization failed: {e}")

    async def start(self) -> None:
        """Start mining operations."""
        if not self.is_initialized or not self.orchestrator:
            raise MiningGatewayError("Gateway must be initialized first")

        if self.is_running:
            return

        self.logger.info("Starting mining gateway")
        await self.orchestrator.start()
        self.is_running = True

    async def stop(self) -> None:
        """Stop mining operations."""
        if not self.is_running or not self.orchestrator:
            return

        self.logger.info("Stopping mining gateway")
        await self.orchestrator.stop()
        self.is_running = False

    async def submit_share(self, job: Any, nonce: int, extranonce2: Optional[str] = None) -> bool:
        """
        Submit a mining share.

        Args:
            job: Mining job from get_next_job()
            nonce: Nonce value
            extranonce2: Optional extranonce2 override

        Returns:
            True if share was accepted by at least one pool
        """
        if not self.is_running or not self.orchestrator:
            raise MiningGatewayError("Gateway is not running")

        results = await self.orchestrator.submit_share(job, nonce, extranonce2)
        return any(result.accepted for result in results)

    async def get_next_job(self) -> Optional[Any]:
        """Get next available mining job."""
        if not self.is_running or not self.orchestrator:
            raise MiningGatewayError("Gateway is not running")

        return await self.orchestrator.get_next_job()

    def get_status(self) -> Dict[str, Any]:
        """Get gateway status."""
        if not self.orchestrator:
            return {
                "initialized": False,
                "running": False,
                "status": "not_initialized",
            }

        stats = self.orchestrator.get_mining_stats()
        health_status = self.orchestrator.get_pool_health_status()

        # Determine overall status
        if stats.healthy_pools > 0:
            overall_status = "healthy"
        elif stats.degraded_pools > 0:
            overall_status = "degraded"
        elif stats.offline_pools < stats.total_pools:
            overall_status = "unhealthy"
        else:
            overall_status = "offline"

        return {
            "initialized": self.is_initialized,
            "running": self.is_running,
            "status": overall_status,
            "stats": stats.to_dict(),
            "pools": health_status,
        }

    def get_pool_health(self, pool_id: Optional[str] = None) -> Dict[str, Any]:
        """Get pool health status."""
        if not self.orchestrator:
            return {}

        return self.orchestrator.get_pool_health_status(pool_id)


# Global gateway instance
_gateway: Optional[ProductionMiningGateway] = None


def get_gateway() -> ProductionMiningGateway:
    """Get or create the global mining gateway."""
    global _gateway
    if _gateway is None:
        _gateway = ProductionMiningGateway()
    return _gateway


__all__ = [
    "MiningGatewayError",
    "PoolConfigurationError",
    "ProductionMiningGateway",
    "get_gateway",
]
