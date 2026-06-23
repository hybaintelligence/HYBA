from __future__ import annotations

import sys

import pytest

from pythia_mining.replay_executor import (
    ReplayCommandResult,
    ReplayExecutionError,
    canonical_replay_output_digest,
    execute_reproducibility_replay,
)
from pythia_mining.scientific_rigor_kernel import build_reproducibility_attestation


def _command_for(message: str) -> str:
    return f'{sys.executable} -c "print({message!r})"'


def test_replay_executor_verifies_valid_claim_output_digest(tmp_path) -> None:
    command = _command_for("bounded replay ok")
    expected_digest = canonical_replay_output_digest(
        [
            ReplayCommandResult(
                command=command, returncode=0, stdout="bounded replay ok\n", stderr=""
            )
        ]
    )
    attestation = build_reproducibility_attestation(
        claim_id="runtime_integration_proxy_not_consciousness_claim",
        inputs={"message": "bounded replay ok"},
        commands=[command],
        seeds={"python_hash_seed": 0},
        dependency_pins={
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.*"
        },
        boundary="Local deterministic replay only; not phenomenal consciousness or external validation.",
    ).to_dict()
    attestation["expected_output_digest"] = expected_digest

    result = execute_reproducibility_replay(attestation, cwd=tmp_path)

    assert result.verified is True
    assert result.output_digest == expected_digest
    assert result.claim_id == "runtime_integration_proxy_not_consciousness_claim"
    assert result.environment_checked["python"].startswith(
        f"{sys.version_info.major}.{sys.version_info.minor}."
    )


def test_replay_executor_rejects_invalid_seed_output_digest(tmp_path) -> None:
    command = _command_for("seed 43 output")
    stale_seed_42_digest = canonical_replay_output_digest(
        [
            ReplayCommandResult(
                command=command, returncode=0, stdout="seed 42 output\n", stderr=""
            )
        ]
    )
    attestation = build_reproducibility_attestation(
        claim_id="phi_scaling_bounded",
        inputs={"message": "seed 43 output"},
        commands=[command],
        seeds={"python_hash_seed": 43},
        dependency_pins={
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.*"
        },
    ).to_dict()
    attestation["expected_output_digest"] = stale_seed_42_digest

    with pytest.raises(ReplayExecutionError, match="replay output digest mismatch"):
        execute_reproducibility_replay(attestation, cwd=tmp_path)


def test_replay_executor_fails_fast_on_dependency_pin_mismatch(tmp_path) -> None:
    command = _command_for("unreachable")
    attestation = build_reproducibility_attestation(
        claim_id="phi_scaling_bounded",
        inputs={"message": "unreachable"},
        commands=[command],
        dependency_pins={"python": "0.0.0"},
    ).to_dict()
    attestation["expected_output_digest"] = "0" * 64

    with pytest.raises(ReplayExecutionError, match="dependency pin mismatch"):
        execute_reproducibility_replay(attestation, cwd=tmp_path)


def test_falsification_probe_passes_when_seed_mutation_diverges(tmp_path) -> None:
    command = (
        f'{sys.executable} -c "import os; '
        "print(os.environ['PYTHIA_REPLAY_SEED_NUMPY'])\""
    )
    expected_digest = canonical_replay_output_digest(
        [ReplayCommandResult(command=command, returncode=0, stdout="42\n", stderr="")]
    )
    attestation = build_reproducibility_attestation(
        claim_id="phi_scaling_bounded",
        inputs={"seed": 42},
        commands=[command],
        seeds={"numpy": 42},
        dependency_pins={
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.*"
        },
        boundary="Changing numpy seed is an actionable falsification route for this replay.",
    ).to_dict()
    attestation["expected_output_digest"] = expected_digest

    from pythia_mining.replay_executor import execute_falsification_probe

    probe = execute_falsification_probe(
        attestation, seed_overrides={"numpy": 43}, cwd=tmp_path
    )

    assert probe.falsified is True
    assert probe.mutation["seed_overrides"] == {"numpy": 43}
    assert "replay output digest mismatch" in probe.failure_reason


def test_falsification_probe_rejects_non_diverging_mutation(tmp_path) -> None:
    command = _command_for("constant output")
    expected_digest = canonical_replay_output_digest(
        [
            ReplayCommandResult(
                command=command, returncode=0, stdout="constant output\n", stderr=""
            )
        ]
    )
    attestation = build_reproducibility_attestation(
        claim_id="phi_scaling_bounded",
        inputs={"message": "constant output"},
        commands=[command],
        seeds={"numpy": 42},
        dependency_pins={
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.*"
        },
    ).to_dict()
    attestation["expected_output_digest"] = expected_digest

    from pythia_mining.replay_executor import execute_falsification_probe

    with pytest.raises(ReplayExecutionError, match="did not diverge"):
        execute_falsification_probe(
            attestation, seed_overrides={"numpy": 43}, cwd=tmp_path
        )


