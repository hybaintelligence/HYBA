"""Sovereign-gated Self-Healing Reactor for Salamander codebase repair.

The lane-level Salamander system owns the regeneration mathematics. This module
owns the codebase-level reactor: it converts damage reports into sealed repair
proposals, wraps them in the governance envelope required by the autonomic
substrate protocol, and never applies source changes without a human approval
event.
"""

from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .autonomous_damage_detector import DamageReport
from .salamander_regenerator import RegenerationCandidate, SalamanderRegenerator


class SelfHealingReactor:
    """Turn damage reports into sovereign-sealed Salamander repair proposals.

    Contract:
    - enforce the Salamander small-limb rule;
    - preserve the human sovereign gate;
    - expose observe→diagnose→heal→optimise→rewire→evolve→benchmark fields;
    - stage proposals only; never auto-apply patches.
    """

    def __init__(self, regenerator: SalamanderRegenerator, max_limb_size: int = 120):
        self.regenerator = regenerator
        self.max_limb_size = max_limb_size

    def heal_damage(
        self,
        damage_report: DamageReport | Dict[str, Any],
        module_path: str,
        target_name: str,
    ) -> Dict[str, Any]:
        """Convert a damage report into a sealed healing proposal."""

        report = DamageReport(dict(damage_report))
        if not report.get("needs_repair", False):
            return {
                "status": "NO_HEALING_NEEDED",
                "damage_report": report,
                "packet": None,
                "action": "NO_CHANGE_APPLIED",
                "sovereign_human_gate": True,
                "small_limb_rule_enforced": False,
                "governance_envelope": self._governance_envelope(report, None),
            }

        target_code_or_error = self._load_target_code(module_path, target_name)
        if isinstance(target_code_or_error, dict):
            return target_code_or_error
        target_code = target_code_or_error
        target_lines = len(target_code.splitlines())

        if target_lines > self.max_limb_size:
            return self._create_error_packet(
                report,
                target_name,
                f"Target too large ({target_lines} lines). Violates Salamander small-limb rule.",
            )

        improvement_goal = self._build_improvement_goal(report)
        candidate = RegenerationCandidate(
            target_name=target_name,
            original_code=target_code,
            improvement_goal=improvement_goal,
            context={
                "module_path": module_path,
                "damage_report": dict(report),
                "healing_type": "self_healing",
                "protocol_step": "heal",
            },
        )
        packet = self.regenerator._run_criticism_and_guard(candidate)
        action = "ESCALATE_TO_REWIRING_ORCHESTRATOR" if self._requires_rewiring(report) else "ESCALATE_TO_SOVEREIGN_HUMAN"

        return {
            "status": "HEALING_PROPOSAL_STAGED",
            "damage_report": report,
            "target": target_name,
            "packet": packet,
            "action": action,
            "sovereign_human_gate": True,
            "small_limb_rule_enforced": target_lines <= self.max_limb_size,
            "governance_envelope": self._governance_envelope(report, packet),
            "auto_apply": False,
        }

    def optimise_hot_path(
        self,
        damage_report: DamageReport | Dict[str, Any],
        module_path: str,
        target_name: str,
    ) -> Dict[str, Any]:
        """Stage a performance/latency/φ-stability repair proposal.

        This is the protocol-level optimise step. It reuses the same Salamander
        guard pipeline and remains sovereign-human gated.
        """

        report = DamageReport(dict(damage_report))
        issues = list(report.get("issues", []))
        issues.append("hot path optimisation requested: preserve latency, performance and φ-stability invariants")
        report["issues"] = issues
        report.setdefault("protocol_step", "optimise")
        report.setdefault("architecture_impact", "LOCAL_LIMB")
        staged = self.heal_damage(report, module_path, target_name)
        staged["status"] = "OPTIMISATION_PROPOSAL_STAGED" if staged.get("packet") else staged["status"]
        staged["protocol_step"] = "optimise"
        return staged

    def _load_target_code(self, module_path: str, target_name: str) -> str | Dict[str, Any]:
        try:
            full_code = Path(module_path).read_text(encoding="utf-8")
        except Exception as exc:  # pragma: no cover - exercised through error packet tests
            return self._create_error_packet(DamageReport({"needs_repair": True}), target_name, f"Failed to read code: {exc}")

        target_code = self._extract_target_code(full_code, target_name)
        if not target_code:
            return self._create_error_packet(DamageReport({"needs_repair": True}), target_name, "Target code not found")
        return target_code

    def _extract_target_code(self, full_code: str, target_name: str) -> Optional[str]:
        """Extract a function/class by name using AST line spans."""

        try:
            tree = ast.parse(full_code)
        except SyntaxError:
            return None
        lines = full_code.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == target_name:
                start = int(node.lineno) - 1
                end = int(getattr(node, "end_lineno", node.lineno))
                return "\n".join(lines[start:end])
        return None

    def _build_improvement_goal(self, damage_report: DamageReport | Dict[str, Any]) -> str:
        """Convert damage signals into an actionable healing goal."""

        issues = [str(issue) for issue in damage_report.get("issues", [])]
        lowered = " | ".join(issues).lower()
        suggested_goal = damage_report.get("suggested_goal")
        if suggested_goal:
            return str(suggested_goal)
        if "φ" in lowered or "phi" in lowered or "floor" in lowered:
            return "Restore φ-geometry alignment, φ-floor coherence and invariant-safe execution"
        if "fidelity" in lowered or "scarring" in lowered or "quarantine" in lowered or "redifferent" in lowered:
            return "Repair regeneration stability, reduce scarring risk and preserve Salamander fidelity invariants"
        if "performance" in lowered or "latency" in lowered or "hot path" in lowered:
            return "Repair hot-path performance regression while preserving φ-stability and all invariants"
        if "rewire" in lowered or "structural" in lowered or "architecture" in lowered or "dependency" in lowered:
            return "Escalate structural brittleness to rewiring while preserving local limb safety"
        if "todo" in lowered or "fixme" in lowered or "technical debt" in lowered:
            return "Resolve technical debt, restore invariants and remove TODO/FIXME drift"
        if "invariant" in lowered:
            return "Restore invariant compliance and add protection"
        return "Repair detected drift and strengthen resilience"

    @staticmethod
    def _requires_rewiring(damage_report: DamageReport | Dict[str, Any]) -> bool:
        lowered = " | ".join(str(issue) for issue in damage_report.get("issues", [])).lower()
        return any(token in lowered for token in ("rewire", "structural", "architecture", "dependency graph", "circular import"))

    def _governance_envelope(
        self,
        damage_report: DamageReport | Dict[str, Any],
        packet: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return {
            "lane_id": damage_report.get("lane_id"),
            "blastema_state": damage_report.get("blastema_state"),
            "progenitor_state": damage_report.get("progenitor_state"),
            "before_metrics": damage_report.get("metrics_before"),
            "after_metrics_expected": damage_report.get("metrics_target"),
            "reasoning_trace": (packet or {}).get("criticisms") or (packet or {}).get("criticism_trail"),
            "performance_impact": damage_report.get("performance_impact"),
            "stability_impact": damage_report.get("stability_impact"),
            "architecture_impact": damage_report.get("architecture_impact", "LOCAL_LIMB"),
            "protocol_steps": ["observe", "diagnose", "heal", "optimise", "rewire", "evolve", "benchmark"],
            "human_sovereign_required": True,
            "auto_apply": False,
        }

    def _create_error_packet(
        self,
        damage_report: DamageReport | Dict[str, Any],
        target_name: str,
        reason: str,
    ) -> Dict[str, Any]:
        packet = {
            "packet_id": f"SHR-ERROR-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "HEALING_FAILURE",
            "target": target_name,
            "status": "REJECTED",
            "reason": reason,
            "damage_report": dict(damage_report),
            "action": "NO_CHANGE_APPLIED",
        }
        return {
            "status": "HEALING_REJECTED",
            "damage_report": DamageReport(dict(damage_report)),
            "target": target_name,
            "packet": packet,
            "action": "NO_CHANGE_APPLIED",
            "sovereign_human_gate": True,
            "small_limb_rule_enforced": False,
            "governance_envelope": self._governance_envelope(DamageReport(dict(damage_report)), packet),
            "auto_apply": False,
        }


def create_healing_proposal(module_path: str, target_name: str, damage_issues: list[str] | None = None) -> Dict[str, Any]:
    """Manual development helper for staging a sovereign healing proposal."""

    regenerator = SalamanderRegenerator()
    reactor = SelfHealingReactor(regenerator)
    damage_report = DamageReport(
        {
            "needs_repair": True,
            "issues": damage_issues or ["Detected drift / technical debt"],
            "suggested_goal": "Repair and strengthen",
        }
    )
    return reactor.heal_damage(damage_report, module_path, target_name)
