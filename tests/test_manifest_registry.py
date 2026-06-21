from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pythia_mining.manifest_registry import list_claims, load_and_reverify, save_verified_manifest
from pythia_mining.mining_auto_attester import emit_attested_mining_success_manifest
from pythia_mining.replay_executor import execute_reproducibility_replay

ROOT = Path(__file__).resolve().parents[1]


def _manifest(tmp_path: Path) -> dict:
    (tmp_path / "proof.txt").write_text("nonce=42\n", encoding="utf-8")
    command = (
        f'{sys.executable} -c "import os; from pathlib import Path; '
        "nonce=os.environ['PYTHIA_REPLAY_SEED_NONCE']; "
        "Path('proof.txt').write_text('nonce=' + nonce + chr(10)); print('ok')\""
    )
    return emit_attested_mining_success_manifest(
        claim_id="registry_nonce_claim",
        claim="Registry nonce claim emits deterministic artifact.",
        replay_command=command,
        replay_stdout="ok\n",
        inputs={"proof": "nonce=42"},
        seeds={"nonce": 42, "python_hash_seed": 0},
        produced_artifacts=["proof.txt"],
        artifact_root=str(tmp_path),
        falsification_seed_overrides={"nonce": 43},
    ).to_dict()


def test_manifest_registry_saves_lists_and_reverifies(tmp_path) -> None:
    registry_dir = tmp_path / "registry"
    manifest = _manifest(tmp_path)
    claim = manifest["claim"]
    replay = execute_reproducibility_replay(claim["reproducibility_attestation"], cwd=tmp_path)

    record = save_verified_manifest(manifest, registry_dir, source_cwd=tmp_path, replay=replay)
    records = list_claims(registry_dir, filter_by_boundary="local deterministic")
    reverified = load_and_reverify(registry_dir, "registry_nonce_claim")

    assert record.claim_id == "registry_nonce_claim"
    assert records == [record]
    assert reverified.record == record
    assert reverified.replay.output_digest == replay.output_digest
    assert (registry_dir / record.manifest_path).exists()
    assert (registry_dir / record.artifact_dir / "proof.txt").read_text(
        encoding="utf-8"
    ) == "nonce=42\n"


def test_replay_claim_cli_registers_lists_and_reverifies(tmp_path) -> None:
    registry_dir = tmp_path / "registry"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_manifest(tmp_path)), encoding="utf-8")

    register = subprocess.run(
        [
            sys.executable,
            "scripts/replay_claim.py",
            str(manifest_path),
            "--cwd",
            str(tmp_path),
            "--register",
            str(registry_dir),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    listed = subprocess.run(
        [sys.executable, "scripts/replay_claim.py", "--list", str(registry_dir)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    reverify = subprocess.run(
        [
            sys.executable,
            "scripts/replay_claim.py",
            "--list",
            str(registry_dir),
            "--reverify",
            "registry_nonce_claim",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert register.returncode == 0, register.stderr
    assert "registered" in register.stdout
    assert listed.returncode == 0, listed.stderr
    assert "registry_nonce_claim" in listed.stdout
    assert reverify.returncode == 0, reverify.stderr
    assert "Registry replay verified" in reverify.stdout
