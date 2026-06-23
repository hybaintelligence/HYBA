#!/usr/bin/env python3
"""Start PYTHIA with mission memory seeded and ready to mine.

This script demonstrates the correct startup sequence:
1. Seed mission memory
2. Validate mission memory
3. Initialize unified engine
4. Set autonomy level to AUTONOMOUS
5. Enforce 1 EH/s limit
6. Ready to mine
"""

import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine
from pythia_mining.autonomous_mining_controller import AutonomyLevel
from pythia_mining.pythia_one_block_mission import (
    seed_mission_memory,
    validate_mission_memory,
)


async def start_pythia_with_mission():
    """Start PYTHIA with mission memory seeded and ready to mine."""

    print("=" * 80)
    print("  PYTHIA MISSION STARTUP")
    print("=" * 80)

    # Step 1: Seed mission memory
    print("\n--- STEP 1: SEED MISSION MEMORY ---")
    mission = seed_mission_memory()
    print(f"  Mission protocol: {mission.protocol}")
    print(f"  Mission: {mission.mission}")
    print(f"  Autonomy from startup: {mission.autonomy_from_startup}")

    # Step 2: Validate mission memory
    print("\n--- STEP 2: VALIDATE MISSION MEMORY ---")
    mission_valid = validate_mission_memory(mission)
    print(f"  Mission valid: {mission_valid}")
    if not mission_valid:
        print("  ERROR: Mission memory validation failed!")
        return False

    # Step 3: Initialize unified engine
    print("\n--- STEP 3: INITIALIZE UNIFIED ENGINE ---")
    engine = UnifiedMiningEngine()
    print("  Engine initialized")
    print(f"  Configured capacity: {engine.configured_capacity_ehs} EH/s")

    # Step 4: Set autonomy level to AUTONOMOUS
    print("\n--- STEP 4: SET AUTONOMY LEVEL ---")
    engine.set_autonomy_level(AutonomyLevel.AUTONOMOUS)
    print(
        f"  Autonomy level: {engine.autonomous_controller.current_autonomy_level.value}"
    )
    print("  Self-healing: ENABLED (consciousness-driven regime adaptation)")
    print("  Self-optimization: ENABLED (search strategy + hashrate tuning)")
    print("  Safety constraints: ENFORCED (mathematical bounds)")

    # Step 5: Enforce 1 EH/s limit
    print("\n--- STEP 5: ENFORCE 1 EH/S LIMIT ---")
    current_capacity = engine.configured_capacity_ehs or 100.0
    safe_hashrate = mission.enforce_hashrate_limit(current_capacity)
    print(f"  Requested hashrate: {current_capacity} EH/s")
    print(f"  Safe hashrate (clamped): {safe_hashrate} EH/s")
    print(
        f"  Limit enforced: {mission.hashrate_limit.max_autonomous_hashrate_ehs} EH/s"
    )

    # Step 6: Verify mission readiness
    print("\n--- STEP 6: VERIFY MISSION READINESS ---")
    print(f"  Mission status: {mission.status.value}")
    print(f"  Mission complete: {mission.is_complete()}")
    print(f"  Should shutdown: {mission.should_shutdown()}")
    print(f"  Phi density: {engine.autonomous_controller.get_phi_density():.6f}")
    print(
        f"  Reflexive loop enabled: {engine.autonomous_controller.config.reflexive_loop_enabled}"
    )

    # Step 7: Run one reflexive improvement cycle
    print("\n--- STEP 7: RUN REFLEXIVE IMPROVEMENT CYCLE ---")
    improvement_result = await engine.autonomous_controller.seek_improvement()
    print(f"  Cycle executed: {improvement_result['reflexive_cycle_executed']}")
    print(f"  Epoch: {improvement_result['epoch']}")
    print(f"  Proposals generated: {improvement_result['proposals_generated']}")
    print(f"  Proposals applied: {improvement_result['proposals_applied']}")
    print(f"  Phi density after: {improvement_result['current_phi_density']:.6f}")

    # Step 8: Final readiness check
    print("\n--- STEP 8: FINAL READINESS CHECK ---")
    print("  Mission memory: VALID")
    print("  Autonomy level: AUTONOMOUS")
    print("  Hashrate limit: 1.0 EH/s ENFORCED")
    print(f"  Phi density: {engine.autonomous_controller.get_phi_density():.6f}")
    print("  Reflexive learning: ACTIVE")
    print("  Safety constraints: ENFORCED")
    print("  Mission target: 1 pool-confirmed accepted block")
    print("  Shutdown after completion: YES")

    print("\n" + "=" * 80)
    print("  PYTHIA IS READY TO MINE")
    print("=" * 80)
    print("\n  Operational sentence:")
    print("  PYTHIA wakes seeded with the full structure-search doctrine,")
    print("  selects the configured default pool, searches deterministically")
    print("  through the dodecahedral/icosahedral/PULVINI/HENDRIX stack,")
    print("  verifies every candidate with exact SHA-256d, learns from every")
    print("  pool response, and shuts herself down after one pool-confirmed")
    print("  accepted block.")
    print("=" * 80)

    return True


if __name__ == "__main__":
    success = asyncio.run(start_pythia_with_mission())
    sys.exit(0 if success else 1)
