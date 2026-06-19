#!/usr/bin/env python3
"""Operational production-readiness doctor for PYTHIA/PULVINI mining.

This is intentionally different from a broad forensic/science gate. It answers one
operator question: can this checkout be deployed for a controlled mining run without
known software-mining or Bitcoin-mining contract failures?

Only CRITICAL failures block. Advisory items are recorded but do not turn the gate
red. Live share submission and accepted-share/revenue claims remain separate, explicit
operator actions.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import inspect
import json
import os
import platform
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
ARTIFACT_DIR = ROOT / "artifacts" / "mining_readiness"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

Mode = Literal["prepare", "command-room", "live"]
Severity = Literal["critical", "advisory"]
Status = Literal["pass", "fail", "warn", "skip"]
TRUE_VALUES = {"1", "true", "yes", "on"}
POOL_IDS = ("VIABTC", "NICEHASH", "BRAIINS", "CKPOOL", "STRATUMV2")


@dataclass(frozen=True)
class CheckResult:
    name: str
    severity: Severity
    status: Status
    summary: str
    detail: str = ""
    duration_seconds: float = 0.0


@dataclass(frozen=True)
class ReadinessReport:
    version: str
    mode: Mode
    status: str
    passed: bool
    generated_at_utc: str
    host: dict[str, str]
    environment_summary: dict[str, str]
    checks: list[CheckResult] = field(default_factory=list)
    next_operator_actions: list[str] = field(default_factory=list)
    source_artifact_sha256: str | None = None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["checks"] = [asdict(check) for check in self.checks]
        return payload


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in TRUE_VALUES


def _tail(text: str, limit: int = 5000) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def _run(command: list[str], *, timeout: int = 300) -> tuple[int, str, str, float]:
    start = time.monotonic()
    try:
        completed = subprocess.run(
            command if sys.platform != "win32" else ["cmd", "/c"] + command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            env=os.environ.copy(),
        )
        return (
            completed.returncode,
            _tail(completed.stdout),
            _tail(completed.stderr),
            time.monotonic() - start,
        )
    except subprocess.TimeoutExpired as exc:
        return (
            124,
            _tail(exc.stdout or ""),
            _tail(exc.stderr or "command timed out"),
            time.monotonic() - start,
        )


def _configured_pools() -> list[str]:
    configured: list[str] = []
    for pool in POOL_IDS:
        prefix = f"HYBA_POOL_{pool}_"
        if any(name.startswith(prefix) and value for name, value in os.environ.items()):
            configured.append(pool)
    return configured


def _environment_summary() -> dict[str, str]:
    fields = [
        "NODE_ENV",
        "HYBA_ENV",
        "HYBA_ALLOW_DEV_FIXTURES",
        "HYBA_ENABLE_LIVE_STRATUM",
        "HYBA_ENABLE_MINING_AUTOCONNECT",
        "HYBA_ENABLE_LIVE_SHARE_SUBMIT",
        "HYBA_ENABLE_AUDIT_LOGGING",
        "HYBA_LIVE_SHARE_APPROVAL_ID",
        "HYBA_MINING_MAX_SOLVER_ITERATIONS",
        "HYBA_MINING_SEARCH_TIMEOUT_CAP_SECONDS",
        "PULVINI_BACKEND_URL",
    ]
    summary: dict[str, str] = {}
    for field_name in fields:
        value = os.getenv(field_name)
        if value is None:
            summary[field_name] = "<unset>"
        elif any(
            marker in field_name for marker in ("SECRET", "PASSWORD", "TOKEN", "KEY", "CREDENTIAL")
        ):
            summary[field_name] = "<redacted>"
        elif value == "":
            summary[field_name] = "<empty>"
        else:
            summary[field_name] = value
    summary["configured_pool_profiles"] = ",".join(_configured_pools()) or "<none>"
    return summary


def _check_required_files() -> CheckResult:
    start = time.monotonic()
    required = [
        "python_backend/pythia_mining/phi_unified_mining_engine.py",
        "python_backend/pythia_mining/ai_optimizer.py",
        "python_backend/pythia_mining/consciousness_engine.py",
        "python_backend/pythia_mining/hendrix_phi_solver.py",
        "python_backend/pythia_mining/pulvini_compressed_solver.py",
        "python_backend/pythia_mining/pulvini_nonce_compression.py",
        "python_backend/pythia_mining/mining_validation.py",
        "python_backend/pythia_mining/stratum_client.py",
        "python_backend/pythia_mining/mass_gap_protector.py",
        "tests/test_phi_unified_mining_engine.py",
        "tests/test_unified_mining_api_surface.py",
        "tests/test_stratum_share_acceptance_e2e.py",
        "tests/test_pulvini_nonce_compression.py",
        # gap-closure test surfaces — absence blocks deployment preparation
        "tests/test_gap_phi_search_vs_random.py",
        "tests/test_gap_reflexive_loop_live_application.py",
        "tests/test_gap_local_pow_validation.py",
        "tests/test_gap_pool_acceptance_rate.py",
        "tests/test_gap_anti_simulation_adversarial.py",
    ]
    missing = [path for path in required if not (ROOT / path).exists()]
    return CheckResult(
        name="required_mining_surfaces_present",
        severity="critical",
        status="fail" if missing else "pass",
        summary="missing canonical mining files" if missing else "canonical mining files present",
        detail="\n".join(missing),
        duration_seconds=time.monotonic() - start,
    )


def _check_unified_engine_contract() -> CheckResult:
    start = time.monotonic()
    try:
        from pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine
        from pythia_mining.stratum_client import MiningJob

        job = MiningJob(
            job_id="doctor-job",
            prevhash="00" * 32,
            coinbase_parts=("", ""),
            merkle_branch=[],
            version="20000000",
            nbits="1d00ffff",
            ntime="5f5e1000",
            target=2**240,
            extranonce1="abcd",
            extranonce2_size=4,
        )
        engine = UnifiedMiningEngine()
        result = asyncio.run(engine.search(job))
        metrics = engine.solver.get_metrics()
        state = engine.get_unified_state()
        failures: list[str] = []
        if result.nonce is None or not (0 <= int(result.nonce) <= 2**32 - 1):
            failures.append("unified engine did not return a uint32 candidate nonce")
        if metrics.get("nonce_space_contract") != "pulvini_phi_compressed_pre_search":
            failures.append("optimizer did not configure PULVINI compressed search")
        if metrics.get("complete_nonce_coverage") is not True:
            failures.append("PULVINI nonce plan does not report complete coverage")
        if metrics.get("overlap_free_nonce_coverage") is not True:
            failures.append("PULVINI nonce plan does not report overlap-free coverage")
        if (
            metrics.get("compressed_working_set_size") is None
            or metrics.get("compressed_working_set_size") <= 0
        ):
            failures.append("PULVINI compressed working set is not configured")
        if (
            state["proofs"].get("sha256d_external_oracle")
            != "bitcoin_header_double_sha256_pool_target"
        ):
            failures.append("SHA-256d external oracle boundary is missing")
        return CheckResult(
            name="unified_engine_pulvini_contract",
            severity="critical",
            status="fail" if failures else "pass",
            summary="unified engine contract failed"
            if failures
            else "unified engine routes through compressed PULVINI search and SHA-256d verification boundary",
            detail="\n".join(failures)
            if failures
            else json.dumps(
                {
                    "nonce": result.nonce,
                    "metrics": {
                        "compressed_working_set_size": metrics.get("compressed_working_set_size"),
                        "last_solve_iterations": metrics.get("last_solve_iterations"),
                    },
                },
                sort_keys=True,
            ),
            duration_seconds=time.monotonic() - start,
        )
    except Exception as exc:  # pragma: no cover - operational diagnostic path
        return CheckResult(
            name="unified_engine_pulvini_contract",
            severity="critical",
            status="fail",
            summary="unified engine contract raised an exception",
            detail=repr(exc),
            duration_seconds=time.monotonic() - start,
        )


def _check_bitcoin_mining_contracts() -> CheckResult:
    start = time.monotonic()
    try:
        from pythia_mining.mining_validation import (
            compact_to_target,
            hash256,
            uint32_little_endian_hex,
        )
        from pythia_mining.stratum_client import StratumClient

        failures: list[str] = []
        if hash256(b"abc") != hashlib.sha256(hashlib.sha256(b"abc").digest()).digest():
            failures.append("hash256 is not Bitcoin double-SHA256")
        if uint32_little_endian_hex(1, field="nonce") != "01000000":
            failures.append("uint32 nonce encoding is not little-endian")
        if compact_to_target("1d00ffff") <= 0:
            failures.append("compact target conversion returned non-positive target")
        source = inspect.getsource(StratumClient.submit_validated_share)
        required_tokens = {
            "stale_job": "stale jobs must be rejected before submit",
            "live_share_submit_disabled": "live pool submit must remain operator gated",
            "validate_share": "local SHA-256d validation must run before submit",
            "submit_result.accepted": "accepted counter must follow pool ACK result",
            "self.shares_accepted += 1": "accepted shares must not increment without explicit accepted branch",
            "invalid_pool_response_structure": "malformed pool responses must not be treated as accepted",
        }
        for token, message in required_tokens.items():
            if token not in source:
                failures.append(message)
        return CheckResult(
            name="bitcoin_and_stratum_pitfall_contracts",
            severity="critical",
            status="fail" if failures else "pass",
            summary="Bitcoin/Stratum contract failed"
            if failures
            else "byte order, compact target, local validation, stale jobs, pool ACK, and malformed response pitfalls are covered",
            detail="\n".join(failures),
            duration_seconds=time.monotonic() - start,
        )
    except Exception as exc:  # pragma: no cover - operational diagnostic path
        return CheckResult(
            name="bitcoin_and_stratum_pitfall_contracts",
            severity="critical",
            status="fail",
            summary="Bitcoin/Stratum contract check raised an exception",
            detail=repr(exc),
            duration_seconds=time.monotonic() - start,
        )


def _check_environment(mode: Mode) -> list[CheckResult]:
    start = time.monotonic()
    failures: list[str] = []
    warnings: list[str] = []

    node_env = os.getenv("NODE_ENV", "").strip().lower()
    hyba_env = os.getenv("HYBA_ENV", "").strip().lower()
    live_submit = _env_bool("HYBA_ENABLE_LIVE_SHARE_SUBMIT")
    approval_id = os.getenv("HYBA_LIVE_SHARE_APPROVAL_ID", "").strip()
    pools = _configured_pools()

    if _env_bool("HYBA_ALLOW_DEV_FIXTURES") and (
        node_env == "production" or hyba_env == "production"
    ):
        failures.append("HYBA_ALLOW_DEV_FIXTURES must be false in production")
    if live_submit and not approval_id:
        failures.append("HYBA_ENABLE_LIVE_SHARE_SUBMIT=true requires HYBA_LIVE_SHARE_APPROVAL_ID")
    if _env_bool("HYBA_ENABLE_MINING_AUTOCONNECT"):
        warnings.append(
            "HYBA_ENABLE_MINING_AUTOCONNECT is enabled; operator should confirm this is intentional"
        )

    reflexive_enabled = _env_bool("HYBA_ENABLE_REFLEXIVE_DAEMON")
    persistence_path = os.getenv("HYBA_ONTOLOGICAL_STATE_PATH") or os.getenv(
        "HYBA_ONTOLOGICAL_PERSISTENCE_PATH"
    )
    if reflexive_enabled and not _env_bool("HYBA_ENABLE_AUDIT_LOGGING"):
        warnings.append(
            "HYBA_ENABLE_REFLEXIVE_DAEMON=true should be paired with HYBA_ENABLE_AUDIT_LOGGING=true for forensic traceability"
        )
    if persistence_path:
        path = Path(persistence_path)
        sensitive_fragments = ("/tmp", ".env", "secret", "credential", "token")
        if any(fragment in persistence_path.lower() for fragment in sensitive_fragments):
            failures.append(
                "HYBA ontological persistence path must not point at temp, .env, or secret-bearing locations"
            )
        if path.exists():
            mode_bits = path.stat().st_mode & 0o777
            if mode_bits & 0o077:
                failures.append(
                    "HYBA ontological persistence path must not be group/world accessible"
                )

    if mode == "live":
        if node_env != "production":
            failures.append("NODE_ENV=production is required in live mode")
        if hyba_env != "production":
            failures.append("HYBA_ENV=production is required in live mode")
        if not _env_bool("HYBA_ENABLE_LIVE_STRATUM"):
            failures.append("HYBA_ENABLE_LIVE_STRATUM=true is required in live mode")
        if not _env_bool("HYBA_ENABLE_AUDIT_LOGGING"):
            failures.append("HYBA_ENABLE_AUDIT_LOGGING=true is required in live mode")
        if not pools:
            failures.append("at least one HYBA_POOL_<ID>_* profile is required in live mode")
    else:
        if node_env != "production" or hyba_env != "production":
            warnings.append(
                "production env flags are not both set; acceptable for code preparation, not for live cutover"
            )
        if not pools:
            warnings.append(
                "no pool profile configured; acceptable for preparation, blocks actual live mining"
            )

    return [
        CheckResult(
            name="operator_environment_safety",
            severity="critical",
            status="fail" if failures else "pass",
            summary="unsafe operator environment"
            if failures
            else "no critical unsafe live-mining flags detected",
            detail="\n".join(failures),
            duration_seconds=time.monotonic() - start,
        ),
        CheckResult(
            name="operator_environment_advisories",
            severity="advisory",
            status="warn" if warnings else "pass",
            summary="operator environment has live-readiness advisories"
            if warnings
            else "no operator environment advisories",
            detail="\n".join(warnings),
            duration_seconds=time.monotonic() - start,
        ),
    ]


def _check_claim_boundary_contract() -> CheckResult:
    """Verify source-level claim boundaries are in place.

    The deployment contract requires that:
    - hashrate telemetry is never fabricated (capacity_source guard present)
    - benchmark results are labelled projection_only when no measured input exists
    - the anti-simulation MassGapProtector is importable and exercisable
    - no revenue or financial outcome is asserted in telemetry paths
    """
    start = time.monotonic()
    failures: list[str] = []
    try:
        from pythia_mining.quantum_solver import DodecahedralQuantumSolver

        solver = DodecahedralQuantumSolver()
        metrics = solver.get_metrics()
        if metrics.get("telemetry_source") != "derived_runtime_state":
            failures.append(
                "solver telemetry_source must be 'derived_runtime_state', not a fabricated label"
            )
        if metrics.get("capacity_source") not in ("not_configured", "configured_estimate"):
            failures.append(
                "solver capacity_source must be 'not_configured' or 'configured_estimate'"
            )
        if metrics.get("hashrate_ehs") is not None:
            failures.append("unconfigured solver must not report a non-None hashrate_ehs")
    except Exception as exc:
        failures.append(f"solver import/metrics raised: {exc}")

    try:
        from pythia_mining.phi_scaling_engine import benchmark_vs_asic

        proj = benchmark_vs_asic(measured_hashes_per_second=None)
        if proj.get("benchmark_mode") != "projection_only":
            failures.append("benchmark without measured input must be labelled 'projection_only'")
        if proj.get("effective_hashes_per_second") is not None:
            failures.append("projection_only benchmark must not report effective_hashes_per_second")
        if proj.get("projected_vs_asic_ratio") is not None:
            failures.append("projection_only benchmark must not report projected_vs_asic_ratio")
    except Exception as exc:
        failures.append(f"benchmark_vs_asic import/call raised: {exc}")

    try:
        from pythia_mining.mass_gap_protector import MassGapProtector

        protector = MassGapProtector()
        # Insufficient data must return 0.0 — the safe default
        score = protector.get_authenticity_score([0.1] * 10)
        if score != 0.0:
            failures.append("MassGapProtector must return 0.0 for < 32 samples")
        result = protector.verify_telemetry([0.1] * 10)
        if result.get("authentic") is not False:
            failures.append(
                "MassGapProtector.verify_telemetry must return authentic=False for < 32 samples"
            )
    except Exception as exc:
        failures.append(f"MassGapProtector import/exercise raised: {exc}")

    return CheckResult(
        name="claim_boundary_contract",
        severity="critical",
        status="fail" if failures else "pass",
        summary="claim boundary violations found"
        if failures
        else "telemetry, benchmark, and anti-simulation claim boundaries enforced",
        detail="\n".join(failures),
        duration_seconds=time.monotonic() - start,
    )


def _check_multi_pool_failover_contract() -> CheckResult:
    """Verify pool profile priority ordering and failover preconditions.

    The deployment contract requires that:
    - DEFAULT_POOL_SPECS defines a deterministic priority ordering
    - higher-priority pools sort before lower-priority ones in order_profiles
    - TLS-required pools reject non-TLS scheme URLs at build time
    - PoolProfile.to_dict redacts credentials in the public (include_secret_fields=False) path
    - validate_profile rejects profiles without username or password
    """
    start = time.monotonic()
    failures: list[str] = []
    try:
        from pythia_mining.pool_profiles import (
            DEFAULT_POOL_SPECS,
            PoolProfile,
            PoolProfileError,
            build_profile,
            order_profiles,
            validate_pool_url,
            validate_profile,
        )

        # 1. Priority ordering is deterministic
        profiles = []
        for pid, spec in DEFAULT_POOL_SPECS.items():
            try:
                profiles.append(
                    build_profile(
                        pid,
                        name=spec["name"],
                        url=spec["url"],
                        username="worker",
                        password="x",
                        stratum_version=spec["stratum_version"],
                        priority=spec["priority"],
                        tls_required=spec["tls_required"],
                    )
                )
            except PoolProfileError:
                pass  # TLS mismatch on some specs is expected with dummy credentials

        ordered = order_profiles(profiles)
        priorities = [p.priority for p in ordered]
        if priorities != sorted(priorities):
            failures.append(
                f"order_profiles does not produce ascending priority order: {priorities}"
            )

        # 2. NiceHash spec requires TLS scheme
        nh_spec = DEFAULT_POOL_SPECS["nicehash"]
        if not nh_spec["tls_required"]:
            failures.append("nicehash spec must require TLS")
        try:
            validate_pool_url("stratum+tcp://sha256.auto.nicehash.com:443", tls_required=True)
            failures.append("non-TLS URL must be rejected when tls_required=True")
        except PoolProfileError:
            pass  # expected

        # 3. to_dict redacts credentials
        p = PoolProfile(
            pool_id="test",
            name="Test",
            url="stratum+tcp://test.example.com:3333",
            username="secret_worker",
            password="secret_pass",
        )
        public = p.to_dict(include_secret_fields=False)
        if "secret_worker" in str(public):
            failures.append("to_dict(include_secret_fields=False) must redact username")
        if "secret_pass" in str(public):
            failures.append("to_dict(include_secret_fields=False) must redact password")

        # 4. validate_profile rejects missing credentials
        try:
            validate_profile(
                PoolProfile(
                    pool_id="noauth",
                    name="No Auth",
                    url="stratum+tcp://test.example.com:3333",
                    username="",
                    password="",
                )
            )
            failures.append("validate_profile must reject profiles without username")
        except PoolProfileError:
            pass  # expected

        # 5. Stratum V2 spec uses stratum2+ scheme
        sv2_spec = DEFAULT_POOL_SPECS["stratumv2"]
        if not sv2_spec["url"].startswith("stratum2+"):
            failures.append("stratumv2 spec URL must use stratum2+ scheme")
        if sv2_spec["stratum_version"] != 2:
            failures.append("stratumv2 spec must declare stratum_version=2")

    except Exception as exc:
        failures.append(f"multi-pool failover contract check raised: {exc}")

    return CheckResult(
        name="multi_pool_failover_contract",
        severity="critical",
        status="fail" if failures else "pass",
        summary="multi-pool failover contract violations found"
        if failures
        else "pool priority ordering, TLS enforcement, credential redaction, and Stratum V2 scheme verified",
        detail="\n".join(failures),
        duration_seconds=time.monotonic() - start,
    )


def _check_focused_tests() -> CheckResult:
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_phi_unified_mining_engine.py",
        "tests/test_unified_mining_api_surface.py",
        "tests/test_stratum_share_acceptance_e2e.py",
        "tests/test_pulvini_nonce_compression.py",
        "-q",
    ]
    code, stdout, stderr, duration = _run(command, timeout=300)
    return CheckResult(
        name="focused_mining_regression_tests",
        severity="critical",
        status="pass" if code == 0 else "fail",
        summary="focused mining regression tests passed"
        if code == 0
        else "focused mining regression tests failed",
        detail=(stdout + "\n" + stderr).strip(),
        duration_seconds=duration,
    )


def _check_build(*, skip_build: bool) -> CheckResult:
    if skip_build:
        return CheckResult(
            name="production_build",
            severity="advisory",
            status="skip",
            summary="production build skipped by operator flag",
            detail="run npm run build before deployment",
        )
    code, stdout, stderr, duration = _run(["npm", "run", "build"], timeout=420)
    return CheckResult(
        name="production_build",
        severity="critical",
        status="pass" if code == 0 else "fail",
        summary="production build passed" if code == 0 else "production build failed",
        detail=(stdout + "\n" + stderr).strip(),
        duration_seconds=duration,
    )


def _check_advisory_science_packets() -> CheckResult:
    expected = [
        ROOT / "artifacts" / "phi_resonance_100blocks" / "phi_resonance_summary.json",
        ROOT / "artifacts" / "phi_hash_validity" / "phi_hash_correlation_summary.json",
        ROOT / "artifacts" / "phi_structured_search" / "structured_search_comparison.json",
        ROOT / "artifacts" / "phi_stack" / "complete_stack_analysis.json",
    ]
    present = [path.relative_to(ROOT).as_posix() for path in expected if path.exists()]
    missing = [path.relative_to(ROOT).as_posix() for path in expected if not path.exists()]
    return CheckResult(
        name="empirical_evidence_artifacts",
        severity="advisory",
        status="warn" if missing else "pass",
        summary="some empirical evidence artifacts are absent locally"
        if missing
        else "empirical evidence artifacts are present locally",
        detail=json.dumps({"present": present, "missing": missing}, indent=2),
    )


def _write_report(report: ReadinessReport, artifact: Path) -> str:
    payload = report.to_dict()
    payload["source_artifact_sha256"] = None
    raw = json.dumps(payload, indent=2, sort_keys=True)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    payload["source_artifact_sha256"] = digest
    artifact.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return digest


def _next_actions(mode: Mode, critical_failed: bool) -> list[str]:
    if critical_failed:
        return [
            "Fix the first CRITICAL failure in the readiness packet; advisory warnings can wait.",
            "Rerun the same readiness doctor command from a clean terminal after the fix.",
            "Do not enable live share submission while any CRITICAL failure remains.",
        ]
    if mode == "live":
        return [
            "Start with HYBA_ENABLE_LIVE_SHARE_SUBMIT=false and confirm subscribe/authorize/job receipt first.",
            "Enable live share submission only with HYBA_LIVE_SHARE_APPROVAL_ID attached.",
            "Treat accepted-share evidence as pool-side truth; local candidate validity is necessary but not sufficient.",
        ]
    return [
        "The software path is ready for controlled deployment preparation.",
        "Before live mining, inject production env, at least one pool profile, and audit logging, then run this doctor with --mode live.",
        "Keep broad science/elevation suites as advisory/review evidence, not blockers for the same-day mining cutover.",
    ]


def run_doctor(mode: Mode, *, skip_build: bool = False) -> ReadinessReport:
    checks: list[CheckResult] = []
    checks.append(_check_required_files())
    checks.extend(_check_environment(mode))
    checks.append(_check_unified_engine_contract())
    checks.append(_check_bitcoin_mining_contracts())
    checks.append(_check_claim_boundary_contract())
    checks.append(_check_multi_pool_failover_contract())
    checks.append(_check_focused_tests())
    checks.append(_check_build(skip_build=skip_build))
    checks.append(_check_advisory_science_packets())

    critical_failed = any(
        check.severity == "critical" and check.status == "fail" for check in checks
    )
    now = datetime.now(timezone.utc)
    return ReadinessReport(
        version="HYBA_MINING_OPERATIONAL_READINESS_V1",
        mode=mode,
        status="blocked" if critical_failed else "ready",
        passed=not critical_failed,
        generated_at_utc=now.isoformat(),
        host={
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "machine": platform.machine(),
        },
        environment_summary=_environment_summary(),
        checks=checks,
        next_operator_actions=_next_actions(mode, critical_failed),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run HYBA mining production-readiness doctor")
    parser.add_argument(
        "--mode", choices=("prepare", "command-room", "live"), default="command-room"
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip npm production build; this changes build from critical to advisory/skip.",
    )
    args = parser.parse_args(argv)

    report = run_doctor(args.mode, skip_build=args.skip_build)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifact = ARTIFACT_DIR / f"mining_production_readiness_{args.mode}_{stamp}.json"
    digest = _write_report(report, artifact)

    for check in report.checks:
        marker = check.status.upper()
        print(f"[{marker}] {check.severity.upper()} {check.name}: {check.summary}")
        if check.detail and check.status in {"fail", "warn"}:
            print(check.detail)
    print(f"Readiness packet: {artifact.relative_to(ROOT)}")
    print(f"Artifact SHA-256: {digest}")
    print(f"Readiness status: {report.status}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