def test_replay_executor_hashes_declared_output_artifacts(tmp_path) -> None:
    from pythia_mining.replay_executor import ReplayArtifactDigest

    command = (
        f'{sys.executable} -c "from pathlib import Path; '
        "Path('proof.txt').write_text('artifact-proof'); print('done')\""
    )
    expected_artifact = ReplayArtifactDigest(
        path="proof.txt",
        sha256="9fc5489cec867591e6d96148a6321d45b952c3ab82d9b857d3f474a81a4156a6",
        size_bytes=len("artifact-proof"),
    )
    expected_digest = canonical_replay_output_digest(
        [
            ReplayCommandResult(
                command=command, returncode=0, stdout="done\n", stderr=""
            )
        ],
        [expected_artifact],
    )
    attestation = build_reproducibility_attestation(
        claim_id="artifact_claim",
        inputs={"artifact": "proof.txt"},
        commands=[command],
        produced_artifacts=["proof.txt"],
        dependency_pins={
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.*"
        },
    ).to_dict()
    attestation["expected_output_digest"] = expected_digest

    result = execute_reproducibility_replay(attestation, cwd=tmp_path)

    assert result.verified is True
    assert result.artifact_digests == (expected_artifact,)


def test_replay_stress_test_accepts_repeatable_claim(tmp_path) -> None:
    from pythia_mining.replay_executor import replay_stress_test

    command = _command_for("stable")
    expected_digest = canonical_replay_output_digest(
        [
            ReplayCommandResult(
                command=command, returncode=0, stdout="stable\n", stderr=""
            )
        ]
    )
    attestation = build_reproducibility_attestation(
        claim_id="stable_claim",
        inputs={"message": "stable"},
        commands=[command],
        dependency_pins={
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.*"
        },
    ).to_dict()
    attestation["expected_output_digest"] = expected_digest

    result = replay_stress_test(attestation, runs=3, cwd=tmp_path)

    assert result.verified is True
    assert result.runs == 3
    assert len(set(result.observed_digests)) == 1


def test_replay_stress_test_rejects_flaky_claim(tmp_path) -> None:
    from pythia_mining.replay_executor import replay_stress_test

    command = f'{sys.executable} -c "import time; print(time.time_ns())"'
    attestation = build_reproducibility_attestation(
        claim_id="flaky_claim",
        inputs={"message": "flaky"},
        commands=[command],
        dependency_pins={
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.*"
        },
    ).to_dict()
    attestation["expected_output_digest"] = "0" * 64

    with pytest.raises(ReplayExecutionError, match="stress run 1/2 failed"):
        replay_stress_test(attestation, runs=2, cwd=tmp_path)


def test_full_falsification_suite_reports_coverage(tmp_path) -> None:
    from pythia_mining.replay_executor import run_full_falsification_suite

    command = (
        f'{sys.executable} -c "import os; '
        "print(os.environ['PYTHIA_REPLAY_SEED_NONCE'])\""
    )
    expected_digest = canonical_replay_output_digest(
        [ReplayCommandResult(command=command, returncode=0, stdout="42\n", stderr="")]
    )
    attestation = build_reproducibility_attestation(
        claim_id="suite_claim",
        inputs={"nonce": 42},
        commands=[command],
        seeds={"nonce": 42},
        dependency_pins={
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.*"
        },
    ).to_dict()
    attestation["expected_output_digest"] = expected_digest
    claim = {
        "id": "suite_claim",
        "reproducibility_attestation": attestation,
        "falsification_routes": [
            {"name": "nonce_mutation", "seed_overrides": {"nonce": 43}},
            {"name": "bad_python_pin", "dependency_pin_overrides": {"python": "0.0.0"}},
        ],
    }

    result = run_full_falsification_suite(claim, cwd=tmp_path)

    assert result.total_routes == 2
    assert result.falsified_routes == 2
    assert result.coverage_percent == 100.0
    assert not result.failures


def test_environment_snapshot_and_requirements_lock_are_diagnostic() -> None:
    from pythia_mining.replay_executor import (
        capture_environment_snapshot,
        generate_requirements_lock,
    )

    snapshot = capture_environment_snapshot(packages=("definitely-not-installed-hyba",))
    lock = generate_requirements_lock(packages=("definitely-not-installed-hyba",))

    assert snapshot.python_version.startswith(
        f"{sys.version_info.major}.{sys.version_info.minor}."
    )
    assert snapshot.packages["definitely-not-installed-hyba"] == "not-installed"
    assert lock == ""
