#!/usr/bin/env python3
"""Final autonomous-mining sovereign gate for production cutover.

This gate distinguishes two different risk classes that must not be collapsed:

1. PYTHIA startup autonomy: boot, heal, optimise, check API/pool readiness,
   validate runtime contracts, and prepare/start the mining search loop under
   configured production controls.
2. Externalising authority: share submission, wallet/pool/credential mutation,
   unbounded parameter escalation, booking/payment actions, or any action that
   changes an external counterparty/system state.

PYTHIA startup autonomy is an intended production behaviour. It does not require
an operator approval ID merely because PYTHIA takes over startup diagnostics and
optimisation. Externalising authority remains separately gated and auditable.

This script does not start mining, connect to a pool, submit shares, mutate
runtime state, or approve autonomous optimisation. It emits a GO/NO-GO evidence
report for human operators.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts" / "mining_readiness"
TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off", ""}

Severity = Literal["critical", "advisory"]
Status = Literal["pass", "fail", "warn"]
Mode = Literal["command-room", "live"]


@dataclass(frozen=True)
class AutonomousGateCheck:
    name: str
    severity: Severity
    status: Status
    summary: str
    detail: str = ""


@dataclass(frozen=True)
class AutonomousSovereignGateReport:
    schema: str
    mode: Mode
    status: str
    passed: bool
    generated_at_utc: str
    checks: list[AutonomousGateCheck] = field(default_factory=list)
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


def _float_env(name: str, default: float) -> float:
    raw = _env(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return float("nan")


def _production_environment_check(mode: Mode) -> AutonomousGateCheck:
    failures: list[str] = []
    if mode == "live":
        if _env("NODE_ENV").lower() != "production":
            failures.append("NODE_ENV=production required for live PYTHIA mining startup")
        if _env("HYBA_ENV").lower() != "production":
            failures.append("HYBA_ENV=production required for live PYTHIA mining startup")
        if not _env_bool("HYBA_ENABLE_LIVE_STRATUM"):
            failures.append(
                "HYBA_ENABLE_LIVE_STRATUM=true required for live pool/API connection checks"
            )
        if not _env_bool("HYBA_ENABLE_AUDIT_LOGGING"):
            failures.append(
                "HYBA_ENABLE_AUDIT_LOGGING=true required for live autonomous startup evidence"
            )
    return AutonomousGateCheck(
        name="production_environment_for_pythia_startup",
        severity="critical",
        status="fail" if failures else "pass",
        summary=(
            "production environment does not permit live PYTHIA startup autonomy"
            if failures
            else "production environment permits live PYTHIA startup autonomy"
        ),
        detail="\n".join(failures),
    )


def _dev_fixture_check() -> AutonomousGateCheck:
    failures: list[str] = []
    if _env_bool("HYBA_ALLOW_DEV_FIXTURES"):
        failures.append("HYBA_ALLOW_DEV_FIXTURES must be false before live PYTHIA mining startup")
    return AutonomousGateCheck(
        name="dev_fixtures_disabled_for_pythia_startup",
        severity="critical",
        status="fail" if failures else "pass",
        summary=(
            "development fixtures could contaminate live PYTHIA mining startup"
            if failures
            else "development fixtures are disabled for live PYTHIA mining startup"
        ),
        detail="\n".join(failures),
    )


def _pythia_startup_autonomy_check(mode: Mode) -> AutonomousGateCheck:
    """Allow PYTHIA's intended startup autonomy while recording evidence."""

    failures: list[str] = []
    warnings: list[str] = []
    enabled = _env_bool("HYBA_ENABLE_AUTONOMOUS_MINING")

    if mode == "live" and not enabled:
        warnings.append(
            "HYBA_ENABLE_AUTONOMOUS_MINING is not true; PYTHIA can still run readiness gates, "
            "but the intended self-heal/optimise/kick-tyres/start-mining path is not explicitly enabled."
        )

    if _env_bool("HYBA_AUTONOMOUS_EXTERNAL_ACTIONS"):
        warnings.append(
            "HYBA_AUTONOMOUS_EXTERNAL_ACTIONS=true detected; external action authority is checked separately."
        )

    status: Status = "fail" if failures else ("warn" if warnings else "pass")
    return AutonomousGateCheck(
        name="pythia_startup_autonomy_allowed",
        severity="critical" if failures else "advisory",
        status=status,
        summary=(
            "PYTHIA startup autonomy is blocked"
            if failures
            else "PYTHIA startup autonomy is allowed as internal production behaviour"
        ),
        detail="\n".join(failures + warnings),
    )


def _external_action_authorisation_check() -> AutonomousGateCheck:
    """Require explicit human authority only for externalising actions."""

    failures: list[str] = []
    external_actions_enabled = _env_bool("HYBA_AUTONOMOUS_EXTERNAL_ACTIONS")
    approval_id = _env("HYBA_AUTONOMOUS_OPERATOR_APPROVAL_ID")
    operator = _env("HYBA_AUTONOMOUS_OPERATOR")
    reason = _env("HYBA_AUTONOMOUS_OPERATOR_REASON")

    if external_actions_enabled:
        if not approval_id:
            failures.append(
                "HYBA_AUTONOMOUS_OPERATOR_APPROVAL_ID is required for autonomous external actions"
            )
        if not operator:
            failures.append("HYBA_AUTONOMOUS_OPERATOR is required for autonomous external actions")
        if not reason:
            failures.append(
                "HYBA_AUTONOMOUS_OPERATOR_REASON is required for autonomous external actions"
            )

    return AutonomousGateCheck(
        name="autonomous_external_action_authorisation",
        severity="critical",
        status="fail" if failures else "pass",
        summary=(
            "autonomous external actions lack explicit human approval"
            if failures
            else "autonomous external actions are disabled or explicitly approved"
        ),
        detail="\n".join(failures),
    )


