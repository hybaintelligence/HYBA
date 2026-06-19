from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from local_clean_10_gate import GateCommand, run_gate  # noqa: E402


def test_clean_gate_reports_go_when_required_commands_pass() -> None:
    report = run_gate(
        [
            GateCommand(
                name="minimal_pass",
                command=[sys.executable, "-c", "print('clean evidence ok')"],
            )
        ]
    )

    assert report.schema == "HYBA_FULLSTACK_LOCAL_CLEAN_10_GATE_V1"
    assert report.status == "GO"
    assert report.passed is True
    assert report.required_failures == []
    assert report.results[0].passed is True
    assert Path(report.results[0].log_path).parts[:2] == ("artifacts", "clean_10")


def test_clean_gate_reports_no_go_when_required_command_fails() -> None:
    report = run_gate(
        [
            GateCommand(
                name="minimal_fail",
                command=[sys.executable, "-c", "raise SystemExit(7)"],
            )
        ]
    )

    assert report.status == "NO_GO"
    assert report.passed is False
    assert report.required_failures == ["minimal_fail"]
    assert report.results[0].returncode == 7
    assert "Do not describe the repository as clean" in report.next_actions[0]
