from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pythia_mining.mining_auto_attester import emit_attested_mining_success_manifest

ROOT = Path(__file__).resolve().parents[1]


def _write_manifest(tmp_path: Path) -> Path:
    (tmp_path / "proof.txt").write_text("nonce=42\n", encoding="utf-8")
    command = (
        f'{sys.executable} -c "import os; from pathlib import Path; '
        "nonce=os.environ['PYTHIA_REPLAY_SEED_NONCE']; "
        "Path('proof.txt').write_text('nonce=' + nonce + chr(10)); print('ok')\""
    )
    manifest = emit_attested_mining_success_manifest(
        claim_id="cli_replay_claim",
        claim="CLI replay claim emits deterministic artifact.",
        replay_command=command,
        replay_stdout="ok\n",
        inputs={"proof": "nonce=42"},
        seeds={"nonce": 42, "python_hash_seed": 0},
        produced_artifacts=["proof.txt"],
        artifact_root=str(tmp_path),
        falsification_seed_overrides={"nonce": 43},
    ).to_dict()
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_replay_claim_cli_replays_and_stresses_manifest(tmp_path) -> None:
    manifest_path = _write_manifest(tmp_path)

    replay = subprocess.run(
        [sys.executable, "scripts/replay_claim.py", str(manifest_path), "--cwd", str(tmp_path)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    stress = subprocess.run(
        [
            sys.executable,
            "scripts/replay_claim.py",
            str(manifest_path),
            "--cwd",
            str(tmp_path),
            "--stress",
            "2",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert replay.returncode == 0, replay.stderr
    assert "Replay verified" in replay.stdout
    falsify = subprocess.run(
        [
            sys.executable,
            "scripts/replay_claim.py",
            str(manifest_path),
            "--cwd",
            str(tmp_path),
            "--falsify",
            "seed_mutation_negative_control",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert stress.returncode == 0, stress.stderr
    assert "Stress replay verified" in stress.stdout
    falsify_all = subprocess.run(
        [
            sys.executable,
            "scripts/replay_claim.py",
            str(manifest_path),
            "--cwd",
            str(tmp_path),
            "--falsify-all",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert falsify.returncode == 0, falsify.stderr
    assert "Falsification verified" in falsify.stdout
    assert falsify_all.returncode == 0, falsify_all.stderr
    assert "Falsification suite verified" in falsify_all.stdout


def test_replay_claim_cli_subcommands_cover_core_workflows(tmp_path) -> None:
    manifest_path = _write_manifest(tmp_path)
    registry_dir = tmp_path / "registry"

    replay = subprocess.run(
        [
            sys.executable,
            "scripts/replay_claim.py",
            "replay",
            str(manifest_path),
            "--cwd",
            str(tmp_path),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    stress = subprocess.run(
        [
            sys.executable,
            "scripts/replay_claim.py",
            "stress",
            str(manifest_path),
            "--runs",
            "2",
            "--cwd",
            str(tmp_path),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    register = subprocess.run(
        [
            sys.executable,
            "scripts/replay_claim.py",
            "register",
            str(manifest_path),
            str(registry_dir),
            "--cwd",
            str(tmp_path),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    listed = subprocess.run(
        [sys.executable, "scripts/replay_claim.py", "list", str(registry_dir)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    reverify = subprocess.run(
        [
            sys.executable,
            "scripts/replay_claim.py",
            "reverify",
            str(registry_dir),
            "cli_replay_claim",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )

    assert replay.returncode == 0, replay.stderr
    assert stress.returncode == 0, stress.stderr
    assert register.returncode == 0, register.stderr
    assert listed.returncode == 0, listed.stderr
    assert "cli_replay_claim" in listed.stdout
    assert reverify.returncode == 0, reverify.stderr
