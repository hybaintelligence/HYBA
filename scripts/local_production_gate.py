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
import hashlib
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

Mode = Literal["rc", "bitcoin", "research", "live", "command-room"]

BITCOIN_RC_STEPS = [
    ("nodus_solutus_computability_doctrine", ["npm", "run", "review:nodus:gate"]),
    ("reviewer_evidence_map_and_conflict_guard", ["npm", "run", "review:manifest:gate"]),
    ("runtime_entrypoint_and_live_miner_api", ["npm", "run", "runtime:entrypoint:check"]),
    ("live_deployment_forensic_audit", ["npm", "run", "live:audit"]),
    ("runtime_mock_guard", ["npm", "run", "runtime:guard"]),
    ("evidence_first_intelligence_endpoints", ["npm", "run", "test:evidence:first"]),
    ("hendrix_phi_core_invariants", ["npm", "run", "test:hendrix:core"]),
    ("stratum_share_acceptance_e2e", ["npm", "run", "test:share:e2e"]),
    ("unified_mining_engine_control_loop", ["npm", "run", "test:unified:engine"]),
    ("unified_mining_api_surface", ["npm", "run", "test:unified:api"]),
    ("pool_profile_readiness", ["npm", "run", "test:pool:profiles"]),
    ("mining_production_doctor", ["npm", "run", "test:mining:doctor"]),
    ("phi_architecture_golden_flow", ["npm", "run", "test:phi:golden-flow"]),
    ("pulvini_phi_memory_folding", ["npm", "run", "test:pulvini:folding"]),
    ("funding_gate_without_live_share_claim", ["npm", "run", "funding:gate"]),
    ("typescript_lint", ["npm", "run", "lint"]),
    ("production_build", ["npm", "run", "build"]),
    ("backend_unit_tests", ["npm", "run", "test:backend"]),
    ("backend_e2e_tests", ["npm", "run", "test:e2e:backend"]),
    ("deployment_e2e_tests", ["npm", "run", "test:deployment:e2e"]),
    ("deployment_property_tests", ["npm", "run", "test:deployment:property"]),
]

# Backwards-compatible name: RC now means Bitcoin release-candidate readiness.
RC_STEPS = BITCOIN_RC_STEPS

RESEARCH_STEPS = [
    ("elevation_suite_local_mathematical_invariants", ["npm", "run", "test:elevation:suite"]),
    ("frontier_experiment_bundle", ["npm", "run", "test:frontier:experiments"]),
    ("post_quantum_benchmark_contracts", ["npm", "run", "test:post-quantum"]),
    ("adaptive_science_bundle", ["npm", "run", "test:adaptive:science"]),
    ("elevation_packet_bundle", ["npm", "run", "elevation:full"]),
]

