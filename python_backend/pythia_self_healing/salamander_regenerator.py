"""Sovereign proposal generator for code-level Salamander regeneration.

This is intentionally a proposal engine, not an auto-patcher. It produces
sealed packets containing candidate code, diff, invariant notes, risk flags, and
human-approval action. The reactor can combine it with optimisation, discovery,
rewiring, and memory modules to stage multiple alternatives.
"""

from __future__ import annotations

import difflib
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal


ProposalKind = Literal["conservative", "optimised", "algorithmic", "rewiring"]


@dataclass(frozen=True)
class RegenerationCandidate:
    target_name: str
    original_code: str
    improvement_goal: str
    context: Dict[str, Any] = field(default_factory=dict)
    candidate_kind: ProposalKind = "conservative"
    proposed_code: str | None = None


@dataclass
class SalamanderRegenerator:
    """Generate sealed, auditable regeneration proposal packets."""

    max_limb_size: int = 120
    stable_core_markers: tuple[str, ...] = (
        "STABLE_CORE",
        "DO_NOT_MODIFY",
        "SOVEREIGN_GATE",
        "HUMAN_APPROVAL_REQUIRED",
    )

    def _run_criticism_and_guard(self, candidate: RegenerationCandidate) -> Dict[str, Any]:
        """Criticise, guard, diff, and seal a candidate.

        The method name is preserved because the supplied ``SelfHealingReactor``
        delegates to this exact private hook. The hook remains side-effect free.
        """

        original_lines = candidate.original_code.splitlines()
        proposed_code = candidate.proposed_code or self._default_proposal(candidate)
        proposed_lines = proposed_code.splitlines()
        issues = self._criticise(candidate, proposed_code)
        approved_for_staging = not any(issue["severity"] == "critical" for issue in issues)
        diff = "\n".join(
            difflib.unified_diff(
                original_lines,
                proposed_lines,
                fromfile=f"original/{candidate.target_name}",
                tofile=f"proposal/{candidate.target_name}",
                lineterm="",
            )
        )

        payload = {
            "target": candidate.target_name,
            "candidate_kind": candidate.candidate_kind,
            "improvement_goal": candidate.improvement_goal,
            "context": candidate.context,
            "original_hash": self._hash(candidate.original_code),
            "proposed_hash": self._hash(proposed_code),
            "diff_hash": self._hash(diff),
            "issues": issues,
            "small_limb_compliant": len(original_lines) <= self.max_limb_size and len(proposed_lines) <= self.max_limb_size,
            "stable_core_safe": not self._touches_stable_core(candidate.original_code),
        }
        packet_id = f"SALAMANDER-SHR-{self._hash(payload)[:16]}"
        return {
            "packet_id": packet_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "SALAMANDER_REGENERATION_PROPOSAL",
            "target": candidate.target_name,
            "candidate_kind": candidate.candidate_kind,
            "status": "STAGED" if approved_for_staging else "REJECTED",
            "action": "ESCALATE_TO_SOVEREIGN_HUMAN" if approved_for_staging else "NO_CHANGE_APPLIED",
            "improvement_goal": candidate.improvement_goal,
            "original_hash": payload["original_hash"],
            "proposed_hash": payload["proposed_hash"],
            "diff_hash": payload["diff_hash"],
            "unified_diff": diff,
            "proposed_code": proposed_code,
            "criticisms": issues,
            "guards": {
                "small_limb_rule": payload["small_limb_compliant"],
                "stable_core_safe": payload["stable_core_safe"],
                "human_sovereign_required": True,
                "auto_apply": False,
            },
            "seal": self._hash(payload),
        }

    def _default_proposal(self, candidate: RegenerationCandidate) -> str:
        """Create a conservative documentation-only proposal skeleton."""

        marker = "# Salamander healing note: " + candidate.improvement_goal
        lines = candidate.original_code.splitlines()
        if any("Salamander healing note" in line for line in lines):
            return candidate.original_code
        if not lines:
            return marker
        insert_at = 1 if lines[0].lstrip().startswith(("def ", "async def ", "class ")) else 0
        return "\n".join(lines[:insert_at] + [marker] + lines[insert_at:])

    def _criticise(self, candidate: RegenerationCandidate, proposed_code: str) -> List[Dict[str, str]]:
        issues: List[Dict[str, str]] = []
        original_lines = candidate.original_code.splitlines()
        proposed_lines = proposed_code.splitlines()
        if len(original_lines) > self.max_limb_size:
            issues.append({"severity": "critical", "issue": "original target violates small-limb rule"})
        if len(proposed_lines) > self.max_limb_size:
            issues.append({"severity": "critical", "issue": "proposal violates small-limb rule"})
        if self._touches_stable_core(candidate.original_code):
            issues.append({"severity": "critical", "issue": "target contains Stable Core marker"})
        if "AUTO_APPLY" in proposed_code or "apply_without_approval" in proposed_code:
            issues.append({"severity": "critical", "issue": "proposal attempts to bypass human sovereign approval"})
        if not issues:
            issues.append({"severity": "info", "issue": "proposal is staged only; sovereign approval remains mandatory"})
        return issues

    def _touches_stable_core(self, code: str) -> bool:
        return any(marker in code for marker in self.stable_core_markers)

    @staticmethod
    def _hash(value: Any) -> str:
        if isinstance(value, str):
            data = value
        else:
            data = json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(data.encode("utf-8")).hexdigest()
