from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from pythia_mining.mining_auto_attester import emit_attested_mining_success_manifest
from pythia_mining.replay_executor import (
    execute_falsification_probe,
    execute_reproducibility_replay,
)

ROOT = Path(__file__).resolve().parents[1]


def _load_claim_tier_guard():
    spec = importlib.util.spec_from_file_location(
        "check_validation_claim_tiers", ROOT / "scripts" / "check_validation_claim_tiers.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mining_success_manifest_passes_gate_replay_and_falsification(tmp_path) -> None:
    artifact = tmp_path / "nonce_proof.txt"
    artifact.write_text("nonce=42\n", encoding="utf-8")
    command = (
        f'{sys.executable} -c "import os; from pathlib import Path; '
        "nonce=os.environ['PYTHIA_REPLAY_SEED_NONCE']; "
        "Path('nonce_proof.txt').write_text('nonce=' + nonce + chr(10)); "
        "print('artifact-written')\""
    )
    manifest = emit_attested_mining_success_manifest(
        claim_id="simulated_local_nonce_success",
        claim="Simulated local nonce success emits a replayable attested manifest.",
        replay_command=command,
        replay_stdout="artifact-written\n",
        inputs={"block_height": 1, "nonce": 42},
        seeds={"nonce": 42, "python_hash_seed": 0},
        produced_artifacts=["nonce_proof.txt"],
        artifact_root=str(tmp_path),
        falsification_seed_overrides={"nonce": 43},
    ).to_dict()
    claim = manifest["claim"]
    attestation = claim["reproducibility_attestation"]

    guard = _load_claim_tier_guard()
    guard._validate_reproducibility_attestation(tmp_path / "manifest.json", claim["id"], claim)

    replay = execute_reproducibility_replay(attestation, cwd=tmp_path)
    assert replay.verified is True

    route = claim["falsification_routes"][0]
    probe = execute_falsification_probe(
        attestation,
        seed_overrides=route["seed_overrides"],
        cwd=tmp_path,
    )
    assert probe.falsified is True
    assert "replay output digest mismatch" in probe.failure_reason
