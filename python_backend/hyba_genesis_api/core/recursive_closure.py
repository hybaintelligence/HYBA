"""Recursive closure bridge from reflection proposals to runtime parameters.

The closure is the production-safe binding layer: it can evolve in-memory runtime
parameters that a mining loop may read, but it never writes Python source files
or persistent configuration without an explicitly supplied external actuator.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Protocol

from hyba_genesis_api.core.constructor_engine import ExplainerIntegrity
from hyba_genesis_api.core.ontological_memory import CrystallineRegistry


@dataclass
class SubstrateBuffer:
    """In-memory learned-parameter registry for proposal-only evolution."""

    parameters: Dict[str, float] = field(default_factory=dict)
    audit_events: list[Dict[str, Any]] = field(default_factory=list)

    def update(self, key: str, adjustment: float, source: str) -> Dict[str, Any]:
        current = self.parameters.get(key, 0.0)
        new_value = current + float(adjustment)
        self.parameters[key] = new_value
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "key": key,
            "previous": round(current, 8),
            "adjustment": round(float(adjustment), 8),
            "value": round(new_value, 8),
            "source": source,
            "persistence": "in_memory_only",
        }
        self.audit_events.append(event)
        return event

    def snapshot(self) -> Dict[str, Any]:
        return {
            "parameters": dict(self.parameters),
            "audit_events": list(self.audit_events),
        }


class MiningParameterSink(Protocol):
    """Runtime sink expected by RecursiveClosure."""

    def update_parameters(self, adjustment: float) -> Dict[str, Any]:
        """Apply an in-memory adjustment and return an audit event."""


class BufferBackedMiningLoop:
    """Safe mining-loop adapter backed by SubstrateBuffer only."""

    def __init__(self, buffer: SubstrateBuffer, key: str = "entropy_threshold_delta"):
        self.buffer = buffer
        self.key = key

    def update_parameters(self, adjustment: float) -> Dict[str, Any]:
        return self.buffer.update(self.key, adjustment, "recursive_closure")


class RecursiveClosure:
    """Bridge ReflexiveController proposals into an in-memory substrate buffer."""

    PHI_ACCEPTANCE_FLOOR = 0.618

    def __init__(
        self,
        controller: Any,
        mining_loop: MiningParameterSink | CrystallineRegistry | None = None,
        registry: CrystallineRegistry | None = None,
    ):
        self.controller = controller
        if isinstance(mining_loop, CrystallineRegistry) and registry is None:
            registry = mining_loop
            mining_loop = None
        self.registry = registry or CrystallineRegistry()
        self._owned_buffer = SubstrateBuffer() if mining_loop is None else None
        self.mining_loop = mining_loop or BufferBackedMiningLoop(self._owned_buffer)
        self.integrity = ExplainerIntegrity()
        self.evolution_registry: Dict[str, Any] = {}

    def sync_learning(self) -> Dict[str, Any]:
        """Perform one governed dream cycle and maybe update runtime parameters."""

        reflection = self.controller.step()
        telemetry = reflection.get("telemetry", {})
        phi_resonance = float(
            telemetry.get("phi_resonance", telemetry.get("phi_density", 0.0))
        )
        proposal = reflection.get("proposal") or {}
        adjustment = float(
            proposal.get("adjustment", telemetry.get("proposed_mutation", 0.0))
        )
        codebase_hash = hashlib.sha256(
            repr(reflection.get("observation", {})).encode("utf-8")
        ).hexdigest()
        hard_to_vary = self.integrity.validate_explanation(
            {"adjustment": adjustment}, codebase_hash
        )
        accepted = (
            reflection.get("apply_mode") == "proposal_only"
            and reflection.get("governance") == "BOUNDED_BY_GEOMETRIC_INVARIANTS"
            and phi_resonance > self.PHI_ACCEPTANCE_FLOOR
            and adjustment >= 0.0
            and hard_to_vary
        )
        event = None
        memory_state = self.registry.load_best_reality()
        if accepted:
            event = self.mining_loop.update_parameters(adjustment)
            memory_state = self.registry.save_peak_state(
                phi_resonance,
                {"adjustment": adjustment, "event": event},
            )
        status = "EVOLVED" if accepted else "STAGNATED"
        result = {
            "status": status,
            "phi_resonance": round(phi_resonance, 6),
            "accepted": accepted,
            "hard_to_vary": hard_to_vary,
            "event": event,
            "ontological_memory": memory_state,
            "reflection": reflection,
            "claim_boundary": "in-memory runtime parameter evolution; no source writes",
        }
        self.evolution_registry["last_sync"] = result
        return result

    def snapshot(self) -> Dict[str, Any]:
        return dict(self.evolution_registry)


def build_buffered_closure(
    controller: Any, registry: CrystallineRegistry | None = None
) -> tuple[RecursiveClosure, SubstrateBuffer]:
    """Factory for a safe closure with an in-memory substrate buffer."""

    buffer = SubstrateBuffer()
    return (
        RecursiveClosure(controller, BufferBackedMiningLoop(buffer), registry),
        buffer,
    )
