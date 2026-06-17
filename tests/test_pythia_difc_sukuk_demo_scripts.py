from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_script(script: str, *args: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, script, *args],
        cwd=Path(__file__).resolve().parents[1],
        env={"PYTHONPATH": "python_backend"},
        text=True,
        capture_output=True,
        check=True,
    )


def test_sukuk_lifecycle_simulation_writes_manifest_and_stage_packets(tmp_path: Path) -> None:
    output_dir = tmp_path / "lifecycle"
    result = _run_script(
        "scripts/simulate_difc_sukuk_lifecycle_drift.py",
        "--output-dir",
        str(output_dir),
        tmp_path=tmp_path,
    )
    manifest = json.loads(result.stdout)

    assert manifest["schema"] == "PYTHIA_DIFC_AAOIFI_SUKUK_LIFECYCLE_SIMULATION_V1"
    assert manifest["stage_count"] == 4
    assert manifest["human_review_required"] is True
    assert manifest["automatic_action_allowed"] is False
    assert (output_dir / "manifest.json").exists()
    assert len(list(output_dir.glob("*.json"))) == 5  # four packets + manifest

    rows = manifest["rows"]
    assert rows[0]["failed_findings"] == 0
    assert rows[-1]["failed_findings"] >= 1
    assert rows[-1]["automatic_action_allowed"] is False


def test_criticism_ledger_renders_human_review_boundary(tmp_path: Path) -> None:
    packet_path = tmp_path / "packet.json"
    ledger_path = tmp_path / "ledger.txt"

    _run_script(
        "scripts/generate_difc_sukuk_audit_packet.py",
        "--drift",
        "--output",
        str(packet_path),
        tmp_path=tmp_path,
    )
    _run_script(
        "scripts/show_difc_sukuk_criticism_ledger.py",
        str(packet_path),
        "--output",
        str(ledger_path),
        tmp_path=tmp_path,
    )

    ledger = ledger_path.read_text(encoding="utf-8")
    assert "PYTHIA DIFC / AAOIFI SUKUK CRITICISM LEDGER" in ledger
    assert "Automatic action allowed: False" in ledger
    assert "Human review required: True" in ledger
    assert "not a fatwa" in ledger
    assert "SSSB" in ledger
    assert "FAIL" in ledger or "WARN" in ledger
