from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "evidence" / "claim_evidence_manifest.json"


def test_claim_evidence_manifest_is_complete_and_points_to_existing_files() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert manifest["schema"] == "HYBA_CLAIM_EVIDENCE_MANIFEST_V1"
    assert manifest["claims"], "manifest must contain reviewer-visible claim entries"

    claim_ids = set()
    for claim in manifest["claims"]:
        claim_ids.add(claim["id"])
        assert claim["claim"].strip()
        assert claim["status"] in {"implemented_and_executable", "implemented_and_documented"}
        assert claim["boundary"].strip(), f"{claim['id']} lacks an explicit boundary"
        assert claim["commands"], f"{claim['id']} lacks reproduction commands"

        for key in ("code_paths", "test_paths", "doc_paths"):
            assert claim[key], f"{claim['id']} lacks {key}"
            for rel_path in claim[key]:
                path = ROOT / rel_path
                assert path.exists(), f"{claim['id']} references missing {key}: {rel_path}"

    assert len(claim_ids) == len(manifest["claims"]), "claim ids must be unique"


def test_claim_manifest_keeps_extraordinary_claim_boundaries_explicit() -> None:
    manifest_text = MANIFEST.read_text(encoding="utf-8").lower()
    boundary_phrases = [
        "guaranteed mining revenue",
        "sha-256 quantum acceleration",
        "phenomenal consciousness",
        "proof of the yang-mills millennium problem",
    ]
    for phrase in boundary_phrases:
        assert phrase in manifest_text, f"boundary phrase missing from manifest: {phrase}"
