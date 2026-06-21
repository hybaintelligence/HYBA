from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.forensic_spectral_zeta_probe import (  # noqa: E402
    canonical_bytes,
    collect_spacings,
    nonce_stream,
    run_probe,
    su2_plaquette_phases,
    write_probe,
)


def test_phi_lcg_nonce_stream_is_deterministic_and_distinct_from_control() -> None:
    first = nonce_stream(8, "phi_lcg")
    second = nonce_stream(8, "phi_lcg")
    control = nonce_stream(8, "control_lcg")

    assert first == second
    assert first != control
    assert len(set(first)) == len(first)


def test_su2_plaquette_probe_extracts_phase_spacings() -> None:
    phases = su2_plaquette_phases(0xDEADBEEF)
    spacings = collect_spacings(16, "phi_lcg")

    assert len(phases) == 12
    assert all(0.0 <= phase < 2.0 * 3.141592653589793 for phase in phases)
    assert len(spacings) == 16 * 12
    assert abs((sum(spacings) / len(spacings)) - 1.0) < 1e-12


def test_probe_is_signed_replay_stable_and_honestly_falsifiable() -> None:
    first = run_probe(sample_count=64)
    second = run_probe(sample_count=64)

    assert first == second
    assert first["contract_satisfied"] is False
    assert first["samplers"]["phi_lcg"]["r_squared_to_gue_wigner"] == 0.0
    assert "not a proof" in first["claim_boundary"]

    unsigned = dict(first)
    digest = unsigned.pop("forensic_sha256")
    assert digest == hashlib.sha256(canonical_bytes(unsigned)).hexdigest()


def test_probe_writer_preserves_packet(tmp_path: Path) -> None:
    output = tmp_path / "spectral.json"
    packet = write_probe(output, sample_count=32)

    assert output.exists()
    reloaded = json.loads(output.read_text(encoding="utf-8"))
    assert reloaded == packet
