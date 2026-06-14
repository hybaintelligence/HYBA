from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from funding_engine_deployment_gate import (  # noqa: E402
    check_accepted_share_artifacts,
    check_deterministic_search,
    check_phi_resonance_artifacts,
)


def _write_phi_artifacts(base: Path) -> None:
    base.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "height": "1",
            "timestamp": "1700000000",
            "nonce": "1000",
            "miner": "test",
            "k_multiplier": "1",
            "approx": "1000.0",
            "diff": "10.0",
            "precision_pct": "99.0",
            "resonance_strength": "0.800000",
            "is_phi_resonant": "False",
            "birthday_modular_diff": "",
            "birthday_substring_hits": "",
            "birthday_resonant": "False",
            "birthday_echo_type": "none",
        },
        {
            "height": "2",
            "timestamp": "1700000600",
            "nonce": "2000",
            "miner": "test",
            "k_multiplier": "2",
            "approx": "2000.0",
            "diff": "500.0",
            "precision_pct": "98.0",
            "resonance_strength": "0.200000",
            "is_phi_resonant": "False",
            "birthday_modular_diff": "",
            "birthday_substring_hits": "",
            "birthday_resonant": "False",
            "birthday_echo_type": "none",
        },
    ]
    with (base / "phi_resonance_blocks.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    (base / "phi_resonance_summary.json").write_text(
        json.dumps(
            {
                "summary": {
                    "mean_resonance_strength": 0.5,
                    "resonance_above_05_count": 1,
                    "resonance_above_05_rate": 0.5,
                }
            }
        ),
        encoding="utf-8",
    )


def test_phi_resonance_artifact_gate_passes(tmp_path: Path) -> None:
    phi_dir = tmp_path / "phi"
    _write_phi_artifacts(phi_dir)
    result = check_phi_resonance_artifacts(phi_dir)
    assert result.status == "passed"
    assert result.details["resonance_above_05_count"] == 1


def test_phi_resonance_artifact_gate_fails_on_missing_fields(tmp_path: Path) -> None:
    phi_dir = tmp_path / "phi"
    phi_dir.mkdir()
    (phi_dir / "phi_resonance_blocks.csv").write_text("height,nonce\n1,2\n", encoding="utf-8")
    (phi_dir / "phi_resonance_summary.json").write_text("{}", encoding="utf-8")
    result = check_phi_resonance_artifacts(phi_dir)
    assert result.status == "failed"
    assert "missing_csv_fields" in result.details


def test_accepted_share_gate_detects_accepted_share(tmp_path: Path) -> None:
    room = tmp_path / "room"
    room.mkdir()
    (room / "mining_status.json").write_text(
        json.dumps({"shares": {"submitted": 3, "accepted": 1, "rejected": 2}}),
        encoding="utf-8",
    )
    result = check_accepted_share_artifacts(room, required=True)
    assert result.status == "passed"
    assert result.details["max_accepted_shares_seen"] == 1


def test_accepted_share_gate_warns_when_not_required(tmp_path: Path) -> None:
    room = tmp_path / "room"
    room.mkdir()
    (room / "mining_status.json").write_text(
        json.dumps({"shares": {"submitted": 0, "accepted": 0, "rejected": 0}}),
        encoding="utf-8",
    )
    result = check_accepted_share_artifacts(room, required=False)
    assert result.status == "warning"


def test_deterministic_search_repeats_nonce() -> None:
    result = check_deterministic_search(target=0x1D00FFFF, nonce_start=0, nonce_end=4095)
    assert result.status == "passed"
    assert result.details["first_nonce"] == result.details["second_nonce"]
    assert 0 <= result.details["first_nonce"] <= 4095
