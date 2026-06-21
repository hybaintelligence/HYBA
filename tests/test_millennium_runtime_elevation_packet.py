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
    assert packet["all_contracts_satisfied"] is False
    assert "no Millennium Problem proof claims" in packet["fullstack_boundary"]["claim_boundary"]


def test_each_contract_has_runtime_question_controls_and_measurements() -> None:
    contracts = {item["slug"]: item for item in millennium_contracts()}
    packet = build_packet()

    assert set(contracts) == EXPECTED_SLUGS
    for item in packet["contract_results"]:
        contract = contracts[item["slug"]]
        assert contract["runtime_question"]
        assert len(contract["required_controls"]) >= 3
        assert set(contract["evidence_fields"]).issubset(item["measurements"].keys())
        assert set(contract["required_controls"]).issubset(
            item["measurements"]["control_results"].keys()
        )
        assert item["missing_fields"] == []
        assert item["missing_controls"] == []
        if item["slug"] == "riemann-hypothesis":
            assert item["failed_controls"] == ["random_constant_ablation", "spectral_replay"]
            assert item["measurements"]["gue_contract_satisfied"] is False
        else:
            assert item["failed_controls"] == []
            assert all(item["measurements"]["control_results"].values())


def test_domain_measurements_are_computed_controls_not_literals() -> None:
    packet = build_packet()
    by_slug = {item["slug"]: item for item in packet["contract_results"]}

    riemann = by_slug["riemann-hypothesis"]["measurements"]
    assert "spectral_probe_sha256" in riemann
    assert riemann["phi_lcg_r_squared_to_gue"] == 0.0
    assert riemann["gue_contract_satisfied"] is False

    p_vs_np = by_slug["p-vs-np"]["measurements"]
    assert p_vs_np["candidate_reduction_ratio"] == 12 / 64
    assert p_vs_np["candidate_reduction_ratio"] != 1.0 / ((1.0 + 5.0**0.5) / 2.0)
    assert p_vs_np["witness_validity"] is True

    navier = by_slug["navier-stokes"]["measurements"]
    assert navier["max_pressure"] == 6
    assert navier["max_pressure"] != ((1.0 + 5.0**0.5) / 2.0)
    assert navier["flow_regular"] is True

    bsd = by_slug["birch-swinnerton-dyer"]["measurements"]
    assert bsd["resource_signal_state"] == "accepted_share_observed"
    assert bsd["ledger_root_present"] is True


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
    assert packet["schema_version"].endswith(".v3")
    assert manifest["contract_count"] == 7
    assert manifest["imports_hyba_unified_backend"] is False
    assert (tmp_path / "millennium_runtime_elevation_manifest.json").exists()
