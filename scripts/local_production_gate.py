#!/usr/bin/env python3
"""Local production evidence gate for HYBA_FULLSTACK.

This script exists for command-room releases where hosted CI is unavailable.
It runs the same evidence categories locally, captures stdout/stderr, and writes
an immutable timestamped JSON evidence packet under artifacts/production_readiness.

It never connects to pools and never enables live share submission. Live-pool
activation remains an operator action after this evidence packet is reviewed.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts" / "production_readiness"

Mode = Literal["rc", "live", "command-room"]

RC_STEPS = [
    ("live_deployment_forensic_audit", ["npm", "run", "live:audit"]),
    ("runtime_mock_guard", ["npm", "run", "runtime:guard"]),
    ("typescript_lint", ["npm", "run", "lint"]),
    ("production_build", ["npm", "run", "build"]),
    ("backend_unit_tests", ["npm", "run", "test:backend"]),
    ("backend_e2e_tests", ["npm", "run", "test:e2e:backend"]),
    ("deployment_e2e_tests", ["npm", "run", "test:deployment:e2e"]),
    ("deployment_property_tests", ["npm", "run", "test:deployment:property"]),
]

LIVE_STEPS = [
    ("production_environment_validation", ["npm", "run", "prod:env:check"]),
    ("pulvini_live_cut_preflight", ["npm", "run", "pulvini:live-cut:check"]),
]

REDACT_KEYS = ("SECRET", "PASSWORD", "CREDENTIAL", "TOKEN", "PRIVATE", "KEY")


@dataclass(frozen=True)
class StepResult:
    name: str
    command: list[str]
    returncode: int
    passed: bool
    duration_seconds: float
    stdout_tail: str
    stderr_tail: str


@dataclass(frozen=True)
class GateReport:
    version: str
    mode: Mode
    status: str
    passed: bool
    generated_at_utc: str
    host: dict[str, str]
    environment_summary: dict[str, str]
    steps: list[StepResult] = field(default_factory=list)
    next_operator_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["steps"] = [asdict(step) for step in self.steps]
        return payload


def _tail(text: str, limit: int = 6000) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def _redacted_env_summary() -> dict[str, str]:
    interesting = [
        "NODE_ENV",
        "HYBA_ENV",
        "HYBA_ALLOW_DEV_FIXTURES",
        "HYBA_ENABLE_LIVE_STRATUM",
        "HYBA_ENABLE_MINING_AUTOCONNECT",
        "HYBA_ENABLE_LIVE_SHARE_SUBMIT",
        "HYBA_ENABLE_AUDIT_LOGGING",
        "HYBA_LIVE_SHARE_APPROVAL_ID",
        "PULVINI_BACKEND_URL",
    ]
    summary: dict[str, str] = {}
    for name in interesting:
        value = os.getenv(name)
        if value is None:
            summary[name] = "<unset>"
        elif any(marker in name for marker in REDACT_KEYS):
            summary[name] = "<redacted>"
        elif value == "":
            summary[name] = "<empty>"
        else:
            summary[name] = value
    configured_pools = []
    for pool in ("VIABTC", "NICEHASH", "BRAIINS", "CKPOOL", "STRATUMV2"):
        if any(os.getenv(f"HYBA_POOL_{pool}_{field}") for field in ("URL", "USERNAME", "PASSWORD", "BTC_ADDRESS", "WORKER", "NICEHASH_POOL_ID", "NH_POOL_ID")):
            configured_pools.append(pool)
    summary["configured_pool_profiles"] = ",".join(configured_pools) if configured_pools else "<none>"
    return summary


def _run_step(name: str, command: list[str]) -> StepResult:
    start = datetime.now(timezone.utc)
    completed = subprocess.run(
        command if sys.platform != "win32" else ["cmd", "/c"] + command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=os.environ.copy(),
    )
    end = datetime.now(timezone.utc)
    duration = (end - start).total_seconds()
    return StepResult(
        name=name,
        command=command,
        returncode=completed.returncode,
        passed=completed.returncode == 0,
        duration_seconds=duration,
        stdout_tail=_tail(completed.stdout),
        stderr_tail=_tail(completed.stderr),
    )


def _steps_for_mode(mode: Mode) -> list[tuple[str, list[str]]]:
    if mode == "rc":
        return RC_STEPS
    if mode == "live":
        return LIVE_STEPS
    return RC_STEPS + LIVE_STEPS


def _next_actions(mode: Mode, passed: bool) -> list[str]:
    if not passed:
        return [
            "Stop the cutover.",
            "Fix the first failed step in the evidence packet.",
            "Rerun the same local gate from a clean checkout or clean terminal session.",
        ]
    if mode == "rc":
        return [
            "Run npm run prod:live:gate with production secrets injected but share submission disabled.",
            "Preserve this evidence JSON with the release ticket.",
        ]
    return [
        "Start production with HYBA_ENABLE_LIVE_SHARE_SUBMIT=false and HYBA_ENABLE_MINING_AUTOCONNECT=false.",
        "Check /bridge/health, backend readiness, and authenticated mining status.",
        "Only enable live share submission after legal, treasury, security, operations, and CEO approval are attached to HYBA_LIVE_SHARE_APPROVAL_ID.",
        "Capture pool-side accepted/rejected share evidence before making revenue or solvency claims.",
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local HYBA_FULLSTACK production evidence gate")
    parser.add_argument("--mode", choices=("rc", "live", "command-room"), default="command-room")
    parser.add_argument("--continue-on-failure", action="store_true", help="Run remaining steps after a failure while still returning non-zero")
    args = parser.parse_args(argv)

    steps: list[StepResult] = []
    for name, command in _steps_for_mode(args.mode):
        print(f"==> {name}: {' '.join(command)}", flush=True)
        result = _run_step(name, command)
        steps.append(result)
        marker = "PASS" if result.passed else "FAIL"
        print(f"<== {name}: {marker} ({result.duration_seconds:.2f}s)", flush=True)
        if not result.passed and not args.continue_on_failure:
            break

    passed = all(step.passed for step in steps) and len(steps) == len(_steps_for_mode(args.mode))
    status = "passed" if passed else "blocked"
    now = datetime.now(timezone.utc)
    report = GateReport(
        version="HYBA_FULLSTACK_LOCAL_PRODUCTION_GATE_V1",
        mode=args.mode,
        status=status,
        passed=passed,
        generated_at_utc=now.isoformat(),
        host={
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "machine": platform.machine(),
        },
        environment_summary=_redacted_env_summary(),
        steps=steps,
        next_operator_actions=_next_actions(args.mode, passed),
    )

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    artifact = ARTIFACT_DIR / f"local_production_gate_{args.mode}_{now.strftime('%Y%m%dT%H%M%SZ')}.json"
    artifact.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    print(f"Evidence packet: {artifact.relative_to(ROOT)}")
    print(f"Gate status: {status}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
