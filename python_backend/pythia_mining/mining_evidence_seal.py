"""Mining Evidence Sealing — Cryptographic Audit Trails for Autonomous Decisions.

This module provides evidence sealing for mining-specific events:
- Autonomous controller decisions
- Reflexive knowledge loop proposals
- Hardware scaling plans
- Share submission outcomes

All seals use SHA-256 and follow the same format as agentic intelligence
evidence seals, ensuring cross-system audit trail consistency.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def create_mining_evidence_seal(
    event_type: str,
    payload: Dict[str, Any],
    *,
    timestamp: Optional[str] = None,
    algorithm: str = "sha256",
) -> Dict[str, Any]:
    """Create a deterministic evidence seal for a mining event.

    Args:
        event_type: Type of mining event (e.g., "autonomous_decision", "scaling_plan")
        payload: Event-specific data to seal
        timestamp: ISO-8601 timestamp (defaults to now)
        algorithm: Hash algorithm (currently only sha256 supported)

    Returns:
        Evidence seal dict with body_hash, timestamp, algorithm, immutable_guard_active
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()

    canonical = json.dumps(
        {"event_type": event_type, "payload": payload},
        sort_keys=True,
        separators=(",", ":"),
    )
    body_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    return {
        "body_hash": body_hash,
        "timestamp": timestamp,
        "algorithm": algorithm,
        "immutable_guard_active": True,
        "event_type": event_type,
    }


def verify_mining_evidence_seal(
    event_type: str,
    payload: Dict[str, Any],
    seal: Dict[str, Any],
) -> bool:
    """Return True iff the seal still matches the event data."""
    expected = create_mining_evidence_seal(
        event_type,
        payload,
        timestamp=seal.get("timestamp"),
        algorithm=seal.get("algorithm", "sha256"),
    )
    return expected.get("body_hash") == seal.get("body_hash")


def seal_autonomous_decision(decision: Any) -> Dict[str, Any]:
    """Seal an AutonomousDecision dataclass instance."""
    return create_mining_evidence_seal(
        "autonomous_decision",
        {
            "decision_id": decision.decision_id,
            "timestamp": decision.timestamp,
            "autonomy_level": decision.autonomy_level.value,
            "decision_type": decision.decision_type,
            "action_taken": decision.action_taken,
            "expected_outcome": decision.expected_outcome,
            "constraints_satisfied": [c.value for c in decision.constraints_satisfied],
            "constraints_violated": [c.value for c in decision.constraints_violated],
            "operator_override": decision.operator_override,
        },
    )


def seal_reflexive_proposal(proposal: Any) -> Dict[str, Any]:
    """Seal a SelfOptimizationProposal dataclass instance."""
    return create_mining_evidence_seal(
        "reflexive_proposal",
        {
            "proposal_id": proposal.proposal_id,
            "timestamp": proposal.timestamp,
            "improvement_type": proposal.improvement_type,
            "current_value": proposal.current_value,
            "proposed_value": proposal.proposed_value,
            "expected_phi_density_gain": proposal.expected_phi_density_gain,
            "counterfactual_confidence": proposal.counterfactual_confidence,
            "constraints_satisfied": [c.value for c in proposal.constraints_satisfied],
            "constraints_violated": [c.value for c in proposal.constraints_violated],
            "applied": proposal.applied,
        },
    )


def seal_scaling_plan(plan: Any) -> Dict[str, Any]:
    """Seal a ScalingPlan dataclass instance."""
    return create_mining_evidence_seal(
        "scaling_plan",
        {
            "coherence_factor": plan.coherence_factor,
            "phi_density": plan.phi_density,
            "timestamp": plan.timestamp,
            "proposal_count": len(plan.proposals),
            "proposed_changes": [
                {
                    "dimension": p.dimension,
                    "from": p.current_value,
                    "to": p.proposed_value,
                    "fib_index": p.fibonacci_index,
                }
                for p in plan.proposals
            ],
        },
    )