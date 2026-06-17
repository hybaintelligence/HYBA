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
        "HYBA_AUTONOMOUS_EXTERNAL_ACTIONS",
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


def _set_live_startup_env(monkeypatch) -> None:
    monkeypatch.setenv("NODE_ENV", "production")
    monkeypatch.setenv("HYBA_ENV", "production")
    monkeypatch.setenv("HYBA_ALLOW_DEV_FIXTURES", "false")
    monkeypatch.setenv("HYBA_ENABLE_LIVE_STRATUM", "true")
    monkeypatch.setenv("HYBA_ENABLE_AUDIT_LOGGING", "true")
    monkeypatch.setenv("HYBA_ENABLE_AUTONOMOUS_MINING", "true")
    monkeypatch.setenv("HYBA_AUTONOMOUS_MAX_HASHRATE_EHS", "100")
    monkeypatch.setenv("HYBA_AUTONOMOUS_MAX_POWER_WATTS", "500")
    monkeypatch.setenv("HYBA_AUTONOMOUS_MIN_PHI_COHERENCE", "0.70")
    monkeypatch.setenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", "false")


def test_live_pythia_startup_autonomy_passes_without_operator_approval(monkeypatch) -> None:
    _clear_env(monkeypatch)
    _set_live_startup_env(monkeypatch)

    report = run_gate("live")

    assert report.passed is True
    assert report.status == "GO"
    assert report.schema == "HYBA_AUTONOMOUS_MINING_SOVEREIGN_GATE_V2"
    startup = next(check for check in report.checks if check.name == "pythia_startup_autonomy_allowed")
    external = next(check for check in report.checks if check.name == "autonomous_external_action_authorisation")
    assert startup.status == "pass"
    assert external.status == "pass"
    assert "boot, heal, optimise" in " ".join(report.next_operator_actions)


def test_autonomous_external_actions_require_operator_approval(monkeypatch) -> None:
    _clear_env(monkeypatch)
    _set_live_startup_env(monkeypatch)
    monkeypatch.setenv("HYBA_AUTONOMOUS_EXTERNAL_ACTIONS", "true")

    report = run_gate("live")

    assert report.passed is False
    assert report.status == "NO_GO"
    approval = next(check for check in report.checks if check.name == "autonomous_external_action_authorisation")
    assert approval.status == "fail"
    assert "HYBA_AUTONOMOUS_OPERATOR_APPROVAL_ID" in approval.detail


def test_autonomous_external_actions_pass_with_bounded_human_authority(monkeypatch) -> None:
    _clear_env(monkeypatch)
    _set_live_startup_env(monkeypatch)
    monkeypatch.setenv("HYBA_AUTONOMOUS_EXTERNAL_ACTIONS", "true")
    monkeypatch.setenv("HYBA_AUTONOMOUS_OPERATOR_APPROVAL_ID", "approval-001")
    monkeypatch.setenv("HYBA_AUTONOMOUS_OPERATOR", "operator")
    monkeypatch.setenv("HYBA_AUTONOMOUS_OPERATOR_REASON", "controlled observed run")

    report = run_gate("live")

    assert report.passed is True
    assert report.status == "GO"
    assert all(check.status != "fail" for check in report.checks if check.severity == "critical")


def test_autonomous_gate_blocks_dev_fixtures_and_unbounded_hashrate(monkeypatch) -> None:
    _clear_env(monkeypatch)
    _set_live_startup_env(monkeypatch)
    monkeypatch.setenv("HYBA_ALLOW_DEV_FIXTURES", "true")
    monkeypatch.setenv("HYBA_AUTONOMOUS_MAX_HASHRATE_EHS", "1000")

    report = run_gate("live")

    assert report.passed is False
    fixture = next(check for check in report.checks if check.name == "dev_fixtures_disabled_for_pythia_startup")
    bounds = next(check for check in report.checks if check.name == "autonomous_runtime_bounds")
    assert fixture.status == "fail"
    assert bounds.status == "fail"


def test_live_share_submit_requires_separate_approval(monkeypatch) -> None:
    _clear_env(monkeypatch)
    _set_live_startup_env(monkeypatch)
    monkeypatch.setenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", "true")

    report = run_gate("live")

    submit = next(check for check in report.checks if check.name == "live_share_submit_authorisation")
    assert report.passed is False
    assert submit.status == "fail"
    assert "HYBA_LIVE_SHARE_APPROVAL_ID" in submit.detail
