from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from evidence_boundary_report import generate_report, write_report  # noqa: E402


def test_evidence_boundary_reports_no_go_without_acceptance_marker(
    tmp_path: Path,
) -> None:
    (tmp_path / "logs").mkdir()
    (tmp_path / "artifacts" / "clean_10").mkdir(parents=True)
    (tmp_path / "artifacts").mkdir(exist_ok=True)
    (tmp_path / "logs" / "braiins_session_stats.json").write_text(
        json.dumps(
            {
                "connected": False,
                "jobs_received": 0,
                "shares_submitted": 0,
                "errors": ["connect failed"],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "artifacts" / "production_gate_output.json").write_text(
        json.dumps(
            {"status": "PASSED", "accepted_share_evidence": {"status": "warning"}}
        ),
        encoding="utf-8",
    )
    (tmp_path / "artifacts" / "clean_10" / "latest.json").write_text(
        json.dumps({"passed": True, "status": "GO", "required_failures": []}),
        encoding="utf-8",
    )

    report = generate_report(tmp_path)

    assert report.status == "NO_GO"
    assert report.passed is False
    assert any(
        check.name == "session_stats" and check.status == "warning"
        for check in report.checks
    )
    assert "Synthetic or local benchmark evidence" in report.claim_boundaries[2]


def test_evidence_boundary_reports_go_with_acceptance_and_clean_gate(
    tmp_path: Path,
) -> None:
    (tmp_path / "logs").mkdir()
    (tmp_path / "artifacts" / "clean_10").mkdir(parents=True)
    (tmp_path / "artifacts").mkdir(exist_ok=True)
    (tmp_path / "logs" / "braiins_session_stats.json").write_text(
        json.dumps(
            {
                "connected": True,
                "jobs_received": 3,
                "shares_submitted": 2,
                "shares_accepted": 1,
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "artifacts" / "production_gate_output.json").write_text(
        json.dumps({"checks": [{"accepted_share_count": 1}]}),
        encoding="utf-8",
    )
    (tmp_path / "artifacts" / "clean_10" / "latest.json").write_text(
        json.dumps({"passed": True, "status": "GO", "required_failures": []}),
        encoding="utf-8",
    )

    report = generate_report(tmp_path)
    output = write_report(report, tmp_path / "evidence" / "latest.json")

    assert report.status == "GO"
    assert report.passed is True
    assert output.exists()
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["schema"] == "HYBA_REPOSITORY_EVIDENCE_BOUNDARY_V1"


def test_evidence_boundary_fails_when_clean_gate_failed_even_with_acceptance(
    tmp_path: Path,
) -> None:
    (tmp_path / "logs").mkdir()
    (tmp_path / "artifacts" / "clean_10").mkdir(parents=True)
    (tmp_path / "artifacts").mkdir(exist_ok=True)
    (tmp_path / "logs" / "braiins_session_stats.json").write_text(
        json.dumps({"shares_accepted": 1}), encoding="utf-8"
    )
    (tmp_path / "artifacts" / "production_gate_output.json").write_text(
        json.dumps({"accepted": True}), encoding="utf-8"
    )
    (tmp_path / "artifacts" / "clean_10" / "latest.json").write_text(
        json.dumps(
            {"passed": False, "status": "NO_GO", "required_failures": ["backend_gate"]}
        ),
        encoding="utf-8",
    )

    report = generate_report(tmp_path)

    assert report.status == "NO_GO"
    assert report.passed is False
    clean_check = next(
        check for check in report.checks if check.name == "clean_10_gate"
    )
    assert clean_check.status == "fail"
