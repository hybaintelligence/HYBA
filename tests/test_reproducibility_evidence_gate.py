from __future__ import annotations

import importlib.util
from pathlib import Path

from pythia_mining.scientific_rigor_kernel import build_reproducibility_attestation

ROOT = Path(__file__).resolve().parents[1]


def _load_claim_tier_guard():
    spec = importlib.util.spec_from_file_location(
        "check_validation_claim_tiers", ROOT / "scripts" / "check_validation_claim_tiers.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reproducibility_attestation_gate_accepts_builder_output(tmp_path) -> None:
    guard = _load_claim_tier_guard()
    commands = ["PYTHONPATH=python_backend pytest tests/test_scientific_rigor_kernel.py -q"]
    attestation = build_reproducibility_attestation(
        claim_id="runtime_integration_proxy_not_consciousness_claim",
        inputs={"sample": {"phi": 0.5, "status": "bounded_proxy"}},
        commands=commands,
        seeds={"numpy": 42},
        dependency_pins={"python": "3.12"},
        boundary="Local deterministic replay only; not phenomenal consciousness or external validation.",
    ).to_dict()
    attestation["inputs"] = {"sample": {"status": "bounded_proxy", "phi": 0.5}}

    guard._validate_reproducibility_attestation(
        tmp_path / "manifest.json",
        "runtime_integration_proxy_not_consciousness_claim",
        {"commands": commands, "reproducibility_attestation": attestation},
    )


def test_reproducibility_attestation_gate_rejects_digest_tampering(tmp_path) -> None:
    guard = _load_claim_tier_guard()
    commands = ["PYTHONPATH=python_backend pytest tests/test_scientific_rigor_kernel.py -q"]
    attestation = build_reproducibility_attestation(
        claim_id="runtime_integration_proxy_not_consciousness_claim",
        inputs={"sample": {"phi": 0.5, "status": "bounded_proxy"}},
        commands=commands,
        seeds={"numpy": 42},
        dependency_pins={"python": "3.12"},
        boundary="Local deterministic replay only; not phenomenal consciousness or external validation.",
    ).to_dict()
    attestation["inputs"] = {"sample": {"status": "bounded_proxy", "phi": 0.5}}
    attestation["replay_digest"] = "0" * 64

    try:
        guard._validate_reproducibility_attestation(
            tmp_path / "manifest.json",
            "runtime_integration_proxy_not_consciousness_claim",
            {"commands": commands, "reproducibility_attestation": attestation},
        )
    except AssertionError as exc:
        assert "replay_digest mismatch" in str(exc)
    else:  # pragma: no cover - explicit failure path for pytest output clarity
        raise AssertionError("tampered replay digest was accepted")
