#!/usr/bin/env python3
"""Run the post-quantum benchmark suite and emit a signed JSON artifact.

Output: artifacts/post_quantum_benchmark_result.json

The artifact includes:
  - per-test outcomes (nodeid, outcome, failure message if any)
  - summary counts and wall-clock duration
  - environment snapshot (Python, numpy, hypothesis, platform)
  - SHA-256 integrity hash of the result payload (self-signed, excludes the hash field)

Usage:
    PYTHONPATH=python_backend python scripts/run_post_quantum_benchmark.py
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATH = ROOT / "artifacts" / "post_quantum_benchmark_result.json"


def _pkg_version(name: str) -> str:
    try:
        import importlib.metadata

        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def run() -> int:
    venv_pytest = ROOT / "venv" / "bin" / "pytest"

    cmd = [
        str(venv_pytest) if venv_pytest.exists() else sys.executable,
        *([] if venv_pytest.exists() else ["-m", "pytest"]),
        "tests/test_post_quantum_benchmark.py",
        "-v",
        "--tb=short",
        "--no-header",
    ]

    print(f"Running: {' '.join(cmd)}")
    wall_start = time.perf_counter()

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        env={
            **__import__("os").environ,
            "PYTHONPATH": str(ROOT / "python_backend"),
        },
    )

    wall_elapsed = time.perf_counter() - wall_start
    raw_output = proc.stdout + proc.stderr

    # --- Parse failure blocks ---
    current_failures: dict[str, str] = {}
    in_failures = False
    current_test_id = ""
    failure_lines: list[str] = []

    for line in raw_output.splitlines():
        if "FAILURES" in line and line.startswith("="):
            in_failures = True
            continue
        if "short test summary" in line and line.startswith("="):
            if current_test_id and failure_lines:
                current_failures[current_test_id] = "\n".join(failure_lines).strip()
            in_failures = False
            current_test_id = ""
            failure_lines = []
            continue
        if in_failures:
            if line.startswith("_") and line.endswith("_"):
                if current_test_id and failure_lines:
                    current_failures[current_test_id] = "\n".join(failure_lines).strip()
                current_test_id = line.strip("_ ").strip()
                failure_lines = []
            elif current_test_id:
                failure_lines.append(line)

    # --- Parse test result lines ---
    tests: list[dict] = []
    for line in raw_output.splitlines():
        stripped = line.strip()
        for outcome in ("PASSED", "FAILED", "ERROR", "SKIPPED", "XFAIL", "XPASS"):
            if outcome in stripped and stripped.startswith("tests/"):
                parts = stripped.split()
                nodeid = parts[0]
                segments = nodeid.split("::")
                failure_msg = None
                if outcome in ("FAILED", "ERROR"):
                    failure_msg = next(
                        (v for k, v in current_failures.items() if segments[-1] in k),
                        None,
                    )
                tests.append(
                    {
                        "nodeid": nodeid,
                        "class": segments[-2] if len(segments) >= 3 else "",
                        "name": segments[-1],
                        "outcome": outcome,
                        "failure": failure_msg,
                    }
                )
                break

    passed = sum(1 for t in tests if t["outcome"] == "PASSED")
    failed = sum(1 for t in tests if t["outcome"] in ("FAILED", "ERROR"))
    total = len(tests)

    # --- Environment ---
    sys_python = sys.version
    try:
        venv_python = str(ROOT / "venv" / "bin" / "python")
        ver_proc = subprocess.run([venv_python, "--version"], capture_output=True, text=True)
        sys_python = ver_proc.stdout.strip() or ver_proc.stderr.strip()
    except Exception:
        pass

    env = {
        "python": sys_python,
        "platform": platform.platform(),
        "numpy": _pkg_version("numpy"),
        "hypothesis": _pkg_version("hypothesis"),
        "pytest": _pkg_version("pytest"),
    }

    summary = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "all_passed": failed == 0 and total > 0,
        "wall_clock_seconds": round(wall_elapsed, 3),
        "exit_code": proc.returncode,
    }

    payload: dict = {
        "benchmark": "POST_QUANTUM_BENCHMARK_V1",
        "description": "PULVINI is not quantum computing — it is what comes after quantum.",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "environment": env,
        "summary": summary,
        "tests": tests,
    }

    # Self-sign: SHA-256 of canonical JSON (hash field excluded from digest)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    integrity_hash = hashlib.sha256(canonical).hexdigest()
    payload["integrity_sha256"] = integrity_hash

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(payload, indent=2))

    print(f"\n{'=' * 60}")
    print(f"POST-QUANTUM BENCHMARK — {passed}/{total} passed")
    print(f"Wall clock : {wall_elapsed:.2f}s")
    print(f"SHA-256    : {integrity_hash}")
    print(f"Artifact   : {ARTIFACT_PATH.relative_to(ROOT)}")
    print(f"{'=' * 60}")

    if failed:
        print(f"\nFAILED ({failed}):")
        for t in tests:
            if t["outcome"] in ("FAILED", "ERROR"):
                print(f"  - {t['nodeid']}")

    return proc.returncode


if __name__ == "__main__":
    sys.exit(run())
