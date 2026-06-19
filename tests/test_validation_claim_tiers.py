from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_validation_claim_tier_guard_cli_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_validation_claim_tiers.py"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "validation-claim-tier guard passed" in result.stdout


def test_mining_manifest_keeps_standalone_status_honest() -> None:
    manifest = json.loads(
        (ROOT / "docs" / "mining" / "evidence" / "mining_validation_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["current_repository_state"] == "entangled_with_hyba_fullstack"
    assert manifest["standalone_repository"] is False
    assert manifest["independent_ci"] is False
    claim = manifest["claims"][0]
    assert claim["tier"] == "HYPOTHETICAL"
    assert claim["evidence_status"] == "real_double_sha256_loop_pending"
    boundaries = "\n".join(claim["boundaries"]).lower()
    assert "no guaranteed mining revenue claim" in boundaries
    assert "no antminer s21 superiority claim" in boundaries
