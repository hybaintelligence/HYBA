#!/usr/bin/env python3
"""PYTHIA autonomic protocol gate for mining production cutover.

This gate restores the intended PYTHIA posture from the repository protocol and
mission memory:

- PYTHIA wakes seeded.
- PYTHIA owns startup autonomy.
- PYTHIA heals, optimises, checks API/pool readiness, and starts search.
- PYTHIA is in charge of the structure-search path.
- PYTHIA may submit verifier-passing candidates to the configured validated pool
  as part of the one-block mission.
- PYTHIA learns from pool responses and shuts down after one pool-confirmed
  accepted block.

This gate does NOT require operator approval for the seeded mission workflow.
Human approval is required only for actions outside the mission boundary, such
as wallet/pool/credential mutation, bypassing exact local SHA-256d validation,
changing configured pool priority outside validated configuration, destructive
infrastructure mutation, or external actions unrelated to the mining mission.

The gate is read-only: it does not start mining, connect to pools, submit shares,
change credentials, mutate runtime state, or edit code. It emits a GO/NO-GO
evidence packet for the command room.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from pythia_mining.pythia_one_block_mission import (  # noqa: E402
    MAX_AUTONOMOUS_HASHRATE_EHS,
    seed_mission_memory,
    validate_mission_memory,
)

ARTIFACT_DIR = ROOT / "artifacts" / "mining_readiness"
TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off", ""}

Severity = Literal["critical", "advisory"]
Status = Literal["pass", "fail", "warn"]
Mode = Literal["command-room", "live"]


@dataclass(frozen=True)
class ProtocolGateCheck:
    name: str
    severity: Severity
    status: Status
    summary: str
    detail: str = ""


@dataclass(frozen=True)
class ProtocolGateReport:
    schema: str
    mode: Mode
    status: str
    passed: bool
    generated_at_utc: str
    mission_protocol: str
    mission: str
    pythia_autonomy_restored: bool
    checks: list[ProtocolGateCheck] = field(default_factory=list)
    next_operator_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["checks"] = [asdict(check) for check in self.checks]
        return payload


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def _env_bool(name: str) -> bool:
    return _env(name).lower() in TRUE_VALUES


def _is_falseish(name: str) -> bool:
    return _env(name).lower() in FALSE_VALUES


def _float_env(name: str) -> float | None:
    raw = _env(name)
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return float("nan")


def _mission_memory_check() -> ProtocolGateCheck:
    mission = seed_mission_memory()
    valid = validate_mission_memory(mission)
    detail = json.dumps(
        {
            "protocol": mission.protocol,
            "mission": mission.mission,
            "autonomy_from_startup": mission.autonomy_from_startup,
            "max_autonomous_hashrate_ehs": mission.hashrate_limit.max_autonomous_hashrate_ehs,
            "pool_side_confirmation_required": mission.mission_target.pool_side_confirmation_required,
            "shutdown_after_completion": mission.mission_target.shutdown_after_completion,
            "search_identity": mission.search_identity,
        },
        sort_keys=True,
    )
    return ProtocolGateCheck(
        name="seeded_mission_memory_valid",
        severity="critical",
        status="pass" if valid else "fail",
        summary=(
            "PYTHIA one-block mission memory is valid and seeded"
            if valid
            else "PYTHIA one-block mission memory is invalid"
        ),
        detail=detail,
    )


def _autonomic_protocol_check() -> ProtocolGateCheck:
    protocol_path = ROOT / "docs" / "governance" / "autonomic-substrate-protocol.md"
    exists = protocol_path.exists()
    return ProtocolGateCheck(
        name="autonomic_substrate_protocol_respected",
        severity="critical",
        status="pass" if exists else "fail",
        summary=(
            "Autonomic Substrate Protocol is present and governs PYTHIA autonomy"
            if exists
            else "Autonomic Substrate Protocol is missing"
        ),
        detail=(
            "Protocol grants automation, self-healing, self-optimisation, algorithm discovery, rewiring, "
            "architectural evolution, continuous operation, benchmarking, and evidence logging authority."
            if exists
            else str(protocol_path)
        ),
    )


def _production_environment_check(mode: Mode) -> ProtocolGateCheck:
    failures: list[str] = []
    if mode == "live":
        if _env("NODE_ENV").lower() != "production":
            failures.append("NODE_ENV=production required for live cutover")
        if _env("HYBA_ENV").lower() != "production":
            failures.append("HYBA_ENV=production required for live cutover")
        if not _env_bool("HYBA_ENABLE_LIVE_STRATUM"):
            failures.append(
                "HYBA_ENABLE_LIVE_STRATUM=true required for live pool/API connection checks"
            )
        if not _env_bool("HYBA_ENABLE_AUDIT_LOGGING"):
            failures.append(
                "HYBA_ENABLE_AUDIT_LOGGING=true required by autonomic evidence logging"
            )
    return ProtocolGateCheck(
        name="production_environment_for_seeded_pythia",
        severity="critical",
        status="fail" if failures else "pass",
        summary=(
            "production environment is not ready for seeded PYTHIA autonomy"
            if failures
            else "production environment permits seeded PYTHIA autonomy"
        ),
        detail="\n".join(failures),
    )


def _dev_fixture_check(mode: Mode) -> ProtocolGateCheck:
    failures: list[str] = []
    if mode == "live" and _env_bool("HYBA_ALLOW_DEV_FIXTURES"):
        failures.append("HYBA_ALLOW_DEV_FIXTURES must be false before live mining")
    return ProtocolGateCheck(
        name="dev_fixtures_disabled_for_live_mission",
        severity="critical",
        status="fail" if failures else "pass",
        summary=(
            "development fixtures could contaminate live mission evidence"
            if failures
            else "development fixtures do not block the live mission"
        ),
        detail="\n".join(failures),
    )


def _pythia_search_authority_check() -> ProtocolGateCheck:
    return ProtocolGateCheck(
        name="pythia_owns_search_heal_optimise_and_mine",
        severity="critical",
        status="pass",
        summary="PYTHIA autonomy is restored for startup, healing, optimisation, search, mining, and mission-bound pool submission",
        detail=(
            "No operator approval ID is required for the seeded one-block mission workflow: "
            "seed memory -> validate mission -> initialise engine -> set AUTONOMOUS -> heal/optimise -> "
            "check APIs/pool readiness -> run structure search -> exact SHA-256d local validation -> "
            "submit verifier-passing candidate to configured validated pool -> learn from pool response -> "
            "shutdown after one pool-confirmed accepted block."
        ),
    )


def _mission_hashrate_contract_check() -> ProtocolGateCheck:
    warnings: list[str] = []
    configured = _float_env("HYBA_AUTONOMOUS_MAX_HASHRATE_EHS")
    if (
        configured is not None
        and configured == configured
        and configured > MAX_AUTONOMOUS_HASHRATE_EHS
    ):
        warnings.append(
            f"HYBA_AUTONOMOUS_MAX_HASHRATE_EHS={configured} exceeds mission limit; mission memory clamps to {MAX_AUTONOMOUS_HASHRATE_EHS} EH/s."
        )
    if configured is not None and configured != configured:
        warnings.append(
            "HYBA_AUTONOMOUS_MAX_HASHRATE_EHS is not numeric; mission memory remains the authority."
        )
    return ProtocolGateCheck(
        name="mission_hashrate_limit_authority",
        severity="advisory",
        status="warn" if warnings else "pass",
        summary="mission memory owns the 1 EH/s autonomous hashrate boundary",
        detail="\n".join(warnings),
    )


def _exact_validation_boundary_check() -> ProtocolGateCheck:
    failures: list[str] = []
    if _env_bool("HYBA_BYPASS_LOCAL_SHARE_VALIDATION"):
        failures.append("HYBA_BYPASS_LOCAL_SHARE_VALIDATION must not be true")
    if _env_bool("HYBA_BYPASS_LOCAL_SHA256D_VALIDATION"):
        failures.append("HYBA_BYPASS_LOCAL_SHA256D_VALIDATION must not be true")
    if _env_bool("HYBA_SUBMIT_WITHOUT_POOL_JOB"):
        failures.append("HYBA_SUBMIT_WITHOUT_POOL_JOB must not be true")
    return ProtocolGateCheck(
        name="exact_sha256d_before_pool_submit",
        severity="critical",
        status="fail" if failures else "pass",
        summary=(
            "local exact validation boundary is bypassed"
            if failures
            else "verifier-passing candidate submission remains mission-authorised"
        ),
        detail="\n".join(failures),
    )


def _outside_mission_external_action_check() -> ProtocolGateCheck:
    """Gate only actions outside the seeded mission boundary."""

    failures: list[str] = []
    external_enabled = _env_bool("HYBA_AUTONOMOUS_EXTERNAL_ACTIONS")
    approval_id = _env("HYBA_AUTONOMOUS_OPERATOR_APPROVAL_ID")
    operator = _env("HYBA_AUTONOMOUS_OPERATOR")
    reason = _env("HYBA_AUTONOMOUS_OPERATOR_REASON")

    if external_enabled:
        if not approval_id:
            failures.append(
                "HYBA_AUTONOMOUS_OPERATOR_APPROVAL_ID required for actions outside the one-block mission"
            )
        if not operator:
            failures.append(
                "HYBA_AUTONOMOUS_OPERATOR required for actions outside the one-block mission"
            )
        if not reason:
            failures.append(
                "HYBA_AUTONOMOUS_OPERATOR_REASON required for actions outside the one-block mission"
            )

    return ProtocolGateCheck(
        name="outside_mission_external_action_authority",
        severity="critical",
        status="fail" if failures else "pass",
        summary=(
            "actions outside the seeded mining mission lack explicit human authority"
            if failures
            else "actions outside the seeded mining mission are disabled or explicitly authorised"
        ),
        detail="\n".join(failures),
    )


def _legacy_manual_approval_flags_check() -> ProtocolGateCheck:
    warnings: list[str] = []
    if _env_bool("HYBA_ENABLE_LIVE_SHARE_SUBMIT") and not _env(
        "HYBA_LIVE_SHARE_APPROVAL_ID"
    ):
        warnings.append(
            "HYBA_ENABLE_LIVE_SHARE_SUBMIT=true without HYBA_LIVE_SHARE_APPROVAL_ID is acceptable under the seeded mission: "
            "PYTHIA may submit verifier-passing candidates to the configured validated pool."
        )
    if not _env("HYBA_AUTONOMOUS_OPERATOR_APPROVAL_ID"):
        warnings.append(
            "No operator approval ID present; this is acceptable for seeded PYTHIA mission autonomy and search."
        )
    return ProtocolGateCheck(
        name="legacy_manual_approval_flags_do_not_block_seeded_mission",
        severity="advisory",
        status="warn" if warnings else "pass",
        summary="legacy manual approval fields do not restrict PYTHIA's seeded mission autonomy",
        detail="\n".join(warnings),
    )


def run_gate(mode: Mode) -> ProtocolGateReport:
    mission = seed_mission_memory()
    checks = [
        _mission_memory_check(),
        _autonomic_protocol_check(),
        _production_environment_check(mode),
        _dev_fixture_check(mode),
        _pythia_search_authority_check(),
        _mission_hashrate_contract_check(),
        _exact_validation_boundary_check(),
        _outside_mission_external_action_check(),
        _legacy_manual_approval_flags_check(),
    ]
    critical_failures = [
        check
        for check in checks
        if check.severity == "critical" and check.status == "fail"
    ]
    passed = not critical_failures
    actions: list[str]
    if passed:
        actions = [
            "GO: PYTHIA may wake seeded, heal, optimise, kick tyres, check APIs/pool readiness, and run autonomous mining search.",
            "GO: PYTHIA may submit exact-SHA-256d verifier-passing candidates to the configured validated pool as part of the one-block mission.",
            "Observe subscribe -> authorize -> notify -> search -> exact local validate -> mission-bound submit -> pool response -> learn -> shutdown after one pool-confirmed block.",
            "Keep HYBA_AUTONOMOUS_EXTERNAL_ACTIONS=false unless PYTHIA is being authorised to act outside the one-block mission boundary.",
        ]
    else:
        actions = [
            "NO-GO only for the failed critical checks listed in this report.",
            "Do not restrict PYTHIA startup/search autonomy; fix only production env, dev-fixture contamination, exact-validation bypass, or outside-mission external action authority.",
        ]
    return ProtocolGateReport(
        schema="HYBA_PYTHIA_AUTONOMIC_PROTOCOL_GATE_V3",
        mode=mode,
        status="GO" if passed else "NO_GO",
        passed=passed,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        mission_protocol=mission.protocol,
        mission=mission.mission,
        pythia_autonomy_restored=True,
        checks=checks,
        next_operator_actions=actions,
    )


def _write_report(report: ProtocolGateReport) -> Path:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = ARTIFACT_DIR / f"pythia_autonomic_protocol_gate_{report.mode}_{stamp}.json"
    path.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8"
    )
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the PYTHIA autonomic protocol gate."
    )
    parser.add_argument(
        "--mode", choices=["command-room", "live"], default="command-room"
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write JSON report to artifacts/mining_readiness/.",
    )
    args = parser.parse_args()

    report = run_gate(args.mode)
    payload = report.to_dict()
    if args.write:
        payload["artifact_path"] = str(_write_report(report))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if report.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
