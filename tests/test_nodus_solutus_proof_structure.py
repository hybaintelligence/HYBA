from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "NODUS_SOLUTUS_MUNDUS_COMPUTABILIS_EST.md"
MANIFEST = ROOT / "docs" / "evidence" / "claim_evidence_manifest.json"
PROOF_INDEX = ROOT / "docs" / "evidence" / "EXTRAORDINARY_PROOF_INDEX.md"
REVIEWER_MAP = ROOT / "REVIEWER_EVIDENCE_MAP.md"
LOCAL_GATE = ROOT / "scripts" / "local_production_gate.py"
PACKAGE_JSON = ROOT / "package.json"

CLAIM_ID = "nodus_solutus_repository_local_computability"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _manifest_claim() -> dict[str, object]:
    manifest = json.loads(_text(MANIFEST))
    for claim in manifest["claims"]:
        if claim["id"] == CLAIM_ID:
            return claim
    raise AssertionError(f"{CLAIM_ID} is missing from the claim evidence manifest")


def test_nodus_solutus_document_states_bounded_computability_doctrine() -> None:
    doc = _text(DOC).lower()

    assert "repository-local computability doctrine" in doc
    assert "deterministic source paths" in doc
    assert "executable tests" in doc
    assert "replayable local evidence packets" in doc
    assert "external truth boundaries" in doc
    assert "not" in doc and "metaphysical proof" in doc
    assert "physical universe" in doc
    assert "reviewer rejection rule" in doc


def test_nodus_solutus_document_keeps_holonomic_coherence_bounded() -> None:
    doc = _text(DOC)

    assert "Evidence of Holonomic Coherence" in doc
    assert "topological_holonomy_engine.py" in doc
    assert "geometric phase `0.554 rad`" in doc
    assert "gauge phase `π`" in doc
    assert "only after the corresponding run artifact is committed or archived" in doc
    assert "inadmissible statement" in doc
    assert "universal physical topological phase transition" in doc


def test_nodus_solutus_manifest_entry_is_executable_and_bounded() -> None:
    claim = _manifest_claim()

    assert claim["status"] == "implemented_and_executable"
    assert "repository-local computability doctrine" in claim["claim"]
    assert "not a metaphysical proof" in claim["boundary"]
    assert "physical universe" in claim["boundary"]
    assert "npm run review:nodus:gate" in claim["commands"]
    assert "npm run test:frontier:experiments" in claim["commands"]
    assert (
        "python_backend/pythia_mining/topological_holonomy_engine.py"
        in claim["code_paths"]
    )
    assert "docs/SCIENTIFIC_PUBLICATION_NODUS_SOLUTUS.md" in claim["doc_paths"]
    assert "docs/PRESS_RELEASE_NODUS_SOLUTUS.md" in claim["doc_paths"]

    for key in ("code_paths", "test_paths", "doc_paths"):
        for rel_path in claim[key]:
            assert (
                ROOT / rel_path
            ).exists(), f"{CLAIM_ID} references missing {key}: {rel_path}"


def test_nodus_solutus_is_visible_from_reviewer_entrypoints() -> None:
    proof_index = _text(PROOF_INDEX)
    reviewer_map = _text(REVIEWER_MAP)

    assert "Nodus Solutus" in proof_index
    assert "Mundus Computabilis Est" in proof_index
    assert "docs/NODUS_SOLUTUS_MUNDUS_COMPUTABILIS_EST.md" in proof_index
    assert "Nodus Solutus" in reviewer_map
    assert "docs/NODUS_SOLUTUS_MUNDUS_COMPUTABILIS_EST.md" in reviewer_map


def test_nodus_solutus_is_part_of_local_release_authority() -> None:
    local_gate = _text(LOCAL_GATE)
    package_json = json.loads(_text(PACKAGE_JSON))
    scripts = package_json["scripts"]

    assert "nodus_solutus_computability_doctrine" in local_gate
    assert "nodus_solutus" in local_gate
    assert "repository_local_computability" in local_gate
    assert "physical universe" in local_gate
    assert "review:nodus:gate" in scripts
    assert "test_nodus_solutus_proof_structure.py" in scripts["review:nodus:gate"]
    assert "npm run review:nodus:gate" in scripts["review:evidence:gate"]
    assert "review:manifest:gate" in scripts
