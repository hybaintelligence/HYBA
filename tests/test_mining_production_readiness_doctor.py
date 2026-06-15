from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from mining_production_readiness_doctor import (  # noqa: E402
    _check_bitcoin_mining_contracts,
    _check_environment,
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
