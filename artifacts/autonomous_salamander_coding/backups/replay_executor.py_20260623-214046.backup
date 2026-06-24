"""Deterministic replay execution for reproducibility attestations.

The replay executor is deliberately local-only. It does not construct networked
build environments, fetch dependencies, submit mining work, or certify external
truth. It verifies the declared dependency pins against the current interpreter,
injects deterministic seed environment variables, runs replay commands, and
hashes canonical command output so evidence gates can perform dynamic replay in
addition to static digest checks.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
from pathlib import Path
import sys
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .scientific_rigor_kernel import ReproducibilityAttestation


class ReplayExecutionError(RuntimeError):
    """Raised when a replay cannot be executed or verified."""


@dataclass(frozen=True)
class ReplayCommandResult:
    """Canonical command execution output captured for replay hashing."""

    command: str
    returncode: int
    stdout: str
    stderr: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FalsificationProbeResult:
    """Result of a negative replay probe.

    ``falsified`` means the intentionally mutated replay failed to reproduce the
    approved digest. That is the desired outcome for a valid falsification
    route: boundaries are actionable only when the negative control diverges.
    """

    claim_id: str
    falsified: bool
    mutation: dict[str, Any]
    failure_reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FalsificationSuiteResult:
    """Coverage report for all declared falsification routes."""

    claim_id: str
    total_routes: int
    falsified_routes: int
    coverage_percent: float
    results: tuple[FalsificationProbeResult, ...]
    failures: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EnvironmentSnapshot:
    """Replay-relevant environment fingerprint for diagnostics and locks."""

    python_version: str
    platform: str
    libc: str
    python_hash_seed: str
    packages: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplayArtifactDigest:
    """Byte digest for a declared replay artifact."""

    path: str
    sha256: str
    size_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplayExecutionResult:
    """Result of executing a reproducibility attestation replay."""

    claim_id: str
    output_digest: str
    expected_output_digest: str
    verified: bool
    command_results: tuple[ReplayCommandResult, ...]
    artifact_digests: tuple[ReplayArtifactDigest, ...]
    environment_checked: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["command_results"] = [result.to_dict() for result in self.command_results]
        data["artifact_digests"] = [
            artifact.to_dict() for artifact in self.artifact_digests
        ]
        return data


@dataclass(frozen=True)
class ReplayStressResult:
    """Multi-run determinism result for replay attestations."""

    claim_id: str
    runs: int
    verified: bool
    output_digest: str
    observed_digests: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def hash_replay_artifacts(
    produced_artifacts: Sequence[str], cwd: str | os.PathLike[str] | None = None
) -> tuple[ReplayArtifactDigest, ...]:
    """Hash declared artifact file bytes in deterministic path order."""

    root = Path(cwd or os.getcwd())
    digests: list[ReplayArtifactDigest] = []
    for rel_path in sorted(
        str(path).strip() for path in produced_artifacts if str(path).strip()
    ):
        artifact_path = root / rel_path
        if not artifact_path.is_file():
            raise ReplayExecutionError(f"declared replay artifact missing: {rel_path}")
        data = artifact_path.read_bytes()
        digests.append(
            ReplayArtifactDigest(
                path=rel_path,
                sha256=hashlib.sha256(data).hexdigest(),
                size_bytes=len(data),
            )
        )
    return tuple(digests)


def canonical_replay_output_digest(
    command_results: Sequence[ReplayCommandResult],
    artifact_digests: Sequence[ReplayArtifactDigest] = (),
) -> str:
    """Hash command output and declared artifact digests in stable JSON form."""

    payload = {
        "artifacts": [artifact.to_dict() for artifact in artifact_digests],
        "commands": [result.to_dict() for result in command_results],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _pin_matches(actual: str, expected: str) -> bool:
    expected = str(expected).strip()
    if not expected or expected == "*":
        return True
    if expected.endswith(".*"):
        return actual.startswith(expected[:-1])
    return actual == expected


def _installed_version(package: str) -> str:
    normalized = package.lower().replace("_", "-")
    if normalized == "python":
        return sys.version.split()[0]
    if normalized == "platform":
        return platform.platform()
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError as exc:
        raise ReplayExecutionError(
            f"dependency pin {package!r} is not installed"
        ) from exc


def verify_dependency_pins(dependency_pins: Mapping[str, str]) -> dict[str, str]:
    """Fail fast when the current runtime does not satisfy declared pins."""

    checked: dict[str, str] = {}
    for package, expected in sorted(dependency_pins.items()):
        actual = _installed_version(str(package))
        if not _pin_matches(actual, str(expected)):
            raise ReplayExecutionError(
                f"dependency pin mismatch for {package}: expected {expected!r}, got {actual!r}"
            )
        checked[str(package)] = actual
    return checked


def _seed_environment(
    seeds: Mapping[str, int], env_overrides: Mapping[str, str] | None = None
) -> dict[str, str]:
    env = os.environ.copy()
    for name, value in seeds.items():
        env[f"PYTHIA_REPLAY_SEED_{str(name).upper()}"] = str(int(value))
    if "python_hash_seed" in seeds:
        env["PYTHONHASHSEED"] = str(int(seeds["python_hash_seed"]))
    for name, value in (env_overrides or {}).items():
        env[str(name)] = str(value)
    return env


def execute_reproducibility_replay(
    attestation: ReproducibilityAttestation | Mapping[str, Any],
    *,
    expected_output_digest: str | None = None,
    cwd: str | os.PathLike[str] | None = None,
    timeout_seconds: float = 60.0,
    env_overrides: Mapping[str, str] | None = None,
) -> ReplayExecutionResult:
    """Execute attested replay commands and verify their canonical output digest.

    ``expected_output_digest`` is intentionally separate from the attestation's
    metadata ``replay_digest``. The latter proves the envelope did not drift;
    this function proves the command outputs replay to an explicitly declared
    output digest. Callers may pass a plain mapping from a manifest object or a
    ``ReproducibilityAttestation`` instance.
    """

    data = (
        attestation.to_dict()
        if isinstance(attestation, ReproducibilityAttestation)
        else dict(attestation)
    )
    expected = (
        expected_output_digest
        or data.get("expected_output_digest")
        or data.get("output_digest")
    )
    if not expected:
        raise ReplayExecutionError(
            "expected_output_digest is required for dynamic replay verification"
        )
    commands = tuple(
        str(command).strip()
        for command in data.get("commands", ())
        if str(command).strip()
    )
    if not commands:
        raise ReplayExecutionError("at least one replay command is required")
    environment_checked = verify_dependency_pins(data.get("dependency_pins", {}))
    env = _seed_environment(data.get("seeds", {}), env_overrides=env_overrides)
    command_results: list[ReplayCommandResult] = []
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            shell=True,
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
        )
        result = ReplayCommandResult(
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
        command_results.append(result)
        if completed.returncode != 0:
            raise ReplayExecutionError(
                f"replay command failed with exit code {completed.returncode}: {command}"
            )
    artifact_digests = hash_replay_artifacts(
        data.get("produced_artifacts", ()), cwd=cwd
    )
    output_digest = canonical_replay_output_digest(command_results, artifact_digests)
    verified = output_digest == expected
    if not verified:
        raise ReplayExecutionError(
            f"replay output digest mismatch: expected {expected}, got {output_digest}"
        )
    return ReplayExecutionResult(
        claim_id=str(data.get("claim_id", "")),
        output_digest=output_digest,
        expected_output_digest=expected,
        verified=True,
        command_results=tuple(command_results),
        artifact_digests=artifact_digests,
        environment_checked=environment_checked,
    )


def execute_falsification_probe(
    attestation: ReproducibilityAttestation | Mapping[str, Any],
    *,
    seed_overrides: Mapping[str, int] | None = None,
    dependency_pin_overrides: Mapping[str, str] | None = None,
    env_overrides: Mapping[str, str] | None = None,
    expected_output_digest: str | None = None,
    cwd: str | os.PathLike[str] | None = None,
    timeout_seconds: float = 60.0,
) -> FalsificationProbeResult:
    """Run an intentional negative-control replay and require divergence.

    This operationalizes attestation falsification routes. The probe copies the
    approved attestation, applies explicit seed or dependency-pin mutations, and
    then runs normal replay verification. The probe succeeds only if that mutated
    replay fails with a digest/environment/command error. If the mutated replay
    still verifies, the claim boundary is not falsifiable by this probe and the
    function raises ``ReplayExecutionError``.
    """

    data = (
        attestation.to_dict()
        if isinstance(attestation, ReproducibilityAttestation)
        else dict(attestation)
    )
    mutated = dict(data)
    mutated["seeds"] = {**dict(data.get("seeds", {})), **dict(seed_overrides or {})}
    mutated["dependency_pins"] = {
        **dict(data.get("dependency_pins", {})),
        **dict(dependency_pin_overrides or {}),
    }
    mutation = {
        "seed_overrides": dict(seed_overrides or {}),
        "dependency_pin_overrides": dict(dependency_pin_overrides or {}),
        "env_overrides": dict(env_overrides or {}),
    }
    if (
        not mutation["seed_overrides"]
        and not mutation["dependency_pin_overrides"]
        and not mutation["env_overrides"]
    ):
        raise ReplayExecutionError("falsification probe requires at least one mutation")
    try:
        execute_reproducibility_replay(
            mutated,
            expected_output_digest=expected_output_digest,
            cwd=cwd,
            timeout_seconds=timeout_seconds,
            env_overrides=env_overrides,
        )
    except ReplayExecutionError as exc:
        return FalsificationProbeResult(
            claim_id=str(data.get("claim_id", "")),
            falsified=True,
            mutation=mutation,
            failure_reason=str(exc),
        )
    raise ReplayExecutionError(
        "falsification probe did not diverge; mutated replay still matched expected output"
    )


def capture_environment_snapshot(
    packages: Sequence[str] = ("numpy", "scipy")
) -> EnvironmentSnapshot:
    """Capture replay-relevant local environment diagnostics."""

    captured: dict[str, str] = {}
    for package in packages:
        try:
            captured[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            captured[package] = "not-installed"
    libc_name, libc_version = platform.libc_ver()
    return EnvironmentSnapshot(
        python_version=sys.version.split()[0],
        platform=platform.platform(),
        libc=f"{libc_name} {libc_version}".strip() or "unknown",
        python_hash_seed=os.environ.get("PYTHONHASHSEED", ""),
        packages=captured,
    )


def generate_requirements_lock(packages: Sequence[str] = ("numpy", "scipy")) -> str:
    """Generate a minimal pip-style lock snippet from installed package versions."""

    snapshot = capture_environment_snapshot(packages)
    return "\n".join(
        f"{name}=={version}"
        for name, version in sorted(snapshot.packages.items())
        if version != "not-installed"
    )


def _claim_from_manifest_or_claim(
    manifest_or_claim: Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(manifest_or_claim.get("claim"), dict):
        return dict(manifest_or_claim["claim"])
    return dict(manifest_or_claim)


def run_full_falsification_suite(
    manifest_or_claim: Mapping[str, Any],
    *,
    cwd: str | os.PathLike[str] | None = None,
    timeout_seconds: float = 60.0,
) -> FalsificationSuiteResult:
    """Run every declared falsification route and report coverage."""

    claim = _claim_from_manifest_or_claim(manifest_or_claim)
    attestation = claim["reproducibility_attestation"]
    routes = tuple(claim.get("falsification_routes", ()))
    results: list[FalsificationProbeResult] = []
    failures: list[str] = []
    for route in routes:
        name = str(route.get("name", "unnamed_route"))
        try:
            result = execute_falsification_probe(
                attestation,
                seed_overrides=route.get("seed_overrides", {}),
                dependency_pin_overrides=route.get("dependency_pin_overrides", {}),
                env_overrides=route.get("env_overrides", {}),
                cwd=cwd,
                timeout_seconds=timeout_seconds,
            )
            results.append(result)
        except ReplayExecutionError as exc:
            failures.append(f"{name}: {exc}")
    total = len(routes)
    coverage = (len(results) / total * 100.0) if total else 0.0
    return FalsificationSuiteResult(
        claim_id=str(claim.get("id", attestation.get("claim_id", ""))),
        total_routes=total,
        falsified_routes=len(results),
        coverage_percent=coverage,
        results=tuple(results),
        failures=tuple(failures),
    )


def replay_stress_test(
    attestation: ReproducibilityAttestation | Mapping[str, Any],
    *,
    runs: int = 50,
    cwd: str | os.PathLike[str] | None = None,
    timeout_seconds: float = 60.0,
) -> ReplayStressResult:
    """Run a replay repeatedly and require identical verified output digests."""

    if runs < 1:
        raise ReplayExecutionError("stress test requires at least one run")
    observed: list[str] = []
    claim_id = ""
    for index in range(runs):
        try:
            result = execute_reproducibility_replay(
                attestation, cwd=cwd, timeout_seconds=timeout_seconds
            )
        except ReplayExecutionError as exc:
            raise ReplayExecutionError(
                f"stress run {index + 1}/{runs} failed: {exc}"
            ) from exc
        claim_id = result.claim_id
        observed.append(result.output_digest)
    unique = set(observed)
    if len(unique) != 1:
        raise ReplayExecutionError(
            f"stress replay produced non-deterministic digests: {sorted(unique)}"
        )
    return ReplayStressResult(
        claim_id=claim_id,
        runs=runs,
        verified=True,
        output_digest=observed[0],
        observed_digests=tuple(observed),
    )


__all__ = [
    "EnvironmentSnapshot",
    "FalsificationProbeResult",
    "FalsificationSuiteResult",
    "ReplayArtifactDigest",
    "ReplayCommandResult",
    "ReplayExecutionError",
    "ReplayExecutionResult",
    "ReplayStressResult",
    "canonical_replay_output_digest",
    "capture_environment_snapshot",
    "execute_falsification_probe",
    "execute_reproducibility_replay",
    "generate_requirements_lock",
    "hash_replay_artifacts",
    "replay_stress_test",
    "run_full_falsification_suite",
    "verify_dependency_pins",
]
