from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_millennium_runtime_elevation_packet import (  # noqa: E402
    build_packet,
    canonical_bytes,
    millennium_contracts,
    phi_resonance_evidence,
    write_packet,
)


EXPECTED_SLUGS = {
    "riemann-hypothesis",
    "p-vs-np",
    "navier-stokes",
    "yang-mills-mass-gap",
    "hodge-conjecture",
    "birch-swinnerton-dyer",
    "poincare-conjecture",
}


def test_packet_extracts_all_seven_domains_without_backend_dependency() -> None:
    packet = build_packet()

    assert packet["fullstack_boundary"]["funding_runtime_separate"] is True
    assert packet["fullstack_boundary"]["imports_hyba_unified_backend"] is False
    assert (
        packet["backend_origin"]["extraction_mode"]
        == "local_contract_extraction_no_runtime_dependency"
    )
    assert {item["slug"] for item in packet["contract_results"]} == EXPECTED_SLUGS
    assert packet["all_contracts_satisfied"] is True


def test_each_contract_has_runtime_question_controls_and_measurements() -> None:
    contracts = {item["slug"]: item for item in millennium_contracts()}
    packet = build_packet()

    assert set(contracts) == EXPECTED_SLUGS
    for item in packet["contract_results"]:
        contract = contracts[item["slug"]]
        assert contract["runtime_question"]
        assert len(contract["required_controls"]) >= 3
        assert set(contract["evidence_fields"]).issubset(item["measurements"].keys())
        assert item["missing_fields"] == []


def test_phi_resonance_is_central_but_not_magic() -> None:
    evidence = phi_resonance_evidence()

    assert evidence["structured_winner"] == "phi"
    assert evidence["phi_structured_dominates"] is True
    assert evidence["noise_winner"] == "uniform"
    assert evidence["phi_not_magic_on_uniform_noise"] is True
    assert evidence["structured_similarity"]["phi"] > evidence["structured_similarity"]["pi"]
    assert evidence["structured_similarity"]["phi"] > evidence["structured_similarity"]["e"]
    assert evidence["noise_similarity"]["uniform"] >= evidence["noise_similarity"]["phi"]


def test_packet_hash_is_forensic_and_replay_stable() -> None:
    first = build_packet()
    second = build_packet()

    assert first == second
    digest = first["forensic_sha256"]
    unsigned = dict(first)
    unsigned.pop("forensic_sha256")
    assert digest == hashlib.sha256(canonical_bytes(unsigned)).hexdigest()


def test_packet_writer_preserves_manifest(tmp_path: Path) -> None:
    manifest = write_packet(tmp_path)
    packet_path = Path(manifest["packet"])

    assert packet_path.exists()
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    assert packet["forensic_sha256"] == manifest["packet_sha256"]
    assert manifest["contract_count"] == 7
    assert manifest["imports_hyba_unified_backend"] is False
    assert (tmp_path / "millennium_runtime_elevation_manifest.json").exists()
