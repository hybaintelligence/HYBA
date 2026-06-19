from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from mining_production_readiness_doctor import (  # noqa: E402
    _check_bitcoin_mining_contracts,
    _check_claim_boundary_contract,
    _check_environment,
    _check_multi_pool_failover_contract,
    _check_required_files,
    _check_unified_engine_contract,
    run_doctor,
)


def test_required_mining_surfaces_are_present() -> None:
    result = _check_required_files()

    assert result.severity == "critical"
    assert result.status == "pass"


def test_unified_engine_doctor_enforces_pulvini_contract() -> None:
    result = _check_unified_engine_contract()

    assert result.severity == "critical"
    assert result.status == "pass"
    assert "compressed PULVINI" in result.summary


def test_bitcoin_and_stratum_pitfall_contracts_are_static_guarded() -> None:
    result = _check_bitcoin_mining_contracts()

    assert result.severity == "critical"
    assert result.status == "pass"
    assert "pool ACK" in result.summary


def test_command_room_environment_warnings_do_not_block_preparation(monkeypatch) -> None:
    monkeypatch.delenv("NODE_ENV", raising=False)
    monkeypatch.delenv("HYBA_ENV", raising=False)
    monkeypatch.delenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", raising=False)
    monkeypatch.delenv("HYBA_LIVE_SHARE_APPROVAL_ID", raising=False)

    critical, advisory = _check_environment("command-room")

    assert critical.status == "pass"
    assert advisory.status == "warn"


def test_live_share_submit_without_approval_is_critical(monkeypatch) -> None:
    monkeypatch.setenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", "true")
    monkeypatch.delenv("HYBA_LIVE_SHARE_APPROVAL_ID", raising=False)

    critical, _advisory = _check_environment("command-room")

    assert critical.status == "fail"
    assert "HYBA_LIVE_SHARE_APPROVAL_ID" in critical.detail


def test_prepare_doctor_can_skip_build_without_turning_build_into_blocker() -> None:
    report = run_doctor("prepare", skip_build=True)
    build = next(check for check in report.checks if check.name == "production_build")

    assert build.severity == "advisory"
    assert build.status == "skip"
    assert report.status in {"ready", "blocked"}


def test_reflexive_daemon_without_audit_logging_is_advisory(monkeypatch) -> None:
    monkeypatch.setenv("HYBA_ENABLE_REFLEXIVE_DAEMON", "true")
    monkeypatch.delenv("HYBA_ENABLE_AUDIT_LOGGING", raising=False)
    monkeypatch.delenv("HYBA_ONTOLOGICAL_STATE_PATH", raising=False)
    monkeypatch.delenv("HYBA_ONTOLOGICAL_PERSISTENCE_PATH", raising=False)

    critical, advisory = _check_environment("command-room")

    assert critical.status == "pass"
    assert advisory.status == "warn"
    assert "HYBA_ENABLE_REFLEXIVE_DAEMON" in advisory.detail


def test_ontological_persistence_rejects_secret_or_temp_paths(monkeypatch) -> None:
    monkeypatch.setenv("HYBA_ONTOLOGICAL_STATE_PATH", "/tmp/hyba_secret_grace.json")

    critical, _advisory = _check_environment("command-room")

    assert critical.status == "fail"
    assert "ontological persistence path" in critical.detail


def test_claim_boundary_contract_passes() -> None:
    """Doctor claim-boundary check must pass: no fabricated telemetry, projections labelled correctly."""
    result = _check_claim_boundary_contract()

    assert result.severity == "critical"
    assert result.status == "pass", f"claim boundary failures:\n{result.detail}"


def test_multi_pool_failover_contract_passes() -> None:
    """Doctor multi-pool failover check must pass: priority ordering, TLS, redaction, V2 scheme."""
    result = _check_multi_pool_failover_contract()

    assert result.severity == "critical"
    assert result.status == "pass", f"failover contract failures:\n{result.detail}"


def test_required_files_includes_gap_test_surfaces() -> None:
    """The required-files check must include all gap-test files as blocking surfaces."""
    result = _check_required_files()

    assert result.severity == "critical"
    # All gap test files must be present in the repo for this to pass
    assert result.status == "pass", f"missing surfaces:\n{result.detail}"


def test_run_doctor_includes_claim_boundary_and_failover_checks() -> None:
    """run_doctor must execute both new checks and include them in the report."""
    report = run_doctor("prepare", skip_build=True)

    check_names = {c.name for c in report.checks}
    assert "claim_boundary_contract" in check_names, (
        "claim_boundary_contract check missing from report"
    )
    assert "multi_pool_failover_contract" in check_names, (
        "multi_pool_failover_contract check missing from report"
    )


def test_live_mode_blocks_without_production_env(monkeypatch) -> None:
    """run_doctor in live mode must be blocked when NODE_ENV and HYBA_ENV are not production."""
    monkeypatch.setenv("NODE_ENV", "development")
    monkeypatch.setenv("HYBA_ENV", "development")
    monkeypatch.delenv("HYBA_ENABLE_LIVE_STRATUM", raising=False)
    monkeypatch.delenv("HYBA_ENABLE_AUDIT_LOGGING", raising=False)

    critical, _advisory = _check_environment("live")

    assert critical.status == "fail"
    assert "NODE_ENV=production" in critical.detail


def test_live_mode_blocks_without_live_stratum_flag(monkeypatch) -> None:
    """run_doctor live mode must fail when HYBA_ENABLE_LIVE_STRATUM is not set."""
    monkeypatch.setenv("NODE_ENV", "production")
    monkeypatch.setenv("HYBA_ENV", "production")
    monkeypatch.delenv("HYBA_ENABLE_LIVE_STRATUM", raising=False)
    monkeypatch.setenv("HYBA_ENABLE_AUDIT_LOGGING", "true")
    monkeypatch.setenv("HYBA_POOL_BRAIINS_USERNAME", "worker")
    monkeypatch.setenv("HYBA_POOL_BRAIINS_PASSWORD", "x")

    critical, _advisory = _check_environment("live")

    assert critical.status == "fail"
    assert "HYBA_ENABLE_LIVE_STRATUM" in critical.detail


def test_dev_fixtures_in_production_is_critical_failure(monkeypatch) -> None:
    """HYBA_ALLOW_DEV_FIXTURES=true in production must be a critical failure."""
    monkeypatch.setenv("NODE_ENV", "production")
    monkeypatch.setenv("HYBA_ENV", "production")
    monkeypatch.setenv("HYBA_ALLOW_DEV_FIXTURES", "true")

    critical, _advisory = _check_environment("command-room")

    assert critical.status == "fail"
    assert "HYBA_ALLOW_DEV_FIXTURES" in critical.detail
