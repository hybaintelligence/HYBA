from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run_script(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, script],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


def _load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _template_frontmatter() -> str:
    text = (ROOT / "docs" / "templates" / "external_claim_material.md").read_text(
        encoding="utf-8"
    )
    assert text.startswith("---\n")
    end = text.find("\n---\n", 4)
    assert end > 0
    return text[4:end]


def test_validation_claim_tier_guard_cli_passes() -> None:
    result = _run_script("scripts/check_validation_claim_tiers.py")
    assert result.returncode == 0, result.stderr
    assert "validation-claim-tier guard passed" in result.stdout


def test_commercialization_gate_cli_passes() -> None:
    result = _run_script("scripts/check_commercialization_gates.py")
    assert result.returncode == 0, result.stderr
    assert "commercialization gate passed" in result.stdout


def test_external_claim_template_has_distribution_controls() -> None:
    frontmatter = _template_frontmatter()
    for key in [
        "channel:",
        "review_status:",
        "approved_by:",
        "external_distribution:",
        "distribution_boundary:",
    ]:
        assert key in frontmatter
    assert "external_distribution: false" in frontmatter


def test_mining_manifest_keeps_standalone_status_honest() -> None:
    manifest = _load_json("docs/mining/evidence/mining_validation_manifest.json")
    assert manifest["current_repository_state"] == "entangled_with_hyba_fullstack"
    assert manifest["standalone_repository"] is False
    assert manifest["independent_ci"] is False
    assert manifest["commercialization_stage"] == "stage_0_pre_validation_research_only"
    claim = manifest["claims"][0]
    assert claim["tier"] == "HYPOTHETICAL"
    assert claim["evidence_status"] == "benchmarks_passed_numpy_unblocked"
    boundaries = "\n".join(claim["boundaries"]).lower()
    assert "no guaranteed mining revenue claim" in boundaries
    assert "no antminer s21 superiority claim" in boundaries
    assert "no commercialization before stage 2" in boundaries
    assert "no production sla" in boundaries


def test_commercialization_gates_lock_premature_revenue() -> None:
    gates = _load_json("docs/mining/commercialization_gates.json")
    assert gates["schema"] == "HYBA_MINING_COMMERCIALIZATION_GATES_V1"
    assert gates["current_stage"] == 0
    configured = gates["commercialization_gates"]
    assert configured["firmware_licensing"]["required_stage"] == 2
    assert configured["firmware_licensing"]["min_valid_runs"] >= 100
    assert configured["pool_integration"]["required_stage"] == 3
    assert configured["pool_integration"]["min_field_trial_months"] >= 6
    assert configured["sovereign_mining"]["required_stage"] == 3
    for gate in configured.values():
        assert gate["status"] == "BLOCKED"
        assert gate["approved_for_commercial_use"] is False


def test_override_policy_requires_written_counterparty_notice() -> None:
    gates = _load_json("docs/mining/commercialization_gates.json")
    policy = gates["override_policy"]
    assert policy["overrides_allowed"] is False
    required = set(policy["if_exception_requested_requires"])
    assert "written_ceo_approval" in required
    assert "board_vote_record" in required
    assert "counterparty_written_notice_of_current_tier" in required
    assert "post_call_followup_email_confirming_tier" in required
