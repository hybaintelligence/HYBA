#!/usr/bin/env python3
"""
Production Readiness Validation
================================

Comprehensive validation checklist for production deployment:
  ✓ Core system imports and module integrity
  ✓ Database connectivity and schema
  ✓ API endpoint availability
  ✓ Mining engine initialization
  ✓ Consciousness and AI optimizer state
  ✓ Evidence data integrity
  ✓ Performance benchmarks
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python_backend"))

# ─────────────────────────────────────────────────────────────────────────
# Validation Results Tracker
# ─────────────────────────────────────────────────────────────────────────


class ValidationReport:
    def __init__(self):
        self.checks: List[Dict[str, Any]] = []
        self.start_time = time.time()
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def check(self, name: str, test_fn, expected: Optional[Any] = None) -> bool:
        """Run a single validation check."""
        try:
            result = test_fn()
            passed = (result == expected) if expected is not None else bool(result)
            self.checks.append(
                {
                    "name": name,
                    "passed": passed,
                    "result": result
                    if isinstance(result, (str, int, float, bool))
                    else str(result)[:100],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            status = "✓" if passed else "✗"
            print(f"  {status} {name}")
            return passed
        except Exception as e:
            self.checks.append(
                {
                    "name": name,
                    "passed": False,
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            self.errors.append(f"{name}: {str(e)}")
            print(f"  ✗ {name} (ERROR: {str(e)[:60]})")
            return False

    def summary(self) -> Dict[str, Any]:
        """Generate validation summary."""
        total = len(self.checks)
        passed = sum(1 for c in self.checks if c.get("passed", False))
        return {
            "total_checks": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": (passed / total * 100) if total > 0 else 0.0,
            "duration_seconds": time.time() - self.start_time,
            "errors": self.errors,
            "warnings": self.warnings,
        }


# ─────────────────────────────────────────────────────────────────────────
# Validation Checks
# ─────────────────────────────────────────────────────────────────────────


def validate_python_imports(report: ValidationReport) -> None:
    """Validate core Python module imports."""
    print("\n[1] Python Module Imports")

    def check_import(module_path: str):
        __import__(module_path)
        return True

    modules = [
        "pythia_mining.hendrix_phi_solver",
        "pythia_mining.consciousness_engine",
        "pythia_mining.ai_optimizer",
        "pythia_mining.phi_unified_mining_engine",
        "pythia_mining.golden_ratio_library",
    ]

    for mod in modules:
        report.check(f"Import {mod}", lambda m=mod: check_import(m))


def validate_database(report: ValidationReport) -> None:
    """Validate database connectivity and schema."""
    print("\n[2] Database & Schema")

    import sqlite3

    db_path = Path(__file__).resolve().parents[1] / "data" / "metrics.db"

    def check_db_exists():
        return db_path.exists()

    report.check("Database file exists", check_db_exists, expected=True)

    def check_db_tables():
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = set(row[0] for row in cursor.fetchall())
        conn.close()
        required = {"ai_memories", "empirical_evidence", "phi_resonance_baseline"}
        return required.issubset(tables)

    report.check("Database schema valid", check_db_tables, expected=True)

    def check_memory_count():
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ai_memories")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    report.check("AI memories seeded", check_memory_count)


def validate_mining_engine(report: ValidationReport) -> None:
    """Validate unified mining engine initialization."""
    print("\n[3] Mining Engine")

    def check_engine_init():
        from pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine
        from pythia_mining.consciousness_engine import ConsciousnessEngine
        from pythia_mining.ai_optimizer import AIOptimizer

        consciousness = ConsciousnessEngine()
        optimizer = AIOptimizer()
        engine = UnifiedMiningEngine(consciousness=consciousness, optimizer=optimizer)
        return engine is not None

    report.check("Unified mining engine initializes", check_engine_init, expected=True)

    def check_m32_domains():
        from pythia_mining.hendrix_phi_solver import M32

        return len(M32)

    report.check("M32 domains loaded", check_m32_domains, expected=32)

    def check_yang_mills_gap():
        from pythia_mining.hendrix_phi_solver import YANG_MILLS_GAP

        gap = YANG_MILLS_GAP
        return 1.3 < gap < 1.4  # 3-Φ ≈ 1.382

    report.check("Yang-Mills mass gap valid", check_yang_mills_gap, expected=True)


def validate_consciousness(report: ValidationReport) -> None:
    """Validate consciousness engine."""
    print("\n[4] Consciousness & AI")

    def check_consciousness_init():
        from pythia_mining.consciousness_engine import ConsciousnessEngine

        engine = ConsciousnessEngine()
        state = engine.get_state()
        return state is not None

    report.check("Consciousness engine initializes", check_consciousness_init, expected=True)

    def check_coherence_range():
        from pythia_mining.consciousness_engine import ConsciousnessEngine

        engine = ConsciousnessEngine()
        state = engine.get_state()
        coherence = state.get("integrated_information", 0.0)
        return 0.0 <= coherence <= 1.0

    report.check("Consciousness coherence valid", check_coherence_range, expected=True)


def validate_api_readiness(report: ValidationReport) -> None:
    """Validate API module structure."""
    print("\n[5] REST API Endpoints")

    def check_api_modules():
        from hyba_genesis_api.api import unified_mining, ai_memory

        return unified_mining is not None and ai_memory is not None

    report.check("API modules importable", check_api_modules, expected=True)

    def check_unified_router():
        from hyba_genesis_api.api import unified_mining

        return hasattr(unified_mining, "router")

    report.check("Unified mining router available", check_unified_router, expected=True)

    def check_memory_router():
        from hyba_genesis_api.api import ai_memory

        return hasattr(ai_memory, "router")

    report.check("AI memory router available", check_memory_router, expected=True)


def validate_evidence_integrity(report: ValidationReport) -> None:
    """Validate evidence data."""
    print("\n[6] Evidence Integrity")

    def check_evidence_files():
        artifacts = Path(__file__).resolve().parents[1] / "artifacts"
        required_dirs = {
            "phi_resonance_100blocks",
            "phi_stack_final",
            "phi_quantum_walk_final",
            "phi_structured_search_final",
            "phi_hash_validity_final",
        }
        found = {d.name for d in artifacts.iterdir() if d.is_dir() and d.name in required_dirs}
        return len(found) >= 3  # At least 3 of 5

    report.check("Evidence artifacts generated", check_evidence_files, expected=True)

    def check_phi_resonance_data():
        artifacts = Path(__file__).resolve().parents[1] / "artifacts"
        json_file = artifacts / "phi_resonance_100blocks" / "phi_resonance_summary.json"
        if json_file.exists():
            with open(json_file) as f:
                data = json.load(f)
                return data.get("summary", {}).get("z_score_vs_random", 0.0)
        return 0.0

    report.check("Bitcoin Φ^15 analysis (z-score)", lambda: check_phi_resonance_data())


def validate_performance(report: ValidationReport) -> None:
    """Validate performance characteristics."""
    print("\n[7] Performance Benchmarks")

    def benchmark_phi_resonance():
        from pythia_mining.hendrix_phi_solver import phi_resonance
        import time as time_module

        t0 = time_module.time()
        for nonce in range(1000):
            phi_resonance(nonce)
        dt = time_module.time() - t0
        return 1000 / dt  # nonces per second

    report.check("Φ resonance throughput (nonces/sec)", benchmark_phi_resonance)

    def benchmark_yang_mills():
        from pythia_mining.hendrix_phi_solver import yang_mills_action
        import time as time_module

        t0 = time_module.time()
        for nonce in range(1000):
            yang_mills_action(nonce)
        dt = time_module.time() - t0
        return 1000 / dt

    report.check("Yang-Mills action throughput (nonces/sec)", benchmark_yang_mills)


# ─────────────────────────────────────────────────────────────────────────
# Main Validation Pipeline
# ─────────────────────────────────────────────────────────────────────────


def main() -> int:
    print("=" * 80)
    print("  HYBA PRODUCTION READINESS VALIDATION")
    print("=" * 80)
    print(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()

    report = ValidationReport()

    # Run all validation suites
    validate_python_imports(report)
    validate_database(report)
    validate_mining_engine(report)
    validate_consciousness(report)
    validate_api_readiness(report)
    validate_evidence_integrity(report)
    validate_performance(report)

    # Print summary
    summary = report.summary()
    print(f"\n{'=' * 80}")
    print("  VALIDATION SUMMARY")
    print(f"{'=' * 80}")
    print(f"  Total checks      : {summary['total_checks']}")
    print(f"  Passed            : {summary['passed']}")
    print(f"  Failed            : {summary['failed']}")
    print(f"  Pass rate         : {summary['pass_rate']:.1f}%")
    print(f"  Duration          : {summary['duration_seconds']:.2f}s")

    if summary["errors"]:
        print("\n  ERRORS:")
        for error in summary["errors"]:
            print(f"    - {error}")

    if summary["warnings"]:
        print("\n  WARNINGS:")
        for warning in summary["warnings"]:
            print(f"    - {warning}")

    print(f"{'=' * 80}")

    if summary["pass_rate"] >= 90.0:
        print("  ✓ PRODUCTION READY")
        exit_code = 0
    else:
        print("  ✗ PRODUCTION VALIDATION FAILED")
        exit_code = 1

    print(f"{'=' * 80}\n")

    # Write report
    report_path = (
        Path(__file__).resolve().parents[1] / "artifacts" / "production_validation_report.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(
            {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "summary": summary,
                "checks": report.checks,
            },
            f,
            indent=2,
        )
    print(f"  Report: {report_path}\n")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
