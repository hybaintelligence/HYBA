#!/usr/bin/env python3
"""Validate pool profile contracts before a live PYTHIA/PULVINI cutover.

This check is intentionally offline: it validates that loaded pool profiles are
safe for the currently implemented job-flow path before the operator starts the
runtime. It does not connect to pools, submit shares, or touch credentials.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
ARTIFACT_DIR = ROOT / "artifacts" / "mining_readiness"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

Mode = Literal["prepare", "live"]
SUPPORTED_ROTATION_POOLS = {"viabtc", "braiins", "nicehash", "ckpool"}
JOB_CAPABLE_STRATUM_VERSIONS = {1}


@dataclass(frozen=True)
class PoolProfileFinding:
    pool_id: str
    severity: str
    status: str
    message: str
    detail: dict[str, object]


@dataclass(frozen=True)
class PoolProfileReport:
    status: str
    mode: Mode
    loaded_profile_count: int
    findings: list[PoolProfileFinding]
    generated_at: float

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["findings"] = [asdict(finding) for finding in self.findings]
        return payload


def _redact_profile(profile) -> dict[str, object]:
    return {
        "pool_id": profile.pool_id,
        "name": profile.name,
        "url": profile.url,
        "username": "<configured>" if profile.username else "",
        "password": "<configured>" if profile.password else "",
        "stratum_version": profile.stratum_version,
        "priority": profile.priority,
        "tls_required": profile.tls_required,
    }


def build_report(mode: Mode) -> PoolProfileReport:
    from pythia_mining.pool_profiles import DEFAULT_POOL_SPECS, load_pool_profiles

    findings: list[PoolProfileFinding] = []
    missing_supported = sorted(SUPPORTED_ROTATION_POOLS - set(DEFAULT_POOL_SPECS))
    if missing_supported:
        findings.append(
            PoolProfileFinding(
                pool_id="default_specs",
                severity="critical",
                status="fail",
                message="missing default rotation pool specs",
                detail={"missing": missing_supported},
            )
        )

    braiins = DEFAULT_POOL_SPECS.get("braiins", {})
    if int(braiins.get("stratum_version", 0)) != 1 or not str(braiins.get("url", "")).startswith(
        "stratum+tcp://"
    ):
        findings.append(
            PoolProfileFinding(
                pool_id="braiins",
                severity="critical",
                status="fail",
                message="Braiins default must be Stratum v1 job-flow capable",
                detail={"default_spec": braiins},
            )
        )

    profiles = load_pool_profiles()
    if mode == "live" and not profiles:
        findings.append(
            PoolProfileFinding(
                pool_id="all",
                severity="critical",
                status="fail",
                message="live mode requires at least one loaded pool profile",
                detail={},
            )
        )

    if mode == "prepare" and not profiles:
        findings.append(
            PoolProfileFinding(
                pool_id="all",
                severity="advisory",
                status="warn",
                message="no pool profiles loaded; acceptable for preparation, not for live cutover",
                detail={},
            )
        )

    for profile in profiles:
        detail = _redact_profile(profile)
        if "@" in profile.url:
            findings.append(
                PoolProfileFinding(
                    pool_id=profile.pool_id,
                    severity="critical",
                    status="fail",
                    message="profile URL must not expose inline credentials after normalization",
                    detail=detail,
                )
            )
        if not profile.username or not profile.password:
            findings.append(
                PoolProfileFinding(
                    pool_id=profile.pool_id,
                    severity="critical",
                    status="fail",
                    message="profile is missing authorize credentials",
                    detail=detail,
                )
            )
        if int(profile.stratum_version) not in JOB_CAPABLE_STRATUM_VERSIONS:
            findings.append(
                PoolProfileFinding(
                    pool_id=profile.pool_id,
                    severity="critical",
                    status="fail",
                    message="profile is not job-flow capable with the current daemon; use Stratum v1 until v2 channel/job flow is implemented",
                    detail=detail,
                )
            )
        if profile.pool_id == "braiins" and int(profile.stratum_version) != 1:
            findings.append(
                PoolProfileFinding(
                    pool_id=profile.pool_id,
                    severity="critical",
                    status="fail",
                    message="Braiins must be configured with HYBA_POOL_BRAIINS_STRATUM_VERSION=1 for mining.notify job flow",
                    detail=detail,
                )
            )

    critical_failed = any(f.severity == "critical" and f.status == "fail" for f in findings)
    return PoolProfileReport(
        status="blocked" if critical_failed else "ready",
        mode=mode,
        loaded_profile_count=len(profiles),
        findings=findings,
        generated_at=time.time(),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("prepare", "live"), default="prepare")
    args = parser.parse_args(argv)

    report = build_report(args.mode)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    artifact = ARTIFACT_DIR / f"pool_profile_job_flow_{args.mode}_{int(time.time())}.json"
    artifact.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    for finding in report.findings:
        print(
            f"[{finding.status.upper()}] {finding.severity.upper()} {finding.pool_id}: {finding.message}"
        )
        if finding.status == "fail":
            print(json.dumps(finding.detail, indent=2, sort_keys=True))
    print(f"Pool profile job-flow status: {report.status}")
    print(f"Loaded profiles: {report.loaded_profile_count}")
    print(f"Report: {artifact.relative_to(ROOT)}")
    return 0 if report.status == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
