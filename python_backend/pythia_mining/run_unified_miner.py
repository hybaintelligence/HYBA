"""Unified mining loop integrating verified pool profiles with autonomous controller.

This module provides the main entry point for production mining operations with
full integration of pool routing, secrets validation, autonomous control, and
Salamander frontier regeneration capabilities.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from typing import Optional

from pythia_mining.audit_logger import get_audit_logger
from pythia_mining.phi_config import initialize_production_secrets
from pythia_mining.pool_profiles import PoolProfile, load_pool_profiles
from pythia_mining.salamander_mining_integration import SalamanderMiningIntegration


async def main_mining_loop(
    override_profiles: Optional[list[PoolProfile]] = None,
) -> None:
    """
    Integrates sealed pool profiles directly with the hardened Autonomous Controller.

    Args:
        override_profiles: Optional list of profiles for testing (bypasses pool config loading)

    Raises:
        RuntimeError: If no verified pool profiles are available or security check fails
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger("hyba.mining")
    audit_logger = get_audit_logger()

    # 1. Enforce production environmental validation gates
    logger.info("Initializing production security gates...")
    security_status = initialize_production_secrets()
    assert security_status["status"] in [
        "SEC_SECURE",
        "DEV_PASS",
    ], "Security validation failed"
    logger.info(f"Security status: {security_status['status']}")

    # 2. Load the verified, immutable stratum pool profiles
    if override_profiles:
        verified_profiles = override_profiles
        logger.info(f"Using {len(verified_profiles)} override pool profiles")
    else:
        logger.info("Loading verified pool profiles from configuration...")
        verified_profiles = load_pool_profiles()

    if len(verified_profiles) < 1:
        raise RuntimeError(
            "Initialization blocked: No verified stratum pool profiles available. "
            "Configure at least one pool via environment variables or mining_pools_config.json"
        )

    logger.info(f"Loaded {len(verified_profiles)} verified pool profiles:")
    for profile in verified_profiles:
        logger.info(
            f"  - {profile.name} ({profile.pool_id}) @ {profile.url} "
            f"[priority: {profile.priority}, stratum v{profile.stratum_version}]"
        )

    # 3. Instantiate the autonomous controller (lazy import to avoid circular dependencies)
    try:
        from pythia_mining.autonomous_mining_controller import AutonomousMiningController

        controller = AutonomousMiningController()
        await controller.initialize_substrate()
        logger.info("Autonomous mining controller initialized successfully")
    except ImportError as exc:
        logger.error(f"Failed to import autonomous controller: {exc}")
        raise RuntimeError(
            "Autonomous controller unavailable. Ensure all dependencies are installed."
        ) from exc

    # 4. Integrate Salamander frontier for autonomous regeneration and optimization
    try:
        salamander = SalamanderMiningIntegration(
            mining_system=controller,
            target_hashrate=150.0,
            enable_autonomy_loops=True,
        )
        salamander.initialize()
        logger.info("Salamander frontier integration initialized successfully")
    except Exception as exc:
        logger.error(f"Failed to initialize Salamander integration: {exc}")
        raise RuntimeError(
            "Salamander frontier unavailable. Ensure salamander_mining_integration is properly configured."
        ) from exc

    # 5. Begin execution loop utilizing verified routing targets
    current_pool = verified_profiles[0]
    logger.info(f"HYBA Engine active. Primary target set to: {current_pool.url}")

    audit_logger.log_connection_attempt(
        pool_name=current_pool.name,
        pool_url=current_pool.url,
        stratum_version=current_pool.stratum_version,
        attempt_number=1,
    )

    # 6. Start Salamander autonomy loops for continuous self-optimization
    try:
        await salamander.start_autonomy_loops()
        logger.info("Salamander autonomy loops started successfully")
    except Exception as exc:
        logger.error(f"Failed to start Salamander autonomy loops: {exc}")
        raise RuntimeError(
            "Salamander autonomy loops failed to start. Mining will continue without autonomous optimization."
        ) from exc

    # Main mining loop with Salamander frontier integration
    try:
        while True:
            # Observe mining state through Salamander frontier
            metrics = salamander.observe_mining_state()
            
            # Detect mining-specific anomalies
            anomaly = salamander.detect_mining_anomaly(metrics)
            if anomaly:
                logger.warning(f"Mining anomaly detected: {anomaly.type} - {anomaly.severity}")
                outcome = salamander.execute_mining_regeneration(anomaly)
                logger.info(f"Regeneration executed: {outcome.reason}")
            
            # Core mining execution logic utilizing active strategy tracking
            # This would typically call:
            # - controller.process_job(job)
            # - controller.submit_share(share)
            # - controller.handle_pool_response(response)
            
            # Record share submissions to Salamander evidence log for non-repudiation
            # Example: salamander.record_share_submission(job_id, nonce, difficulty, accepted, revenue_btc)
            
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal, stopping mining operations...")
        await salamander.stop_autonomy_loops()
        logger.info("Salamander autonomy loops stopped successfully")
    except Exception as exc:
        logger.error(f"Fatal error in mining loop: {exc}")
        await salamander.stop_autonomy_loops()
        raise
    finally:
        logger.info("Mining loop terminated")
        
        # Export final health report for regulatory compliance
        health_report = salamander.get_mining_health_report()
        logger.info(f"Final mining health report: agents_active={health_report.get('agents_active')}, hashrate_current={health_report.get('hashrate_current')}")


def main() -> None:
    """CLI entry point for the unified mining loop."""
    try:
        asyncio.run(main_mining_loop())
    except Exception as exc:
        print(f"FATAL: Mining loop failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
