from __future__ import annotations

import sys

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import HealthCheck, given, settings, strategies as st  # noqa: E402

from pythia_mining.manifest_registry import (
    load_and_reverify,
    save_verified_manifest,
)  # noqa: E402
from pythia_mining.mining_auto_attester import (
    emit_attested_mining_success_manifest,
)  # noqa: E402
from pythia_mining.replay_executor import (  # noqa: E402
    ReplayArtifactDigest,
    ReplayCommandResult,
    canonical_replay_output_digest,
    execute_reproducibility_replay,
    replay_stress_test,
)
from pythia_mining.scientific_rigor_kernel import (
    build_reproducibility_attestation,
)  # noqa: E402

safe_text = st.text(
    alphabet=st.characters(
        blacklist_categories=("Cs",), blacklist_characters="\n\r'\\"
    ),
    min_size=1,
    max_size=24,
)
seed_values = st.integers(min_value=0, max_value=10_000)


@settings(max_examples=30, derandomize=True, deadline=None)
@given(message=safe_text, seed=seed_values)
def test_replay_digest_is_order_stable_for_equivalent_inputs(
    message: str, seed: int
) -> None:
    first = build_reproducibility_attestation(
        "property_claim",
        {"message": message, "nested": {"seed": seed, "flag": True}},
        ["pytest -q"],
        seeds={"python_hash_seed": seed, "numpy": seed + 1},
        dependency_pins={"python": "3.12.*", "numpy": "1.*"},
        produced_artifacts=["proof.txt"],
        boundary="Local deterministic replay only.",
    )
    second = build_reproducibility_attestation(
        "property_claim",
        {"nested": {"flag": True, "seed": seed}, "message": message},
        ["pytest -q"],
        seeds={"numpy": seed + 1, "python_hash_seed": seed},
        dependency_pins={"numpy": "1.*", "python": "3.12.*"},
        produced_artifacts=["proof.txt"],
        boundary="Local deterministic replay only.",
    )

    assert first.input_digest == second.input_digest
    assert first.replay_digest == second.replay_digest


@settings(
    max_examples=20,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(message=safe_text)
def test_replay_matches_expected_digest_under_fixed_command(
    tmp_path, message: str
) -> None:
    command = f'{sys.executable} -c "print({message!r})"'
    expected_digest = canonical_replay_output_digest(
        [
            ReplayCommandResult(
                command=command, returncode=0, stdout=f"{message}\n", stderr=""
            )
        ]
    )
    attestation = build_reproducibility_attestation(
        claim_id="property_replay_claim",
        inputs={"message": message},
        commands=[command],
        dependency_pins={
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.*"
        },
    ).to_dict()
    attestation["expected_output_digest"] = expected_digest

    replay = execute_reproducibility_replay(attestation, cwd=tmp_path)
    stress = replay_stress_test(attestation, runs=2, cwd=tmp_path)

    assert replay.output_digest == expected_digest
    assert stress.output_digest == expected_digest


@settings(
    max_examples=20,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(content=st.binary(min_size=0, max_size=64))
def test_artifact_hashing_folds_file_bytes_into_digest(
    tmp_path, content: bytes
) -> None:
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(content)
    # Use a safer command that writes the pre-created artifact file
    command = f"{sys.executable} -c \"print('ok')\""
    artifact_digest = ReplayArtifactDigest(
        path="artifact.bin",
        sha256=__import__("hashlib").sha256(content).hexdigest(),
        size_bytes=len(content),
    )
    expected_digest = canonical_replay_output_digest(
        [ReplayCommandResult(command=command, returncode=0, stdout="ok\n", stderr="")],
        [artifact_digest],
    )
    attestation = build_reproducibility_attestation(
        claim_id="property_artifact_claim",
        inputs={"artifact_size": len(content)},
        commands=[command],
        produced_artifacts=["artifact.bin"],
        dependency_pins={
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.*"
        },
    ).to_dict()
    attestation["expected_output_digest"] = expected_digest

    result = execute_reproducibility_replay(attestation, cwd=tmp_path)

    assert result.artifact_digests == (artifact_digest,)
    assert result.output_digest == expected_digest


@settings(
    max_examples=10,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(nonce=st.integers(min_value=1, max_value=999))
def test_registry_roundtrip_reverifies_property_manifests(tmp_path, nonce: int) -> None:
    (tmp_path / "proof.txt").write_text(f"nonce={nonce}\n", encoding="utf-8")
    command = (
        f'{sys.executable} -c "import os; from pathlib import Path; '
        "nonce=os.environ['PYTHIA_REPLAY_SEED_NONCE']; "
        "Path('proof.txt').write_text('nonce=' + nonce + chr(10)); print('ok')\""
    )
    manifest = emit_attested_mining_success_manifest(
        claim_id=f"property_registry_{nonce}",
        claim="Property registry claim.",
        replay_command=command,
        replay_stdout="ok\n",
        inputs={"nonce": nonce},
        seeds={"nonce": nonce},
        produced_artifacts=["proof.txt"],
        artifact_root=str(tmp_path),
    ).to_dict()
    record = save_verified_manifest(
        manifest, tmp_path / "registry", source_cwd=tmp_path
    )
    reverified = load_and_reverify(tmp_path / "registry", record.claim_id)

    assert reverified.record == record
    assert reverified.replay.output_digest == record.output_digest
