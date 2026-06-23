#!/usr/bin/env python3
"""HYBA local clean-10 evidence gate.

This gate is intentionally local-first. It does not assert the system is clean by
inspection. It executes the release-critical command set, writes a structured
JSON evidence packet, and exits non-zero unless every command passes. The report
also embeds a bounded tail from each command log so NO_GO artifacts are directly
actionable even when the per-command log files are not separately archived.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts" / "clean_10"
LOG_TAIL_LINES = 80


@dataclass(frozen=True)
class GateCommand:
    name: str
    command: list[str]
    required: bool = True


@dataclass(frozen=True)
class GateResult:
    name: str
    command: list[str]
    returncode: int
    passed: bool
    duration_seconds: float
    log_path: str
    log_tail: list[str]


@dataclass(frozen=True)
class CleanGateReport:
    schema: str
    generated_at_utc: str
    status: str
    passed: bool
    repository: str
    results: list[GateResult]
    required_failures: list[str]
    next_actions: list[str]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["results"] = [asdict(result) for result in self.results]
        return payload


def _base_env() -> dict[str, str]:
    env = os.environ.copy()
    pythonpath_parts = [str(ROOT / "python_backend")]
    if env.get("PYTHONPATH"):
        pythonpath_parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    env.setdefault("NODE_ENV", "production")
    env.setdefault("HYBA_ENV", env["NODE_ENV"])
    env.setdefault("HYBA_ENABLE_AUDIT_LOGGING", "true")
    env.setdefault("HYBA_ALLOW_DEV_FIXTURES", "false")
    env.setdefault("HYBA_ENABLE_AUTONOMOUS_MINING", "true")
    return env


def _commands() -> list[GateCommand]:
    python = sys.executable
    return [
        GateCommand(
            name="python_backend_environment",
            command=["npm", "run", "python:env:check"],
        ),
        GateCommand(
            name="review_gap_closure_matrix",
            command=[
                python,
                "-m",
                "pytest",
                "tests/test_review_gap_closure_matrix.py",
                "-q",
            ],
        ),
        GateCommand(
            name="simulation_vs_instantiation_boundary",
            command=[
                python,
                "-m",
                "pytest",
                "tests/test_simulation_vs_instantiation.py",
                "-q",
            ],
        ),
        GateCommand(
            name="deutsch_pulvini_claim_boundary",
            command=[
                python,
                "-m",
                "pytest",
                "tests/test_deutsch_pulvini_claim_boundary.py",
                "-q",
            ],
        ),
        GateCommand(
            name="quantum_solver_job_plumbing",
            command=[
                python,
                "-m",
                "pytest",
                "tests/test_agent3_quantum_solvers.py",
                "-q",
            ],
        ),
        GateCommand(
            name="hendrix_phi_solver_contracts",
            command=[
                python,
                "-m",
                "pytest",
                "tests/test_hendrix_phi_solver_contracts.py",
                "-q",
            ],
        ),
        GateCommand(
            name="hendrix_job_backed_benchmarks",
            command=[
                python,
                "-m",
                "pytest",
                "tests/test_hendrix_phi_performance_benchmark.py",
                "-q",
            ],
        ),
        GateCommand(
            name="iit_phi_proxy_contracts",
            command=[
                python,
                "-m",
                "pytest",
                "tests/test_iit_4_analyzer.py",
                "tests/test_iit_4_complete.py",
                "tests/test_iit_phi_mining_correlation.py",
                "-q",
            ],
        ),
        GateCommand(
            name="api_posture_serialization",
            command=[
                python,
                "-m",
                "pytest",
                "tests/test_api_posture_serialization.py",
                "-q",
            ],
        ),
        GateCommand(
            name="backend_mining_api_contracts",
            command=[python, "-m", "pytest", "tests/test_backend_mining_api.py", "-q"],
        ),
        GateCommand(
            name="auth_jwt_contracts",
            command=[python, "-m", "pytest", "tests/test_auth_jwt_contracts.py", "-q"],
        ),
        GateCommand(
            name="runtime_reflexive_introspection",
            command=[
                python,
                "-m",
                "pytest",
                "tests/test_runtime_reflexive_introspection.py",
                "-q",
            ],
        ),
        GateCommand(
            name="evidence_boundary_report",
            command=[
                python,
                "-m",
                "pytest",
                "tests/test_evidence_boundary_report.py",
                "-q",
            ],
        ),
        GateCommand(
            name="adaptive_capability_registry",
            command=[
                python,
                "-m",
                "pytest",
                "tests/test_adaptive_capability_registry.py",
                "-q",
            ],
        ),
        GateCommand(
            name="claim_evidence_manifest",
            command=[
                python,
                "-m",
                "pytest",
                "tests/test_claim_evidence_manifest.py",
                "-q",
            ],
        ),
        GateCommand(
            name="prediction_endpoint_contracts",
            command=[python, "-m", "pytest", "tests/test_prediction_endpoint.py", "-q"],
        ),
        GateCommand(
            name="pool_profile_primitives",
            command=[
                python,
                "-m",
                "pytest",
                "tests/test_pool_profile_primitives.py",
                "-q",
            ],
        ),
        GateCommand(
            name="autonomous_sovereign_gate_contracts",
            command=[
                python,
                "-m",
                "pytest",
                "tests/test_mining_autonomous_sovereign_gate.py",
                "-q",
            ],
        ),
        GateCommand(
            name="local_launch_contracts",
            command=[
                python,
                "-m",
                "pytest",
                "tests/test_local_launch_script_contract.py",
                "-q",
            ],
        ),
        GateCommand(
            name="frontend_bridge_and_security_contracts",
            command=[
                "npx",
                "vitest",
                "run",
                "tests/test_bridge_security.test.ts",
                "tests/test_security_swarm_routes.test.ts",
                "tests/test_consciousness_behavioral.test.ts",
            ],
        ),
        GateCommand(
            name="frontend_unit_gate",
            command=["npm", "run", "test:frontend:unit"],
        ),
        GateCommand(
            name="backend_gate",
            command=["npm", "run", "test:backend"],
        ),
        GateCommand(
            name="build_gate",
            command=["npm", "run", "build"],
        ),
    ]


def _read_log_tail(log_path: Path, line_limit: int = LOG_TAIL_LINES) -> list[str]:
    if not log_path.exists():
        return []
    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ["<log tail unavailable>"]
    return lines[-line_limit:]


def _run_command(
    command: GateCommand, env: dict[str, str], log_dir: Path
) -> GateResult:
    started = datetime.now(timezone.utc)
    log_path = log_dir / f"{command.name}.log"
    with log_path.open("w", encoding="utf-8") as log:
        log.write(f"$ {' '.join(command.command)}\n\n")
        process = subprocess.run(
            command.command,
            cwd=ROOT,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    finished = datetime.now(timezone.utc)
    duration = (finished - started).total_seconds()
    return GateResult(
        name=command.name,
        command=command.command,
        returncode=process.returncode,
        passed=process.returncode == 0,
        duration_seconds=duration,
        log_path=str(log_path.relative_to(ROOT)),
        log_tail=[] if process.returncode == 0 else _read_log_tail(log_path),
    )


def run_gate(commands: Iterable[GateCommand] | None = None) -> CleanGateReport:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = ARTIFACT_DIR / stamp
    run_dir.mkdir(parents=True, exist_ok=True)
    env = _base_env()
    selected = list(commands or _commands())
    results = [_run_command(command, env, run_dir) for command in selected]
    failures = [
        result.name
        for command, result in zip(selected, results)
        if command.required and not result.passed
    ]
    passed = not failures
    next_actions = (
        [
            "Archive this artifact with bootstrap, sovereign gate, readiness, telemetry and accepted-share evidence."
        ]
        if passed
        else [
            "Do not describe the repository as clean until required failures are zero.",
            "Use each failed result's embedded log_tail first, then open the referenced full log if needed.",
            "Fix the first failing command group and rerun this gate.",
        ]
    )
    report = CleanGateReport(
        schema="HYBA_FULLSTACK_LOCAL_CLEAN_10_GATE_V1",
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        status="GO" if passed else "NO_GO",
        passed=passed,
        repository="HYBA_FULLSTACK",
        results=results,
        required_failures=failures,
        next_actions=next_actions,
    )
    report_path = run_dir / "clean_10_gate.json"
    report_path.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8"
    )
    latest_path = ARTIFACT_DIR / "latest.json"
    latest_path.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8"
    )
    return report


def main() -> int:
    report = run_gate()
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0 if report.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