LIVE_STEPS = [
    ("production_environment_validation", ["npm", "run", "prod:env:check"]),
    ("pulvini_live_cut_preflight", ["npm", "run", "pulvini:live-cut:check"]),
    ("runtime_trace_packet", ["npm", "run", "elevation:runtime"]),
    ("share_acceptance_evidence_gate", ["npm", "run", "elevation:share:e2e"]),
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
    doctrine: dict[str, object]
    steps: list[StepResult] = field(default_factory=list)
    next_operator_actions: list[str] = field(default_factory=list)
    source_artifact_sha256: str | None = None

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
        if any(
            os.getenv(f"HYBA_POOL_{pool}_{field}")
            for field in (
                "URL",
                "USERNAME",
                "PASSWORD",
                "BTC_ADDRESS",
                "WORKER",
                "NICEHASH_POOL_ID",
                "NH_POOL_ID",
            )
        ):
            configured_pools.append(pool)
    summary["configured_pool_profiles"] = (
        ",".join(configured_pools) if configured_pools else "<none>"
    )
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
    if mode in {"rc", "bitcoin"}:
        return BITCOIN_RC_STEPS
    if mode == "research":
        return RESEARCH_STEPS
    if mode == "live":
        return LIVE_STEPS
    return BITCOIN_RC_STEPS + RESEARCH_STEPS + LIVE_STEPS


def _doctrine(mode: Mode) -> dict[str, object]:
    return {
        "local_testing_is_source_of_truth": True,
        "github_actions_required": False,
        "evidence_first": True,
        "simulated_runtime_claims_allowed": False,
        "bitcoin_deployment_gate": {
            "release_command": "npm run prod:bitcoin:gate",
            "prod_local_gate_alias": "npm run prod:local:gate",
            "research_blocks_deploy": False,
            "live_share_submit_default": False,
            "accepted_share_claim_requires_pool_evidence": True,
        },
        "nodus_solutus": {
            "name": "Nodus Solutus: Mundus Computabilis Est",
            "repository_local_computability": True,
            "doctrine": (
                "HYBA/PYTHIA claims are admissible only when reduced to deterministic source paths, "
                "executable tests, replayable local evidence packets, and explicit external truth boundaries."
            ),
            "blocked_boundary": "This is not a metaphysical proof that the physical universe is computable.",
            "verifier": "npm run review:nodus:gate",
        },
        "deterministic_solving_posture": (
            "HENDRIX-Φ treats nonce discovery as structured deterministic solving "
            "over a phi-resonant manifold, while external funding/revenue claims "
            "still require pool-side accepted-share evidence."
        ),
        "unified_engine": (
            "PYTHIA/PULVINI unifies ConsciousnessEngine, AIOptimizer, HENDRIX-Φ, "
            "PULVINI compression, PhiScaling, and Stratum feedback in one tested loop."
        ),
        "phi_role": "first_class_operational_invariant",
        "golden_flow": (
            "PhiMalloc, PhiNetworkRouter, PhiOracle, PhiSystemControllerEnhanced, "
            "PhiJIT, PhiVM, and PhiBackpropTuner are tested as one golden-flow surface."
        ),
        "memory_compression": (
            "PULVINI memory compression includes dense fold/unfold, in-place buffers, "
            "sparse_fib_packed strategy, large-array replay, sketch telemetry gates, "
            "and reviewer-facing proof-map evidence."
        ),
        "post_quantum_benchmark": (
            "The post-quantum benchmark covers deterministic passports, exact M32/A5 group "
            "closure, Bures geometry, non-Markovian memory, phi compression, passport "
            "integrity, density-state repair, and performance boundaries."
        ),
        "hardware_scaling": "Apple Silicon MLX/Metal evidence is included when available and non-breaking otherwise.",
        "live_pool_policy": {
            "pool_profile": "open Bitcoin/Stratum routing-auth config; not a HYBA app secret",
            "autoconnect": "disabled unless explicitly enabled by operator",
            "share_submit": "disabled unless explicitly enabled by operator",
            "accepted_share_claim": "requires pool ACK and accepted-share gate evidence",
        },
        "mode": mode,
    }


def _next_actions(mode: Mode, passed: bool) -> list[str]:
    if not passed:
        return [
            "Stop the cutover.",
            "Fix the first failed step in the evidence packet.",
            "Rerun the same local gate from a clean checkout or clean terminal session.",
        ]
    if mode in {"rc", "bitcoin"}:
        return [
            "Preserve this local Bitcoin RC evidence JSON with the release ticket.",
            "Run npm run prod:live:gate with private HYBA app credentials and open Bitcoin pool profiles injected.",
            "Keep HYBA_ENABLE_LIVE_SHARE_SUBMIT=false until explicit approval and pool-side evidence capture are attached.",
        ]
    if mode == "research":
        return [
            "Preserve this research/elevation evidence JSON with the review packet.",
            "Do not treat research evidence as authorization for live share submission or revenue claims.",
        ]
    return [
        "Start production with HYBA_ENABLE_LIVE_SHARE_SUBMIT=false and HYBA_ENABLE_MINING_AUTOCONNECT=false.",
        "Check /bridge/health, backend readiness, authenticated mining status, /api/v1/unified/health, and /api/v1/intelligence/audit.",
        "Only enable live share submission after legal, treasury, security, operations, and CEO approval are attached to HYBA_LIVE_SHARE_APPROVAL_ID.",
        "Capture pool-side accepted/rejected share evidence before making revenue or solvency claims.",
    ]


def _write_report(report: GateReport, artifact: Path) -> str:
    payload = report.to_dict()
    payload["source_artifact_sha256"] = None
    raw = json.dumps(payload, indent=2, sort_keys=True)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    payload["source_artifact_sha256"] = digest
    artifact.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return digest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run local HYBA_FULLSTACK production evidence gate"
    )
    parser.add_argument(
        "--mode",
        choices=("rc", "bitcoin", "research", "live", "command-room"),
        default="command-room",
    )
    parser.add_argument(
        "--continue-on-failure",
        action="store_true",
        help="Run remaining steps after a failure while still returning non-zero",
    )
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
        version="HYBA_FULLSTACK_LOCAL_PRODUCTION_GATE_V8_BITCOIN_DEPLOYMENT",
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
        doctrine=_doctrine(args.mode),
        steps=steps,
        next_operator_actions=_next_actions(args.mode, passed),
    )

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    artifact = (
        ARTIFACT_DIR / f"local_production_gate_{args.mode}_{now.strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    digest = _write_report(report, artifact)
    print(f"Evidence packet: {artifact.relative_to(ROOT)}")
    print(f"Artifact SHA-256: {digest}")
    print(f"Gate status: {status}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
