#!/usr/bin/env python3
"""Simulate a Sukuk lifecycle drift sequence and emit evidence packets.

The simulation is product-demo infrastructure only. It creates deterministic
review candidates across lifecycle stages, generates sealed evidence packets,
and writes a summary index for human SSSB/compliance review. It never approves,
issues, books, trades, files, or submits anything.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, List

from pythia_finance_audit import (
    DIFCSukukCandidate,
    generate_difc_sukuk_audit_packet,
    sample_difc_sukuk_candidate,
)


STAGES = [
    {
        "name": "pre_issuance",
        "asset_backing_ratio": 0.88,
        "risk_sharing_score": 0.70,
        "spv_independence_score": 0.80,
        "economic_substance_score": 0.92,
        "form_alignment_score": 0.93,
        "uncertainty_score": 0.20,
        "trustee_oversight_present": True,
        "notes": "Initial structure has adequate asset evidence, trustee oversight, and SSSB escalation.",
    },
    {
        "name": "post_issuance_continuity",
        "asset_backing_ratio": 0.84,
        "risk_sharing_score": 0.63,
        "spv_independence_score": 0.76,
        "economic_substance_score": 0.88,
        "form_alignment_score": 0.93,
        "uncertainty_score": 0.27,
        "trustee_oversight_present": True,
        "notes": "Ongoing management remains reviewable but shows narrowing economic headroom.",
    },
    {
        "name": "market_stress_restructure_review",
        "asset_backing_ratio": 0.77,
        "risk_sharing_score": 0.54,
        "spv_independence_score": 0.69,
        "economic_substance_score": 0.83,
        "form_alignment_score": 0.95,
        "uncertainty_score": 0.38,
        "trustee_oversight_present": True,
        "notes": "Stress event introduces asset-backing weakness, debt-mimicry warning, and uncertainty drift.",
    },
    {
        "name": "termination_or_liquidation_review",
        "asset_backing_ratio": 0.71,
        "risk_sharing_score": 0.48,
        "spv_independence_score": 0.62,
        "economic_substance_score": 0.79,
        "form_alignment_score": 0.96,
        "uncertainty_score": 0.44,
        "trustee_oversight_present": False,
        "notes": "Termination path requires hard human escalation due to weak asset backing and trustee/SPV evidence.",
    },
]


def _candidate_for_stage(
    base: DIFCSukukCandidate, idx: int, stage: Dict[str, Any]
) -> DIFCSukukCandidate:
    return replace(
        base,
        candidate_id=f"DIFC-SUKUK-LIFECYCLE-{idx:03d}",
        lifecycle_stage=stage["name"],
        asset_backing_ratio=stage["asset_backing_ratio"],
        risk_sharing_score=stage["risk_sharing_score"],
        spv_independence_score=stage["spv_independence_score"],
        economic_substance_score=stage["economic_substance_score"],
        form_alignment_score=stage["form_alignment_score"],
        uncertainty_score=stage["uncertainty_score"],
        trustee_oversight_present=stage["trustee_oversight_present"],
        notes=stage["notes"],
    )


def _finding_counts(packet: Dict[str, Any]) -> Dict[str, int]:
    counts = {"passed": 0, "warning": 0, "failed": 0}
    for finding in packet.get("difc_aaiofi_findings", []):
        status = str(finding.get("status", "")).lower()
        if status in counts:
            counts[status] += 1
    return counts


def _summary_row(packet_path: Path, packet: Dict[str, Any]) -> Dict[str, Any]:
    candidate = packet["candidate"]
    counts = _finding_counts(packet)
    return {
        "packet_path": str(packet_path),
        "packet_hash": packet.get("difc_aaiofi_packet_hash"),
        "candidate_id": candidate.get("candidate_id"),
        "lifecycle_stage": candidate.get("lifecycle_stage"),
        "verdict": packet.get("verdict"),
        "human_review_required": packet.get("human_review_required"),
        "automatic_action_allowed": packet.get("automatic_action_allowed"),
        "passed_findings": counts["passed"],
        "warning_findings": counts["warning"],
        "failed_findings": counts["failed"],
        "asset_backing_ratio": candidate.get("asset_backing_ratio"),
        "risk_sharing_score": candidate.get("risk_sharing_score"),
        "spv_independence_score": candidate.get("spv_independence_score"),
        "uncertainty_score": candidate.get("uncertainty_score"),
    }


def simulate(output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    base = sample_difc_sukuk_candidate()
    rows: List[Dict[str, Any]] = []
    for idx, stage in enumerate(STAGES, start=1):
        candidate = _candidate_for_stage(base, idx, stage)
        packet = generate_difc_sukuk_audit_packet(candidate)
        packet_path = output_dir / f"{idx:02d}_{stage['name']}.json"
        packet_path.write_text(json.dumps(packet, indent=2, sort_keys=True), encoding="utf-8")
        rows.append(_summary_row(packet_path, packet))

    manifest = {
        "schema": "PYTHIA_DIFC_AAOIFI_SUKUK_LIFECYCLE_SIMULATION_V1",
        "boundary": (
            "Simulation evidence only. Not a fatwa, legal opinion, regulatory determination, issuance approval, "
            "trade instruction, booking instruction, external filing, or automated approval."
        ),
        "stage_count": len(rows),
        "human_review_required": True,
        "automatic_action_allowed": False,
        "rows": rows,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a deterministic DIFC/AAOIFI Sukuk lifecycle drift simulation."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/difc_audit/lifecycle"),
        help="Directory for lifecycle packets and manifest.json.",
    )
    args = parser.parse_args()
    manifest = simulate(args.output_dir)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
