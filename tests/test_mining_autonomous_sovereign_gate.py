from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from mining_autonomous_sovereign_gate import run_gate  # noqa: E402


def _clear_env(monkeypatch) -> None:
    for name in [
        "NODE_ENV",
        "HYBA_ENV",
        "HYBA_ALLOW_DEV_FIXTURES",
        "HYBA_ENABLE_LIVE_STRATUM",
        "HYBA_ENABLE_AUDIT_LOGGING",
        "HYBA_ENABLE_AUTONOMOUS_MINING",
        "HYBA_AUTONOMOUS_OPERATOR_APPROVAL_ID",
        "HYBA_AUTONOMOUS_OPERATOR",
        "HYBA_AUTONOMOUS_OPERATOR_REASON",
        "HYBA_AUTONOMOUS_MAX_HASHRATE_EHS",
        "HYBA_AUTONOMOUS_MAX_POWER_WATTS",
        "HYBA_AUTONOMOUS_MIN_PHI_COHERENCE",
        "HYBA_ENABLE_LIVE_SHARE_SUBMIT",
        "HYBA_LIVE_SHARE_APPROVAL_ID",
    ]:
        monkeypatch.delenv(name, raising=False)


def test_live_autonomous_gate_blocks_without_operator_approval(monkeypatch) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("NODE_ENV", "production")
    monkeypatch.setenv("HYBA_ENV", "production")
    monkeypatch.setenv("HYBA_ALLOW_DEV_FIXTURES", "false")
    monkeypatch.setenv("HYBA_ENABLE_LIVE_STRATUM", "true")
    monkeypatch.setenv("HYBA_ENABLE_AUDIT_LOGGING", "true")

    report = run_gate("live")

    assert report.passed is False
    assert report.status == "NO_GO"
    approval = next(check for check in report.checks if check.name == "autonomous_operator_authorisation")
    assert approval.status == "fail"
    assert "HYBA_AUTONOMOUS_OPERATOR_APPROVAL_ID" in approval.detail


def test_live_autonomous_gate_passes_with_bounded_human_authority(monkeypatch) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("NODE_ENV", "production")
    monkeypatch.setenv("HYBA_ENV", "production")
    monkeypatch.setenv("HYBA_ALLOW_DEV_FIXTURES", "false")
    monkeypatch.setenv("HYBA_ENABLE_LIVE_STRATUM", "true")
    monkeypatch.setenv("HYBA_ENABLE_AUDIT_LOGGING", "true")
    monkeypatch.setenv("HYBA_ENABLE_AUTONOMOUS_MINING", "true")
    monkeypatch.setenv("HYBA_AUTONOMOUS_OPERATOR_APPROVAL_ID", "CEO-COS-ED-2026-06-17-001")
    monkeypatch.setenv("HYBA_AUTONOMOUS_OPERATOR", "Andre Taylor-Morris")
    monkeypatch.setenv("HYBA_AUTONOMOUS_OPERATOR_REASON", "controlled command-room live mining cutover")
    monkeypatch.setenv("HYBA_AUTONOMOUS_MAX_HASHRATE_EHS", "100")
    monkeypatch.setenv("HYBA_AUTONOMOUS_MAX_POWER_WATTS", "500")
    monkeypatch.setenv("HYBA_AUTONOMOUS_MIN_PHI_COHERENCE", "0.70")
    monkeypatch.setenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", "false")

    report = run_gate("live")

    assert report.passed is True
    assert report.status == "GO"
    assert all(check.status != "fail" for check in report.checks if check.severity == "critical")


def test_autonomous_gate_blocks_dev_fixtures_and_unbounded_hashrate(monkeypatch) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("NODE_ENV", "production")
    monkeypatch.setenv("HYBA_ENV", "production")
    monkeypatch.setenv("HYBA_ALLOW_DEV_FIXTURES", "true")
    monkeypatch.setenv("HYBA_ENABLE_LIVE_STRATUM", "true")
    monkeypatch.setenv("HYBA_ENABLE_AUDIT_LOGGING", "true")
    monkeypatch.setenv("HYBA_ENABLE_AUTONOMOUS_MINING", "true")
    monkeypatch.setenv("HYBA_AUTONOMOUS_OPERATOR_APPROVAL_ID", "approval")
    monkeypatch.setenv("HYBA_AUTONOMOUS_OPERATOR", "operator")
    monkeypatch.setenv("HYBA_AUTONOMOUS_OPERATOR_REASON", "test")
    monkeypatch.setenv("HYBA_AUTONOMOUS_MAX_HASHRATE_EHS", "1000")

    report = run_gate("live")

    assert report.passed is False
    fixture = next(check for check in report.checks if check.name == "dev_fixtures_disabled_for_autonomy")
    bounds = next(check for check in report.checks if check.name == "autonomous_runtime_bounds")
    assert fixture.status == "fail"
    assert bounds.status == "fail"


def test_live_share_submit_requires_separate_approval(monkeypatch) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("NODE_ENV", "production")
    monkeypatch.setenv("HYBA_ENV", "production")
    monkeypatch.setenv("HYBA_ALLOW_DEV_FIXTURES", "false")
    monkeypatch.setenv("HYBA_ENABLE_LIVE_STRATUM", "true")
    monkeypatch.setenv("HYBA_ENABLE_AUDIT_LOGGING", "true")
    monkeypatch.setenv("HYBA_ENABLE_AUTONOMOUS_MINING", "true")
    monkeypatch.setenv("HYBA_AUTONOMOUS_OPERATOR_APPROVAL_ID", "approval")
    monkeypatch.setenv("HYBA_AUTONOMOUS_OPERATOR", "operator")
    monkeypatch.setenv("HYBA_AUTONOMOUS_OPERATOR_REASON", "test")
    monkeypatch.setenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", "true")

    report = run_gate("live")

    submit = next(check for check in report.checks if check.name == "live_share_submit_authorisation")
    assert report.passed is False
    assert submit.status == "fail"
    assert "HYBA_LIVE_SHARE_APPROVAL_ID" in submit.detail
