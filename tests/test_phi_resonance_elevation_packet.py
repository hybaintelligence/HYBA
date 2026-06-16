from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_phi_resonance_elevation_packet import build_packet, write_packet
from scripts.phi_resonance_math import forensic_hash


def test_phi_packet_checks_and_hash_are_stable() -> None:
    packet = build_packet()

    assert packet["doctrine"]["not_decorative"] is True
    assert packet["all_elevation_checks_pass"] is True
    assert packet["elevation_checks"]["lucas_converges_to_phi"] is True
    assert packet["elevation_checks"]["phi_best_structured_scaler"] is True
    assert packet["elevation_checks"]["phi_specific_not_noise_magic"] is True
    assert packet["elevation_checks"]["distribution_normalized"] is True
    assert packet["elevation_checks"]["hardware_allocation_stable"] is True

    unsigned = dict(packet)
    digest = unsigned.pop("forensic_sha256")
    assert digest == forensic_hash(unsigned)
    assert digest == build_packet()["forensic_sha256"]


def test_phi_packet_manifest_links_to_packet(tmp_path: Path) -> None:
    manifest = write_packet(tmp_path)
    packet_path = Path(manifest["packet"])
    packet = json.loads(packet_path.read_text(encoding="utf-8"))

    assert packet_path.exists()
    assert manifest["packet_sha256"] == packet["forensic_sha256"]
    assert manifest["all_elevation_checks_pass"] is True

    unsigned_manifest = dict(manifest)
    digest = unsigned_manifest.pop("forensic_sha256")
    assert digest == forensic_hash(unsigned_manifest)
