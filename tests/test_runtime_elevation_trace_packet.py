from __future__ import annotations

import json
from pathlib import Path

from scripts.phi_resonance_math import forensic_hash
from scripts.runtime_trace_packet import build_packet, write_packet


def test_runtime_packet_records_absence_without_success(tmp_path: Path) -> None:
    packet = build_packet(tmp_path)

    assert packet["inputs"]["pythia_state_present"] is False
    assert packet["shares"]["accepted"] == 0
    assert packet["shares"]["accepted_present"] is False
    assert packet["claim_level"] == "runtime_trace_no_share_present"

    unsigned = dict(packet)
    digest = unsigned.pop("forensic_sha256")
    assert digest == forensic_hash(unsigned)


def test_runtime_packet_records_accepted_share_when_present(tmp_path: Path) -> None:
    backend = tmp_path / "python_backend"
    backend.mkdir()
    (backend / "pythia_state.json").write_text(
        json.dumps(
            {
                "total_shares": 3,
                "accepted_shares": 1,
                "system_health": "HEALTHY",
                "telemetry_source": "runtime_state",
            }
        ),
        encoding="utf-8",
    )

    packet = build_packet(tmp_path)

    assert packet["inputs"]["pythia_state_present"] is True
    assert packet["shares"]["total"] == 3
    assert packet["shares"]["accepted"] == 1
    assert packet["shares"]["accepted_present"] is True
    assert packet["claim_level"] == "share_present"
    assert packet["runtime"]["system_health"] == "HEALTHY"


def test_runtime_packet_manifest_links_to_packet(tmp_path: Path) -> None:
    manifest = write_packet(tmp_path / "out", tmp_path)
    packet_path = Path(manifest["packet"])
    packet = json.loads(packet_path.read_text(encoding="utf-8"))

    assert packet_path.exists()
    assert manifest["packet_sha256"] == packet["forensic_sha256"]
    unsigned = dict(manifest)
    digest = unsigned.pop("forensic_sha256")
    assert digest == forensic_hash(unsigned)
