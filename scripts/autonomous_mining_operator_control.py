#!/usr/bin/env python3
"""PYTHIA Autonomous Mining Operator Control Interface.

This script provides operators with control over PYTHIA's autonomous mining capabilities,
including setting autonomy levels, approving/rejecting decisions, and monitoring autonomous
activity with full audit trails.

Usage:
    python scripts/autonomous_mining_operator_control.py --help
    python scripts/autonomous_mining_operator_control.py --status
    python scripts/autonomous_mining_operator_control.py --set-level AUTONOMOUS
    python scripts/autonomous_mining_operator_control.py --history
    python scripts/autonomous_mining_operator_control.py --approve <decision_id>
    python scripts/autonomous_mining_operator_control.py --reject <decision_id> <reason>
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Add python_backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python_backend'))

from pythia_mining.autonomous_mining_controller import (
    AutonomousConfig,
    AutonomousMiningController,
    AutonomyLevel,
    SafetyConstraint,
)
from pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine


class OperatorControlInterface:
    """Interface for operators to control PYTHIA's autonomous mining."""

    def __init__(self, engine: UnifiedMiningEngine):
        self.engine = engine
        self.controller = engine.autonomous_controller
        self.audit_log_path = Path("artifacts/autonomous_mining/operator_audit.log")
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

    def _log_audit_entry(self, entry: Dict[str, Any]) -> None:
        """Log operator action to audit file."""
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "operator_action": entry,
        }
        with open(self.audit_log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def get_status(self) -> Dict[str, Any]:
        """Get current autonomous mining status."""
        status = self.controller.get_autonomy_status()
        engine_state = self.engine.get_unified_state()
        
        return {
            "autonomy_level": status["autonomy_level"],
            "total_decisions": status["total_decisions"],
            "autonomous_decisions": status["autonomous_decisions"],
            "operator_overrides": status["operator_overrides"],
            "constraint_violations": status["constraint_violations"],
            "phi_coherence": engine_state["state"]["phi_coherence"],
            "integration_regime": engine_state["state"]["integration_regime"],
            "current_hashrate_ehs": engine_state["state"]["last_batch_hashrate_ehs"],
            "accepted_shares": engine_state["state"]["accepted_shares"],
            "rejected_shares": engine_state["state"]["rejected_shares"],
        }

    def set_autonomy_level(self, level: str, operator_reason: str) -> Dict[str, Any]:
        """Set autonomy level with audit logging."""
        try:
            autonomy_level = AutonomyLevel(level.lower())
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid autonomy level: {level}. Valid levels: {[l.value for l in AutonomyLevel]}",
            }

        previous_level = self.controller.current_autonomy_level
        self.controller.set_autonomy_level(autonomy_level)

        # Log audit entry
        self._log_audit_entry({
            "action": "set_autonomy_level",
            "previous_level": previous_level.value,
            "new_level": autonomy_level.value,
            "reason": operator_reason,
        })

        return {
            "success": True,
            "previous_level": previous_level.value,
            "new_level": autonomy_level.value,
            "reason": operator_reason,
        }

    def get_decision_history(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get history of autonomous decisions."""
        decisions = self.engine.get_autonomous_decision_history(limit=limit)
        
        return {
            "total_decisions": len(decisions),
            "decisions": decisions,
            "recent_summary": {
                "last_10_autonomous": sum(1 for d in decisions[-10:] if not d.get("operator_override")),
                "last_10_overridden": sum(1 for d in decisions[-10:] if d.get("operator_override")),
                "last_10_violations": sum(1 for d in decisions[-10:] if d.get("constraints_violated")),
            }
        }

    def approve_decision(self, decision_id: str, operator_reason: str) -> Dict[str, Any]:
        """Approve a pending autonomous decision."""
        # Find the decision in history
        decisions = self.controller.get_decision_history()
        target_decision = None
        for decision in decisions:
            if decision.decision_id == decision_id:
                target_decision = decision
                break
        
        if not target_decision:
            return {
                "success": False,
                "error": f"Decision {decision_id} not found in history",
            }

        # Log approval
        self._log_audit_entry({
            "action": "approve_decision",
            "decision_id": decision_id,
            "decision_type": target_decision.decision_type,
            "action_taken": target_decision.action_taken,
            "reason": operator_reason,
        })

        return {
            "success": True,
            "decision_id": decision_id,
            "decision_type": target_decision.decision_type,
            "action_taken": target_decision.action_taken,
            "reason": operator_reason,
        }

    def reject_decision(self, decision_id: str, operator_reason: str) -> Dict[str, Any]:
        """Reject a pending autonomous decision."""
        # Find the decision in history
        decisions = self.controller.get_decision_history()
        target_decision = None
        for decision in decisions:
            if decision.decision_id == decision_id:
                target_decision = decision
                break
        
        if not target_decision:
            return {
                "success": False,
                "error": f"Decision {decision_id} not found in history",
            }

        # Log rejection
        self._log_audit_entry({
            "action": "reject_decision",
            "decision_id": decision_id,
            "decision_type": target_decision.decision_type,
            "action_taken": target_decision.action_taken,
            "reason": operator_reason,
        })

        return {
            "success": True,
            "decision_id": decision_id,
            "decision_type": target_decision.decision_type,
            "action_taken": target_decision.action_taken,
            "reason": operator_reason,
        }

    def configure_safety_constraints(
        self,
        max_hashrate_ehs: Optional[float] = None,
        max_power_watts: Optional[float] = None,
        phi_coherence_threshold: Optional[float] = None,
        operator_reason: str = "configuration_update",
    ) -> Dict[str, Any]:
        """Configure safety constraints for autonomous operations."""
        config = self.controller.config
        
        changes = {}
        if max_hashrate_ehs is not None:
            changes["max_autonomous_hashrate_ehs"] = {
                "previous": config.max_autonomous_hashrate_ehs,
                "new": max_hashrate_ehs,
            }
            config.max_autonomous_hashrate_ehs = max_hashrate_ehs
        
        if max_power_watts is not None:
            changes["max_autonomous_power_watts"] = {
                "previous": config.max_autonomous_power_watts,
                "new": max_power_watts,
            }
            config.max_autonomous_power_watts = max_power_watts
        
        if phi_coherence_threshold is not None:
            changes["phi_coherence_threshold"] = {
                "previous": config.phi_coherence_threshold,
                "new": phi_coherence_threshold,
            }
            config.phi_coherence_threshold = phi_coherence_threshold

        # Log configuration change
        self._log_audit_entry({
            "action": "configure_safety_constraints",
            "changes": changes,
            "reason": operator_reason,
        })

        return {
            "success": True,
            "changes": changes,
            "reason": operator_reason,
        }

    async def trigger_autonomous_optimization(
        self,
        optimization_type: str,
        target_value: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Trigger an autonomous optimization cycle."""
        if optimization_type == "search_strategy":
            result = await self.engine.autonomous_optimize_search()
        elif optimization_type == "hashrate":
            if target_value is None:
                return {
                    "success": False,
                    "error": "target_value required for hashrate optimization",
                }
            result = await self.engine.autonomous_optimize_hashrate(target_value)
        else:
            return {
                "success": False,
                "error": f"Unknown optimization type: {optimization_type}",
            }

        # Log optimization trigger
        self._log_audit_entry({
            "action": "trigger_autonomous_optimization",
            "optimization_type": optimization_type,
            "target_value": target_value,
            "result": result,
        })

        return {
            "success": True,
            "optimization_type": optimization_type,
            "result": result,
        }

    def get_audit_log(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get operator audit log."""
        if not self.audit_log_path.exists():
            return {
                "total_entries": 0,
                "entries": [],
            }

        entries = []
        with open(self.audit_log_path, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue

        if limit:
            entries = entries[-limit:]

        return {
            "total_entries": len(entries),
            "entries": entries,
        }


def main():
    """Main entry point for operator control interface."""
    parser = argparse.ArgumentParser(
        description="PYTHIA Autonomous Mining Operator Control Interface"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Status command
    subparsers.add_parser("status", help="Get current autonomous mining status")

    # Set autonomy level command
    level_parser = subparsers.add_parser("set-level", help="Set autonomy level")
    level_parser.add_argument("level", help="Autonomy level (MANUAL, ADVISORY, SUPERVISED, AUTONOMOUS, EMERGENCY)")
    level_parser.add_argument("--reason", default="operator_directive", help="Reason for level change")

    # Decision history command
    history_parser = subparsers.add_parser("history", help="Get autonomous decision history")
    history_parser.add_argument("--limit", type=int, default=20, help="Number of decisions to show")

    # Approve decision command
    approve_parser = subparsers.add_parser("approve", help="Approve an autonomous decision")
    approve_parser.add_argument("decision_id", help="Decision ID to approve")
    approve_parser.add_argument("--reason", default="operator_approval", help="Reason for approval")

    # Reject decision command
    reject_parser = subparsers.add_parser("reject", help="Reject an autonomous decision")
    reject_parser.add_argument("decision_id", help="Decision ID to reject")
    reject_parser.add_argument("--reason", required=True, help="Reason for rejection")

    # Configure safety constraints command
    config_parser = subparsers.add_parser("configure", help="Configure safety constraints")
    config_parser.add_argument("--max-hashrate", type=float, help="Maximum autonomous hashrate (EH/s)")
    config_parser.add_argument("--max-power", type=float, help="Maximum power consumption (Watts)")
    config_parser.add_argument("--phi-threshold", type=float, help="Minimum phi coherence threshold")
    config_parser.add_argument("--reason", default="safety_configuration", help="Reason for configuration change")

    # Trigger optimization command
    opt_parser = subparsers.add_parser("optimize", help="Trigger autonomous optimization")
    opt_parser.add_argument("type", choices=["search_strategy", "hashrate"], help="Optimization type")
    opt_parser.add_argument("--target", type=float, help="Target value for optimization")

    # Audit log command
    audit_parser = subparsers.add_parser("audit", help="Get operator audit log")
    audit_parser.add_argument("--limit", type=int, default=50, help="Number of audit entries to show")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize unified engine
    engine = UnifiedMiningEngine(configured_capacity_ehs=100.0)
    interface = OperatorControlInterface(engine)

    # Execute command
    if args.command == "status":
        result = interface.get_status()
    elif args.command == "set-level":
        result = interface.set_autonomy_level(args.level, args.reason)
    elif args.command == "history":
        result = interface.get_decision_history(limit=args.limit)
    elif args.command == "approve":
        result = interface.approve_decision(args.decision_id, args.reason)
    elif args.command == "reject":
        result = interface.reject_decision(args.decision_id, args.reason)
    elif args.command == "configure":
        result = interface.configure_safety_constraints(
            max_hashrate_ehs=args.max_hashrate,
            max_power_watts=args.max_power,
            phi_coherence_threshold=args.phi_threshold,
            operator_reason=args.reason,
        )
    elif args.command == "optimize":
        result = asyncio.run(interface.trigger_autonomous_optimization(
            args.type,
            args.target,
        ))
    elif args.command == "audit":
        result = interface.get_audit_log(limit=args.limit)
    else:
        parser.print_help()
        return

    # Output result
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
