#!/usr/bin/env python3
"""Validate commercial stage gates against the mining evidence manifest."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GATES_PATH = ROOT / "docs" / "mining" / "commercialization_gates.json"
MANIFEST_PATH = (
    ROOT / "docs" / "mining" / "evidence" / "mining_validation_manifest.json"
)
REQUIRED_GATES = {
    "public_performance_claims",
    "firmware_licensing",
    "pool_integration",
    "sovereign_mining",
}
REQUIRED_OVERRIDE_TOKENS = {
    "written_ceo_approval",
    "board_vote_record",
    "evidence_manifest_update",
    "counterparty_written_notice_of_current_tier",
    "post_call_followup_email_confirming_tier",
}


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssertionError(f"{path}: invalid JSON") from exc


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_stage_definitions(gates: dict[str, Any]) -> None:
    stages = gates.get("stage_definitions", [])
    _require(
        isinstance(stages, list) and len(stages) == 4,
        "commercial gates must define exactly four stages 0-3",
    )
    stage_numbers = {stage.get("stage") for stage in stages}
    _require(
        stage_numbers == {0, 1, 2, 3},
        f"stage definitions must be 0,1,2,3, got {sorted(stage_numbers)}",
    )
    for stage in stages:
        for key in [
            "name",
            "claim_tier",
            "allowed_external_claim",
            "commercial_rights",
            "entry_requirements",
            "revenue_unlocks",
        ]:
            _require(key in stage, f"stage {stage.get('stage')}: missing {key}")
        if stage["stage"] < 2:
            _require(
                not stage.get("revenue_unlocks"),
                f"stage {stage['stage']}: revenue must remain locked",
            )


def validate_current_stage(gates: dict[str, Any], manifest: dict[str, Any]) -> None:
    current_stage = gates.get("current_stage")
    _require(
        current_stage == 0,
        f"current_stage must remain 0 while mining is pre-validation, got {current_stage}",
    )
    _require(
        gates.get("current_stage_name") == "stage_0_pre_validation_research_only",
        "current stage name must be stage 0",
    )
    _require(
        manifest.get("current_repository_state") == "entangled_with_hyba_fullstack",
        "manifest must disclose entangled repo state",
    )
    _require(
        manifest.get("standalone_repository") is False,
        "standalone_repository must be false until extraction is complete",
    )
    _require(
        manifest.get("independent_ci") is False,
        "independent_ci must be false until standalone CI exists",
    )
    _require(
        manifest.get("commercialization_stage") == gates.get("current_stage_name"),
        "manifest and gate stage names differ",
    )


def validate_commercial_gates(gates: dict[str, Any]) -> None:
    current_stage = int(gates.get("current_stage", -1))
    configured = gates.get("commercialization_gates", {})
    _require(
        REQUIRED_GATES <= set(configured),
        f"missing commercialization gates: {sorted(REQUIRED_GATES - set(configured))}",
    )
    for name, gate in configured.items():
        required_stage = int(gate.get("required_stage", -1))
        _require(required_stage > 0, f"{name}: required_stage must be positive")
        if current_stage < required_stage:
            _require(
                gate.get("status") == "BLOCKED",
                f"{name}: must be BLOCKED before required_stage",
            )
            _require(
                gate.get("approved_for_commercial_use") is False,
                f"{name}: must not be approved before required_stage",
            )
    firmware = configured["firmware_licensing"]
    _require(
        int(firmware.get("required_stage", 0)) >= 2,
        "firmware licensing cannot unlock before stage 2",
    )
    _require(
        int(firmware.get("min_valid_runs", 0)) >= 100,
        "firmware licensing requires at least 100 valid runs",
    )
    for name in ["pool_integration", "sovereign_mining"]:
        gate = configured[name]
        _require(
            int(gate.get("required_stage", 0)) >= 3,
            f"{name}: cannot unlock before stage 3",
        )
        _require(
            int(gate.get("min_field_trial_months", 0)) >= 6,
            f"{name}: requires at least six months field trial",
        )


def validate_override_policy(gates: dict[str, Any]) -> None:
    policy = gates.get("override_policy", {})
    _require(
        policy.get("overrides_allowed") is False,
        "commercial gate overrides must be disabled by default",
    )
    required = set(policy.get("if_exception_requested_requires", []))
    _require(
        REQUIRED_OVERRIDE_TOKENS <= required,
        f"override policy missing {sorted(REQUIRED_OVERRIDE_TOKENS - required)}",
    )
    escalations = " ".join(policy.get("automatic_escalation", [])).lower()
    for phrase in [
        "external_distribution",
        "hypothetical",
        "revenue",
        "hashrate",
        "asic",
    ]:
        _require(
            phrase in escalations, f"override policy escalation missing {phrase!r}"
        )


def validate_manifest_claims(manifest: dict[str, Any]) -> None:
    claims = manifest.get("claims", [])
    _require(claims, "mining manifest must contain at least one claim")
    for claim in claims:
        _require(
            claim.get("tier") == "HYPOTHETICAL",
            f"claim {claim.get('id')}: must remain HYPOTHETICAL before validation",
        )
        required_text = json.dumps(claim).lower()
        for phrase in [
            "minimum_100_repeated_runs_with_variance",
            "pool_side_accepted_share_evidence",
            "no commercialization before stage 2",
            "no production sla",
        ]:
            _require(
                phrase in required_text, f"claim {claim.get('id')}: missing {phrase}"
            )


def main() -> int:
    try:
        gates = _load_json(GATES_PATH)
        manifest = _load_json(MANIFEST_PATH)
        _require(
            gates.get("schema") == "HYBA_MINING_COMMERCIALIZATION_GATES_V1",
            "invalid commercialization gate schema",
        )
        _require(
            gates.get("source_manifest")
            == "docs/mining/evidence/mining_validation_manifest.json",
            "source manifest mismatch",
        )
        validate_stage_definitions(gates)
        validate_current_stage(gates, manifest)
        validate_commercial_gates(gates)
        validate_override_policy(gates)
        validate_manifest_claims(manifest)
    except Exception as exc:  # noqa: BLE001 - CI should show a concise reason
        print(f"commercialization gate failed: {exc}", file=sys.stderr)
        return 1
    print("commercialization gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
