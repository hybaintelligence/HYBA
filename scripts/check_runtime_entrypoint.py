#!/usr/bin/env python3
"""Validate HYBA runtime entrypoint and live miner API compatibility.

The production image has one ENTRYPOINT shared by the single-container runtime
and the docker-compose service split. Compose service commands must therefore be
honored; otherwise backend/runtime/bridge services all start the bundled default
runtime instead of their explicit service process.

This check also guards the live unified miner against stale Stratum API calls.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "scripts" / "hyba-runtime-entrypoint.sh"
UNIFIED_MINER = ROOT / "python_backend" / "run_unified_miner.py"
FORBIDDEN_MINER_SNIPPETS = {
    "profiles=[": "StratumClient no longer accepts profiles=[...]; construct from PoolProfile fields.",
    ".is_connected()": "StratumClient.is_connected is a boolean state flag, not a method.",
    ".wait_for_job(": "Use poll_live_event() / get_active_job_copy() for current Stratum jobs.",
    ".submit_share(": "Use submit_validated_share() after local SHA-256d verification.",
}
REQUIRED_MINER_SNIPPETS = {
    "submit_validated_share(": "live miner must submit through the exact validation path",
    "poll_live_event(": "live miner must poll the current Stratum event API",
    "get_active_job_copy(": "live miner must read jobs through the current async job accessor",
    "submit_candidate(": "live miner must locally verify candidates through UnifiedMiningEngine",
}


def _check_unified_miner_api() -> list[str]:
    failures: list[str] = []
    try:
        text = UNIFIED_MINER.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"Could not read {UNIFIED_MINER}: {exc}"]

    for snippet, reason in FORBIDDEN_MINER_SNIPPETS.items():
        if snippet in text:
            failures.append(f"Forbidden stale live-miner API snippet {snippet!r}: {reason}")
    for snippet, reason in REQUIRED_MINER_SNIPPETS.items():
        if snippet not in text:
            failures.append(f"Missing live-miner API snippet {snippet!r}: {reason}")
    return failures


def main() -> int:
    syntax = subprocess.run(
        ["sh", "-n", str(ENTRYPOINT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if syntax.returncode != 0:
        print(syntax.stderr, file=sys.stderr)
        return syntax.returncode

    command = subprocess.run(
        [
            "sh",
            str(ENTRYPOINT),
            "python",
            "-c",
            "print('entrypoint command override honored')",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )
    if command.returncode != 0:
        print(command.stdout, file=sys.stderr)
        print(command.stderr, file=sys.stderr)
        return command.returncode
    if "entrypoint command override honored" not in command.stdout:
        print("Entry point did not execute the provided service command", file=sys.stderr)
        print(command.stdout, file=sys.stderr)
        return 1

    miner_failures = _check_unified_miner_api()
    if miner_failures:
        print("Unified miner entrypoint API check failed:", file=sys.stderr)
        for failure in miner_failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Runtime entrypoint and unified miner API checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
