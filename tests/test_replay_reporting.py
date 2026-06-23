from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pythia_mining.mining_auto_attester import emit_attested_mining_success_manifest
from pythia_mining.replay_reporting import (
    build_verification_report,
    unified_text_diff,
    write_report_html,
    write_report_json,
)

ROOT = Path(__file__).resolve().parents[1]


def test_reporting_helpers_emit_json_html_and_diff(tmp_path) -> None:
    diff = unified_text_diff("alpha\n", "beta\n")
    report = build_verification_report(
        ok=False,
        operation="unit-test",
        claim_id="claim-1",
        error="digest mismatch",
        diagnostics={"stdout_diff": diff},
    )
    json_path = tmp_path / "report.json"
    html_path = tmp_path / "report.html"

    write_report_json(report, json_path)
    write_report_html(report, html_path)

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert "-alpha" in payload["diagnostics"]["stdout_diff"]
    assert "+beta" in payload["diagnostics"]["stdout_diff"]
    assert "FAIL" in html_path.read_text(encoding="utf-8")


def test_replay_claim_cli_writes_failure_reports(tmp_path) -> None:
    command = f"{sys.executable} -c \"print('actual')\""
    manifest = emit_attested_mining_success_manifest(
        claim_id="report_failure_claim",
        claim="Report failure claim deliberately has a tampered output digest.",
        replay_command=command,
        replay_stdout="actual\n",
        inputs={"message": "actual"},
        seeds={"python_hash_seed": 0},
    ).to_dict()
    manifest["claim"]["reproducibility_attestation"]["expected_output_digest"] = (
        "0" * 64
    )
    manifest_path = tmp_path / "manifest.json"
    report_json = tmp_path / "report.json"
    report_html = tmp_path / "report.html"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/replay_claim.py",
            str(manifest_path),
            "--cwd",
            str(tmp_path),
            "--report-json",
            str(report_json),
            "--report-html",
            str(report_html),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert "digest mismatch" in payload["error"]
    assert "FAIL" in report_html.read_text(encoding="utf-8")