def _autonomous_bounds_check() -> AutonomousGateCheck:
    failures: list[str] = []
    max_hashrate = _float_env("HYBA_AUTONOMOUS_MAX_HASHRATE_EHS", 100.0)
    max_power = _float_env("HYBA_AUTONOMOUS_MAX_POWER_WATTS", 500.0)
    phi_threshold = _float_env("HYBA_AUTONOMOUS_MIN_PHI_COHERENCE", 0.70)

    if max_hashrate != max_hashrate or max_hashrate <= 0 or max_hashrate > 100.0:
        failures.append("HYBA_AUTONOMOUS_MAX_HASHRATE_EHS must be >0 and <=100.0")
    if max_power != max_power or max_power <= 0 or max_power > 500.0:
        failures.append("HYBA_AUTONOMOUS_MAX_POWER_WATTS must be >0 and <=500.0")
    if phi_threshold != phi_threshold or phi_threshold < 0.70 or phi_threshold > 1.0:
        failures.append("HYBA_AUTONOMOUS_MIN_PHI_COHERENCE must be between 0.70 and 1.0")

    return AutonomousGateCheck(
        name="autonomous_runtime_bounds",
        severity="critical",
        status="fail" if failures else "pass",
        summary="autonomous bounds are unsafe"
        if failures
        else "autonomous bounds are within configured production limits",
        detail="\n".join(failures),
    )


def _share_submit_check() -> AutonomousGateCheck:
    failures: list[str] = []
    if _env_bool("HYBA_ENABLE_LIVE_SHARE_SUBMIT") and not _env("HYBA_LIVE_SHARE_APPROVAL_ID"):
        failures.append("HYBA_ENABLE_LIVE_SHARE_SUBMIT=true requires HYBA_LIVE_SHARE_APPROVAL_ID")
    return AutonomousGateCheck(
        name="live_share_submit_authorisation",
        severity="critical",
        status="fail" if failures else "pass",
        summary="live share submit is not authorised"
        if failures
        else "live share submit is either disabled or explicitly approved",
        detail="\n".join(failures),
    )


def _audit_evidence_check() -> AutonomousGateCheck:
    warnings: list[str] = []
    if _is_falseish("HYBA_ENABLE_AUDIT_LOGGING"):
        warnings.append("audit logging is disabled or unset")
    if not _env("HYBA_AUTONOMOUS_OPERATOR_APPROVAL_ID"):
        warnings.append(
            "operator approval ID missing; this is acceptable for PYTHIA startup autonomy, "
            "but not for autonomous external actions or separately approved live share submission"
        )
    return AutonomousGateCheck(
        name="autonomous_audit_evidence",
        severity="advisory",
        status="warn" if warnings else "pass",
        summary="autonomous audit evidence has advisory gaps"
        if warnings
        else "autonomous audit evidence fields are present",
        detail="\n".join(warnings),
    )


def run_gate(mode: Mode) -> AutonomousSovereignGateReport:
    checks = [
        _production_environment_check(mode),
        _dev_fixture_check(),
        _pythia_startup_autonomy_check(mode),
        _external_action_authorisation_check(),
        _autonomous_bounds_check(),
        _share_submit_check(),
        _audit_evidence_check(),
    ]
    critical_failures = [
        check for check in checks if check.severity == "critical" and check.status == "fail"
    ]
    passed = not critical_failures
    actions: list[str] = []
    if not passed:
        actions.extend(
            [
                "Do not proceed to live mining cutover until critical failures are resolved.",
                "Fix production env flags, disable dev fixtures, keep startup autonomy internal, and attach approval IDs for externalising actions and live share submission.",
            ]
        )
    else:
        actions.extend(
            [
                "PYTHIA may boot, heal, optimise, check APIs/pool readiness, and run the mining startup/search path under command-room observation.",
                "Monitor subscribe -> authorize -> notify -> search -> local validate -> submit gate -> pool ACK when share submission is enabled and approved.",
                "Keep HYBA_AUTONOMOUS_EXTERNAL_ACTIONS=false unless a human approval ID/operator/reason is attached.",
                "HYBA_ENABLE_LIVE_SHARE_SUBMIT=true is permitted when HYBA_LIVE_SHARE_APPROVAL_ID is present and audit logging is enabled.",
            ]
        )
    return AutonomousSovereignGateReport(
        schema="HYBA_AUTONOMOUS_MINING_SOVEREIGN_GATE_V2",
        mode=mode,
        status="GO" if passed else "NO_GO",
        passed=passed,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        checks=checks,
        next_operator_actions=actions,
    )


def _write_report(report: AutonomousSovereignGateReport) -> Path:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = ARTIFACT_DIR / f"autonomous_sovereign_gate_{report.mode}_{stamp}.json"
    path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the final autonomous-mining sovereign GO/NO-GO gate."
    )
    parser.add_argument("--mode", choices=["command-room", "live"], default="command-room")
    parser.add_argument(
        "--write", action="store_true", help="Write JSON report to artifacts/mining_readiness/."
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
