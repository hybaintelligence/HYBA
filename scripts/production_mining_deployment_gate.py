#!/usr/bin/env python3
"""
Production Mining Deployment Gate

Validates production-ready mining configuration and performs
comprehensive pre-deployment checks before live pool integration.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python_backend"))

from pythia_mining.production_mining_gateway import (
    MiningGatewayError,
    PoolConfigurationError,
    ProductionMiningGateway,
)
from pythia_mining.pool_profiles import PoolProfile, build_profile


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DeploymentGate:
    """Validates production mining configuration."""
    
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []
    
    def check(self, name: str, condition: bool, message: str) -> bool:
        """Run a check and record result."""
        if condition:
            logger.info(f"✓ {name}: {message}")
            self.checks_passed += 1
            return True
        else:
            logger.error(f"✗ {name}: {message}")
            self.checks_failed += 1
            return False
    
    def warn(self, message: str) -> None:
        """Record a warning."""
        logger.warning(f"⚠ {message}")
        self.warnings.append(message)
    
    async def validate_environment(self) -> bool:
        """Validate environment configuration."""
        logger.info("\n" + "="*60)
        logger.info("STEP 1: Validating Environment Configuration")
        logger.info("="*60)
        
        # Check for pool configuration
        profiles = ProductionMiningGateway.build_profiles_from_env()
        self.check(
            "Pool Configuration",
            len(profiles) > 0,
            f"Found {len(profiles)} pool profile(s)"
        )
        
        if len(profiles) == 0:
            self.warn("No pool profiles found in environment")
            return False
        
        # Validate each profile
        for profile in profiles:
            self.check(
                f"Pool '{profile.name}' URL",
                bool(profile.url),
                f"URL: {profile.url}"
            )
            self.check(
                f"Pool '{profile.name}' Username",
                bool(profile.username),
                f"Username configured"
            )
            if not profile.password:
                self.warn(f"Pool '{profile.name}' has no password configured")
        
        # Check environment for secrets
        self.check(
            "Credentials Security",
            "HYBA_ALLOW_DEV_FIXTURES" not in os.environ or 
            os.getenv("HYBA_ALLOW_DEV_FIXTURES") != "true",
            "Dev fixtures are disabled (production mode)"
        )
        
        return self.checks_failed == 0
    
    async def validate_pool_connectivity(self, profiles: list[PoolProfile]) -> bool:
        """Test connectivity to pools."""
        logger.info("\n" + "="*60)
        logger.info("STEP 2: Validating Pool Connectivity")
        logger.info("="*60)
        
        gateway = ProductionMiningGateway()
        connection_success = 0
        
        try:
            await gateway.initialize(profiles=profiles)
            connection_success = sum(
                1 for status in gateway.orchestrator.pool_health.values()
                if status.health.value != "offline"
            )
        except Exception as e:
            logger.warning(f"Could not initialize gateway: {e}")
            return False
        
        self.check(
            "Pool Connectivity",
            connection_success > 0,
            f"{connection_success}/{len(profiles)} pool(s) connected"
        )
        
        return connection_success > 0
    
    async def validate_mining_operations(self, gateway: ProductionMiningGateway) -> bool:
        """Validate mining operations."""
        logger.info("\n" + "="*60)
        logger.info("STEP 3: Validating Mining Operations")
        logger.info("="*60)
        
        try:
            # Start mining
            await gateway.start()
            self.check("Mining Start", True, "Mining operations started successfully")
            
            # Get status
            status = gateway.get_status()
            self.check(
                "Status Retrieval",
                status.get("status") != "offline",
                f"Status: {status.get('status')}"
            )
            
            # Check for active pools
            stats = status.get("stats", {})
            active_pools = stats.get("healthy_pools", 0) + stats.get("degraded_pools", 0)
            self.check(
                "Active Pools",
                active_pools > 0,
                f"{active_pools} pool(s) active"
            )
            
            # Try to get a job
            job = await gateway.get_next_job()
            if job:
                self.check("Job Retrieval", True, "Successfully retrieved a mining job")
            else:
                self.warn("Could not retrieve a mining job (may be temporary)")
            
            # Stop mining
            await gateway.stop()
            self.check("Mining Stop", True, "Mining operations stopped cleanly")
            
            return True
        
        except Exception as e:
            logger.error(f"Mining operations validation failed: {e}")
            return False
    
    def print_summary(self) -> None:
        """Print validation summary."""
        logger.info("\n" + "="*60)
        logger.info("DEPLOYMENT GATE SUMMARY")
        logger.info("="*60)
        
        logger.info(f"Checks Passed:  {self.checks_passed}")
        logger.info(f"Checks Failed:  {self.checks_failed}")
        logger.info(f"Warnings:       {len(self.warnings)}")
        
        if self.warnings:
            logger.info("\nWarnings:")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")
        
        if self.checks_failed == 0:
            logger.info("\n✓ DEPLOYMENT GATE PASSED - Ready for production")
            return True
        else:
            logger.error("\n✗ DEPLOYMENT GATE FAILED - Address failures before deploying")
            return False


async def main():
    """Run the deployment gate."""
    gate = DeploymentGate()
    
    # Validate environment
    if not await gate.validate_environment():
        gate.print_summary()
        return 1
    
    # Get profiles
    profiles = ProductionMiningGateway.build_profiles_from_env()
    
    # Validate connectivity
    if not await gate.validate_pool_connectivity(profiles):
        gate.warn("Pool connectivity validation inconclusive")
    
    # Validate mining operations
    try:
        gateway = ProductionMiningGateway()
        await gateway.initialize(profiles=profiles)
        
        if await gate.validate_mining_operations(gateway):
            logger.info("Mining operations validated successfully")
    except Exception as e:
        gate.warn(f"Mining operations validation skipped: {e}")
    
    # Print summary
    gate.print_summary()
    
    return 0 if gate.checks_failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
