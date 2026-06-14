#!/usr/bin/env python3
"""Quick production readiness check - loads .env and validates all gates."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_env_file(env_path: Path) -> dict[str, str]:
    """Parse .env file and return variables."""
    env_vars = {}
    if not env_path.exists():
        return env_vars

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            env_vars[key.strip()] = value.strip()

    return env_vars


def run_check(name: str, command: list[str], env: dict[str, str]) -> tuple[bool, str]:
    """Run a validation check and return (passed, output)."""
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env={**os.environ, **env},
            capture_output=True,
            text=True,
            timeout=30,
        )
        passed = result.returncode == 0
        output = result.stdout + result.stderr
        return passed, output
    except subprocess.TimeoutExpired:
        return False, "Check timed out after 30 seconds"
    except Exception as e:
        return False, f"Check failed with exception: {e}"


def main() -> int:
    """Run all production readiness checks."""

    print("=" * 70)
    print("HYBA PRODUCTION READINESS - QUICK CHECK")
    print("=" * 70)
    print()

    # Load .env file
    env_file = ROOT / ".env"
    if not env_file.exists():
        print("❌ FAILED: .env file not found")
        print(f"   Expected location: {env_file}")
        return 1

    print(f"✅ Found .env file: {env_file}")
    env_vars = load_env_file(env_file)
    print(f"✅ Loaded {len(env_vars)} environment variables")
    print()

    # Define checks
    checks = [
        ("Security Audit", ["python", "scripts/audit_live_deployment.py"]),
        ("Runtime Mocks", ["python", "scripts/check_no_runtime_mocks.py"]),
        ("Environment Config", ["python", "scripts/validate_production_env.py"]),
    ]

    results = []
    all_passed = True

    print("Running production gate checks...")
    print("-" * 70)
    print()

    for name, command in checks:
        print(f"🔍 {name}...", end=" ", flush=True)
        passed, output = run_check(name, command, env_vars)
        results.append((name, passed, output))

        if passed:
            print("✅ PASSED")
        else:
            print("❌ FAILED")
            all_passed = False

    print()
    print("=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    print()

    for name, passed, output in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {name}")
        if not passed:
            print()
            print("Error details:")
            for line in output.splitlines()[-10:]:  # Last 10 lines
                print(f"  {line}")
            print()

    print("=" * 70)

    if all_passed:
        print()
        print("🎉 ALL CHECKS PASSED - PRODUCTION READY")
        print()
        print("Next steps:")
        print("  1. Review PRODUCTION_READINESS_SUMMARY.md")
        print("  2. Deploy using: docker-compose -f docker-compose.production.yml up -d")
        print("  3. Monitor health: curl http://localhost:3000/bridge/health")
        print()
        return 0
    else:
        print()
        print("⛔ SOME CHECKS FAILED - NOT PRODUCTION READY")
        print()
        print("Review failed checks above and:")
        print("  1. Fix issues in .env file")
        print("  2. Run this script again: python scripts/quick_production_check.py")
        print("  3. See PRODUCTION_READINESS_FORENSICS_REPORT.md for details")
        print()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
