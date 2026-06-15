from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

try:
    import numpy as np
except ModuleNotFoundError:
    np = None  # type: ignore[assignment]
    HAS_NUMPY = False
else:
    HAS_NUMPY = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from scripts.generate_consciousness_evidence_packet import (  # noqa: E402
    build_packet,
    canonical_bytes,
    connectivity_matrix,
    deterministic_histories,
    measure_point,
    write_packet,
)


pytestmark = pytest.mark.skipif(not HAS_NUMPY, reason="NumPy is required")


def test_consciousness_iit_packet_is_deterministic() -> None:
    first = build_packet()
    second = build_packet()

    assert first == second
    digest = first["forensic_sha256"]
    unsigned = dict(first)
    unsigned.pop("forensic_sha256")
    assert digest == hashlib.sha256(canonical_bytes(unsigned)).hexdigest()


def test_consciousness_iit_packet_contains_elevation_controls() -> None:
    packet = build_packet()
    points = packet["evidence_points"]

    assert set(points) == {
        "disconnected_ablation",
        "weak_connectivity_control",
        "ring_integration_control",
        "strong_integration_candidate",
        "fragmented_control",
    }
    assert packet["comparisons"]["connectivity_monotonicity"] is True
    assert packet["comparisons"]["disconnected_phi_zero"] is True
    assert "stateful_feedback_control" in packet["comparisons"]["baselines_present"]


@pytest.mark.parametrize("name", ["disconnected_ablation", "strong_integration_candidate", "fragmented_control"])
def test_evidence_points_are_bounded(name: str) -> None:
    packet = build_packet()
    point = packet["evidence_points"][name]

    assert 0.0 <= point["phi_integrated"] <= 1.0
    assert -1.0 <= point["phi_causal"] <= 1.0
    assert 0.0 <= point["complexity"] <= 1.0
    assert point["entropy"] >= 0.0
    assert point["iit_phi_max"] >= 0.0
    assert point["iit_total_phi"] >= 0.0
    assert point["iit_quale_dimensionality"] >= 0


def test_connectivity_matrices_preserve_expected_order() -> None:
    disconnected = connectivity_matrix("disconnected")
    weak = connectivity_matrix("weak")
    strong = connectivity_matrix("strong")

    assert float(np.sum(disconnected)) == 0.0
    assert float(np.sum(strong)) > float(np.sum(weak)) > float(np.sum(disconnected))
    assert np.allclose(np.diag(strong), 0.0)


def test_stronger_connectivity_dominates_weak_control() -> None:
    history = deterministic_histories()["balanced_stable"]
    weak = measure_point("weak", history, connectivity="weak")
    strong = measure_point("strong", history, connectivity="strong")

    assert strong.iit_phi_max >= weak.iit_phi_max
    assert strong.iit_total_phi >= 0.0
    assert weak.iit_total_phi >= 0.0


def test_packet_writer_emits_manifest_and_packet(tmp_path: Path) -> None:
    manifest = write_packet(tmp_path)
    packet_path = Path(manifest["packet"])

    assert packet_path.exists()
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    assert packet["forensic_sha256"] == manifest["forensic_sha256"]
    assert (tmp_path / "consciousness_iit_evidence_manifest.json").exists()
