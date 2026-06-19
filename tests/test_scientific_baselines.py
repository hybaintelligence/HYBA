from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_scientific_baselines import all_baselines, canonical_bytes, generate_artifacts  # noqa: E402


def test_baseline_factory_emits_required_controls() -> None:
    baselines = all_baselines()
    assert set(baselines) == {
        "modular_static",
        "stochastic_noise",
        "coupled_nonadaptive",
        "stateful_feedback_control",
    }
    for name, payload in baselines.items():
        assert payload["schema_version"] == "hyba.science.baseline.v1"
        assert payload["system_type"] == name
        assert "supported_claim" in payload
        assert "claim_boundary" in payload
        digest = payload["forensic_sha256"]
        unsigned = dict(payload)
        unsigned.pop("forensic_sha256")
        assert digest == hashlib.sha256(canonical_bytes(unsigned)).hexdigest()


def test_baselines_separate_coupling_feedback_and_learning() -> None:
    baselines = all_baselines()
    assert (
        baselines["coupled_nonadaptive"]["phi_analog"] > baselines["modular_static"]["phi_analog"]
    )
    assert baselines["coupled_nonadaptive"]["learning_present"] is False
    assert baselines["stateful_feedback_control"]["feedback_loops"] > 0
    assert baselines["stateful_feedback_control"]["learning_present"] is False


def test_generate_artifacts_writes_manifest_and_hashes(tmp_path: Path) -> None:
    manifest = generate_artifacts(tmp_path)
    assert manifest["artifact_count"] == 4
    assert (tmp_path / "baseline_manifest.json").exists()
    for item in manifest["artifacts"]:
        path = Path(item["path"])
        assert path.exists()
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["forensic_sha256"] == item["forensic_sha256"]
