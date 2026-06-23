"""Local append-only-ish registry for verified reproducibility manifests.

The registry is intentionally directory-based and offline. It stores manifest JSON,
replay metadata, and declared artifact bytes under a key derived from claim_id and
input_digest so verified claims can be listed, loaded, and re-verified later.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .replay_executor import ReplayExecutionResult, execute_reproducibility_replay

INDEX_FILE = "index.json"
CLAIMS_DIR = "claims"
ARTIFACTS_DIR = "artifacts"


@dataclass(frozen=True)
class RegistryRecord:
    claim_id: str
    input_digest: str
    replay_digest: str
    record_key: str
    manifest_path: str
    artifact_dir: str
    output_digest: str
    boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReverificationResult:
    record: RegistryRecord
    replay: ReplayExecutionResult

    def to_dict(self) -> dict[str, Any]:
        return {"record": self.record.to_dict(), "replay": self.replay.to_dict()}


def _claim_from_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(manifest.get("claim"), dict):
        return dict(manifest["claim"])
    claims = manifest.get("claims", [])
    if isinstance(claims, list) and claims:
        return dict(claims[0])
    raise ValueError("manifest must contain claim or non-empty claims list")


def _index_path(registry_dir: Path) -> Path:
    return registry_dir / INDEX_FILE


def _load_index(registry_dir: Path) -> dict[str, Any]:
    path = _index_path(registry_dir)
    if not path.exists():
        return {"schema": "HYBA_MANIFEST_REGISTRY_V1", "records": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_index(registry_dir: Path, index: dict[str, Any]) -> None:
    registry_dir.mkdir(parents=True, exist_ok=True)
    _index_path(registry_dir).write_text(
        json.dumps(index, indent=2, sort_keys=True), encoding="utf-8"
    )


def _record_key(claim_id: str, input_digest: str) -> str:
    safe_claim = "".join(
        ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in claim_id
    )
    return f"{safe_claim}--{input_digest[:16]}"


def _copy_artifacts(
    claim: Mapping[str, Any], source_cwd: Path, artifact_dir: Path
) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    attestation = claim["reproducibility_attestation"]
    for rel_path in attestation.get("produced_artifacts", []):
        source = source_cwd / rel_path
        if not source.is_file():
            raise FileNotFoundError(
                f"declared artifact missing during registry save: {rel_path}"
            )
        destination = artifact_dir / rel_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def save_verified_manifest(
    manifest: Mapping[str, Any],
    registry_dir: str | Path,
    *,
    source_cwd: str | Path,
    replay: ReplayExecutionResult | None = None,
) -> RegistryRecord:
    """Verify and persist a manifest plus declared artifacts in the registry."""

    registry_root = Path(registry_dir)
    source_root = Path(source_cwd)
    claim = _claim_from_manifest(manifest)
    attestation = claim["reproducibility_attestation"]
    replay_result = replay or execute_reproducibility_replay(
        attestation, cwd=source_root
    )
    input_digest = str(attestation["input_digest"])
    claim_id = str(claim["id"])
    key = _record_key(claim_id, input_digest)
    record_dir = registry_root / CLAIMS_DIR / key
    artifact_dir = record_dir / ARTIFACTS_DIR
    record_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = record_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    _copy_artifacts(claim, source_root, artifact_dir)
    record = RegistryRecord(
        claim_id=claim_id,
        input_digest=input_digest,
        replay_digest=str(attestation["replay_digest"]),
        record_key=key,
        manifest_path=str(manifest_path.relative_to(registry_root)),
        artifact_dir=str(artifact_dir.relative_to(registry_root)),
        output_digest=replay_result.output_digest,
        boundary=str(claim.get("boundary", attestation.get("boundary", ""))),
    )
    index = _load_index(registry_root)
    records = [
        entry for entry in index.get("records", []) if entry.get("record_key") != key
    ]
    records.append(record.to_dict())
    index["records"] = sorted(
        records, key=lambda entry: (entry["claim_id"], entry["input_digest"])
    )
    _write_index(registry_root, index)
    return record


def list_claims(
    registry_dir: str | Path, filter_by_boundary: str | None = None
) -> list[RegistryRecord]:
    """List registry records, optionally filtering by boundary substring."""

    needle = (filter_by_boundary or "").lower()
    records = [
        RegistryRecord(**entry)
        for entry in _load_index(Path(registry_dir)).get("records", [])
    ]
    if needle:
        records = [record for record in records if needle in record.boundary.lower()]
    return records


def load_manifest(registry_dir: str | Path, claim_id: str) -> dict[str, Any]:
    """Load the first registry manifest matching a claim id."""

    matches = [
        record for record in list_claims(registry_dir) if record.claim_id == claim_id
    ]
    if not matches:
        raise KeyError(f"claim id not found in registry: {claim_id}")
    registry_root = Path(registry_dir)
    return json.loads(
        (registry_root / matches[0].manifest_path).read_text(encoding="utf-8")
    )


def load_and_reverify(registry_dir: str | Path, claim_id: str) -> ReverificationResult:
    """Load a registered manifest and re-run replay from stored artifacts dir."""

    records = [
        record for record in list_claims(registry_dir) if record.claim_id == claim_id
    ]
    if not records:
        raise KeyError(f"claim id not found in registry: {claim_id}")
    record = records[0]
    registry_root = Path(registry_dir)
    manifest = json.loads(
        (registry_root / record.manifest_path).read_text(encoding="utf-8")
    )
    claim = _claim_from_manifest(manifest)
    replay = execute_reproducibility_replay(
        claim["reproducibility_attestation"], cwd=registry_root / record.artifact_dir
    )
    return ReverificationResult(record=record, replay=replay)


__all__ = [
    "RegistryRecord",
    "ReverificationResult",
    "list_claims",
    "load_and_reverify",
    "load_manifest",
    "save_verified_manifest",
]
