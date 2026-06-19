from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "mining_autonomic_protocol_gate.py"


BASE_ENV = {
    "PYTHONPATH": "python_backend",
    "NODE_ENV": "production",
    "HYBA_ENV": "production",
    "HYBA_ENABLE_LIVE_STRATUM": "true",
    "HYBA_ENABLE_AUDIT_LOGGING": "true",
    "HYBA_ALLOW_DEV_FIXTURES": "false",
}


def _run_gate(extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(BASE_ENV)
    for key in list(env):
        if key.startswith("HYBA_AUTONOMOUS_OPERATOR") or key == "HYBA_LIVE_SHARE_APPROVAL_ID":
            env.pop(key, None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--mode", "live"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_seeded_pythia_mission_autonomy_goes_live_without_manual_approval_id() -> None:
    result = _run_gate({"HYBA_ENABLE_LIVE_SHARE_SUBMIT": "true"})

    assert result.returncode == 0, result.stdout + result.stderr
    assert '"schema": "HYBA_PYTHIA_AUTONOMIC_PROTOCOL_GATE_V3"' in result.stdout
    assert '"pythia_autonomy_restored": true' in result.stdout
    assert '"status": "GO"' in result.stdout
    assert "PYTHIA may wake seeded" in result.stdout
    assert "verifier-passing candidates" in result.stdout


def test_live_share_submit_legacy_approval_id_does_not_block_seeded_mission() -> None:
    result = _run_gate({"HYBA_ENABLE_LIVE_SHARE_SUBMIT": "true"})

    assert result.returncode == 0, result.stdout + result.stderr
    assert "acceptable under the seeded mission" in result.stdout
    assert "legacy manual approval fields do not restrict" in result.stdout


def test_exact_validation_bypass_blocks_pool_submission_path() -> None:
    result = _run_gate({"HYBA_BYPASS_LOCAL_SHA256D_VALIDATION": "true"})

    assert result.returncode == 2
    assert '"status": "NO_GO"' in result.stdout
    assert "HYBA_BYPASS_LOCAL_SHA256D_VALIDATION must not be true" in result.stdout


def test_actions_outside_one_block_mission_require_human_authority() -> None:
    result = _run_gate({"HYBA_AUTONOMOUS_EXTERNAL_ACTIONS": "true"})

    assert result.returncode == 2
    assert (
        "actions outside the seeded mining mission lack explicit human authority" in result.stdout
    )
    assert "HYBA_AUTONOMOUS_OPERATOR_APPROVAL_ID required" in result.stdout


def test_actions_outside_one_block_mission_pass_when_explicitly_authorised() -> None:
    result = _run_gate(
        {
            "HYBA_AUTONOMOUS_EXTERNAL_ACTIONS": "true",
            "HYBA_AUTONOMOUS_OPERATOR_APPROVAL_ID": "outside-mission-approval-001",
            "HYBA_AUTONOMOUS_OPERATOR": "command-room",
            "HYBA_AUTONOMOUS_OPERATOR_REASON": "explicitly-authorised-outside-mission-test",
        }
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (
        "actions outside the seeded mining mission are disabled or explicitly authorised"
        in result.stdout
    )


def test_env_hashrate_above_one_ehs_warns_because_mission_memory_clamps() -> None:
    result = _run_gate({"HYBA_AUTONOMOUS_MAX_HASHRATE_EHS": "100"})

    assert result.returncode == 0, result.stdout + result.stderr
    assert "mission memory clamps to 1.0 EH/s" in result.stdout
    assert '"status": "GO"' in result.stdout


def test_live_dev_fixtures_still_block_evidence_integrity() -> None:
    result = _run_gate({"HYBA_ALLOW_DEV_FIXTURES": "true"})

    assert result.returncode == 2
    assert "HYBA_ALLOW_DEV_FIXTURES must be false before live mining" in result.stdout
