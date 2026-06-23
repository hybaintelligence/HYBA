"""VALIDATION TIER: PHYSICAL UBIQUITY.

Compiles the dependency-free Rust blastema seed and verifies it accepts the same
canonical replay manifest emitted by the Python substrate.
"""

import json
import subprocess

from pythia_mining.salamander_frontier import (
    CrossLanguageReplayManifest,
    ImmutableEvidenceLog,
)


def test_e2e_rust_blastema_seed_accepts_python_manifest(tmp_path):
    audit_log = (
        ImmutableEvidenceLog()
        .append("agent_spawned", actor="python-agent", timestamp=1.0, job_id="job-1")
        .append("search_started", actor="python-agent", timestamp=2.0, start_nonce=1000)
        .append("job_completed", actor="python-agent", timestamp=3.0)
    )
    manifest = CrossLanguageReplayManifest(audit_log).to_manifest()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    binary_path = tmp_path / "salamander_blastema_seed"

    compile_result = subprocess.run(
        ["rustc", "runtime_seeds/salamander_blastema_seed.rs", "-o", str(binary_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert compile_result.returncode == 0, compile_result.stderr

    run_result = subprocess.run(
        [str(binary_path), str(manifest_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert run_result.returncode == 0, run_result.stderr
    assert "SALAMANDER_BLASTEMA_READY" in run_result.stdout
    assert str(manifest_path) in run_result.stdout
