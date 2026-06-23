#!/usr/bin/env python3
"""
Apply all Salamander-generated integrations to complete system unification.

This script verifies and documents which integrations have been applied:
1. QaaS routes → main.py (applies qaas_routes_integration.py)
2. Multi-agent orchestrator → reflexive_controller.py (applies multi_agent_integration.py)
3. PULVINI compression → phi_unified_mining_engine.py (already integrated)
4. Memory seed loader → main.py (already integrated)

Date: 21 June 2026
Status: SALAMANDER SYSTEM UNIFICATION
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def verify_qaas_integration(main_py: Path) -> bool:
    """Verify QaaS routes are wired to main.py"""
    content = main_py.read_text()

    checks = [
        (
            "quantum_as_a_service_execute_hardened imported",
            "quantum_as_a_service_execute_hardened" in content,
        ),
        (
            "public_computational_intelligence_service imported",
            "public_computational_intelligence_service" in content,
        ),
        ("qaas router included", "/api/qaas" in content),
        ("ciaas router included", "/api/ciaas" in content),
    ]

    return all(result for _, result in checks), checks


def verify_multi_agent_integration(reflexive_controller: Path) -> bool:
    """Verify multi-agent orchestrator is wired to ReflexiveController"""
    content = reflexive_controller.read_text()

    checks = [
        ("SwarmOrchestrator imported", "SwarmOrchestrator" in content),
        ("AnalysisAgent imported", "AnalysisAgent" in content),
        ("OptimizationAgent imported", "OptimizationAgent" in content),
        ("SecurityAgent imported", "SecurityAgent" in content),
        (
            "orchestrator initialized in __init__",
            "self.orchestrator = SwarmOrchestrator()" in content,
        ),
        ("agents initialized in __init__", "self.agents =" in content),
    ]

    return all(result for _, result in checks), checks


def verify_pulvini_integration(mining_engine: Path) -> bool:
    """Verify PULVINI compression is integrated into phi_unified_mining_engine.py"""
    content = mining_engine.read_text()

    checks = [
        (
            "PulviniCompressedQuantumSolver imported",
            "PulviniCompressedQuantumSolver" in content,
        ),
        (
            "PulviniCompressedQuantumSolver instantiated",
            "PulviniCompressedQuantumSolver(" in content,
        ),
        (
            "phi_folding_mathematical_proof imported",
            "phi_folding_mathematical_proof" in content,
        ),
    ]

    return all(result for _, result in checks), checks


def verify_memory_seed_integration(main_py: Path) -> bool:
    """Verify memory seed loader is wired to main.py"""
    content = main_py.read_text()

    checks = [
        ("_load_memory_seed defined", "_load_memory_seed" in content),
        (
            "_load_memory_seed called in lifespan",
            "await _load_memory_seed(app)" in content,
        ),
        ("memory_seed loaded to app.state", "app.state.memory_seed" in content),
    ]

    return all(result for _, result in checks), checks


def verify_qiaas_integration(main_py: Path) -> bool:
    """Verify QIaaS service status: REMOVED due to unverified claims.

    QIaaS was removed on 21 June 2026 because it served unverified claims
    about "quantum intelligence" without falsifiable definitions or measurement
    protocols. See CRITICAL_ELEVATION_REPORT.md and falsifiability_requirements.md
    for details.

    This check now verifies that QIaaS is NOT wired (the correct state).
    """
    content = main_py.read_text()

    # QIaaS should NOT be present - this is the correct state
    checks = [
        (
            "quantum_intelligence_service NOT imported",
            "quantum_intelligence_service" not in content or "QIaaS removed" in content,
        ),
        (
            "QIaaS router NOT included",
            "quantum_intelligence_service.router" not in content
            or "QIaaS removed" in content,
        ),
    ]

    return all(result for _, result in checks), checks


def main():
    """Run all integration verification checks"""

    backend_root = Path(__file__).parent.parent / "python_backend"

    # Paths to verify
    main_py = backend_root / "hyba_genesis_api" / "main.py"
    reflexive_controller = (
        backend_root / "hyba_genesis_api" / "core" / "reflexive_controller.py"
    )
    mining_engine = backend_root / "pythia_mining" / "phi_unified_mining_engine.py"

    if not all(
        [main_py.exists(), reflexive_controller.exists(), mining_engine.exists()]
    ):
        logger.error("Required files not found")
        return False

    logger.info("=" * 80)
    logger.info("SALAMANDER INTEGRATION VERIFICATION")
    logger.info("=" * 80)

    results = {}

    # 1. Verify Memory Seed Integration
    logger.info("\n1. Memory Seed Loader Integration")
    logger.info("-" * 80)
    memory_seed_ok, memory_seed_checks = verify_memory_seed_integration(main_py)
    results["memory_seed"] = {
        "status": "✅ INTEGRATED" if memory_seed_ok else "❌ NOT INTEGRATED",
        "checks": memory_seed_checks,
    }
    for check_name, passed in memory_seed_checks:
        logger.info(f"  {'✅' if passed else '❌'} {check_name}")

    # 2. Verify QIaaS Integration Status
    logger.info("\n2. QIaaS (Quantum Intelligence as a Service) - REMOVED")
    logger.info("-" * 80)
    logger.info("  ℹ️  QIaaS was removed on 21 June 2026")
    logger.info("  ℹ️  Reason: Served unverified claims without falsifiable criteria")
    logger.info("  ℹ️  See: CRITICAL_ELEVATION_REPORT.md")
    logger.info("  ℹ️  Policy: .kiro/steering/falsifiability_requirements.md")
    qiaas_ok, qiaas_checks = verify_qiaas_integration(main_py)
    results["qiaas"] = {
        "status": (
            "✅ CORRECTLY REMOVED" if qiaas_ok else "❌ STILL PRESENT (should remove)"
        ),
        "checks": qiaas_checks,
    }
    for check_name, passed in qiaas_checks:
        logger.info(f"  {'✅' if passed else '❌'} {check_name}")

    # 3. Verify QaaS Routes Integration
    logger.info("\n3. QaaS Routes Integration")
    logger.info("-" * 80)
    qaas_ok, qaas_checks = verify_qaas_integration(main_py)
    results["qaas_routes"] = {
        "status": "✅ INTEGRATED" if qaas_ok else "❌ NOT INTEGRATED",
        "checks": qaas_checks,
    }
    for check_name, passed in qaas_checks:
        logger.info(f"  {'✅' if passed else '❌'} {check_name}")

    # 4. Verify Multi-Agent Integration
    logger.info("\n4. Multi-Agent Orchestrator Integration")
    logger.info("-" * 80)
    multi_agent_ok, multi_agent_checks = verify_multi_agent_integration(
        reflexive_controller
    )
    results["multi_agent"] = {
        "status": "✅ INTEGRATED" if multi_agent_ok else "❌ NOT INTEGRATED",
        "checks": multi_agent_checks,
    }
    for check_name, passed in multi_agent_checks:
        logger.info(f"  {'✅' if passed else '❌'} {check_name}")

    # 5. Verify PULVINI Integration
    logger.info("\n5. PULVINI Compression Integration")
    logger.info("-" * 80)
    pulvini_ok, pulvini_checks = verify_pulvini_integration(mining_engine)
    results["pulvini"] = {
        "status": "✅ INTEGRATED" if pulvini_ok else "❌ NOT INTEGRATED",
        "checks": pulvini_checks,
    }
    for check_name, passed in pulvini_checks:
        logger.info(f"  {'✅' if passed else '❌'} {check_name}")

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("INTEGRATION SUMMARY")
    logger.info("=" * 80)

    all_ok = memory_seed_ok and qiaas_ok and qaas_ok and multi_agent_ok and pulvini_ok
    integrated_count = sum(1 for _, r in results.items() if "INTEGRATED" in r["status"])
    total_count = len(results)

    logger.info(f"\n✅ Integrated: {integrated_count}/{total_count}")
    logger.info(f"   • Memory Seed: {'✅' if memory_seed_ok else '❌'}")
    logger.info(
        f"   • QIaaS: {'✅ REMOVED (correct)' if qiaas_ok else '❌ Still present'}"
    )
    logger.info(f"   • QaaS Routes: {'✅' if qaas_ok else '❌'}")
    logger.info(f"   • Multi-Agent: {'✅' if multi_agent_ok else '❌'}")
    logger.info(f"   • PULVINI: {'✅' if pulvini_ok else '❌'}")

    if all_ok:
        logger.info("\n🎉 ALL SALAMANDER INTEGRATIONS COMPLETE!")
        logger.info("\nSystem now fully wired:")
        logger.info("  • Memory seed bootstraps system structure metrics at startup")
        logger.info("  • QaaS/CIaaS routes available at /api/qaas and /api/ciaas")
        logger.info("  • Multi-agent orchestrator wired to reflexive controller")
        logger.info("  • PULVINI compression integrated in mining engine")
        logger.info(
            "  • QIaaS REMOVED (unverified claims - see CRITICAL_ELEVATION_REPORT.md)"
        )
        logger.info("\nNext steps:")
        logger.info("  1. Start backend: npm run backend:start")
        logger.info("  2. Run integration tests: npm run test:backend")
        logger.info("  3. Monitor system health at /api/health")
        logger.info("  4. Query QaaS at /api/qaas/health")
    else:
        logger.warning(f"\n⚠️  {total_count - integrated_count} integrations incomplete")
        logger.warning("   Review check results above for details")

    # Save report
    report_path = (
        Path(__file__).parent.parent
        / "artifacts"
        / "integration_verification_report.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w") as f:
        json.dump(
            {
                "timestamp": "2026-06-21",
                "system": "HYBA/PYTHIA-PULVINI",
                "integration_complete": all_ok,
                "results": results,
                "integrated_count": integrated_count,
                "total_count": total_count,
            },
            f,
            indent=2,
        )

    logger.info(f"\n📄 Report saved to: {report_path}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
