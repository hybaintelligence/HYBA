"""Deterministic regeneration manager for the 32-lane PYTHIA manifold.

This module exposes the existing ``quantum_regeneration`` Hilbert-space role
model as an auditable lane manager. It deliberately reports only state it owns
or derives from the mathematical model; hardware cache residency is left as
``None`` unless a future runtime supplies measured evidence.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import fmean
from typing import Any, Dict, List, Optional

import numpy as np

import logging
from .quantum_regeneration import (
    ContextSignal,
    ModuleState,
    Role,
    regeneration_pipeline,
)

LANE_COUNT = 32
PHI_BASELINE = (1.0 + 5.0**0.5) / 2.0
PHI_FLOOR = 0.45
SCAR_FREE_FIDELITY_FLOOR = 0.999


def _json_safe(value: object) -> object:
    """Convert regeneration traces into JSON-safe primitives."""
    if isinstance(value, dict):
        return {str(getattr(key, "value", key)): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if hasattr(value, "value"):
        return getattr(value, "value")
    return value


@dataclass(frozen=True)
class RegenerationEventRecord:
    timestamp: datetime
    lane_id: int
    module_id: str
    pre_injury_phi: float
    post_recovery_fidelity: float
    scarring_detected: bool
    recovery_duration_ms: float
    status: str
    collapsed_role: Optional[str]
    trace: Dict[str, object]


@dataclass
class LaneRegenerationState:
    lane_id: int
    module_state: ModuleState
    progenitor_id: str
    clifford_index: int
    generation: int = 0
    module_path: Optional[str] = None
    target_symbol: Optional[str] = None


@dataclass
class RegenerationManager:
    """Owns auditable regeneration state for a fixed 32-lane manifold."""

    lane_count: int = LANE_COUNT
    system_phi: float = PHI_BASELINE
    lanes: Dict[int, LaneRegenerationState] = field(init=False)
    fidelity_history: List[RegenerationEventRecord] = field(default_factory=list)
    healing_proposals: List[Dict[str, Any]] = field(default_factory=list)
    self_healing_reactor: object = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.lanes = {
            lane_id: LaneRegenerationState(
                lane_id=lane_id,
                module_state=ModuleState.healthy(f"lane_{lane_id:02d}_phi_primary"),
                progenitor_id=f"PROG_{lane_id:02d}_GEN_0000",
                clifford_index=lane_id,
            )
            for lane_id in range(self.lane_count)
        }
        self.self_healing_reactor = self._build_self_healing_reactor()

    def _build_self_healing_reactor(self) -> object:
        """Create the codebase-level SelfHealingReactor lazily.

        Imported here to keep the mathematical regeneration module independent
        from the codebase-repair package during import-time tests.
        """

        from pythia_self_healing.salamander_regenerator import SalamanderRegenerator
        from pythia_self_healing.self_healing_reactor import SelfHealingReactor

        return SelfHealingReactor(SalamanderRegenerator())

    def _require_lane(self, lane_id: int) -> LaneRegenerationState:
        if lane_id not in self.lanes:
            raise ValueError(f"Invalid lane_id {lane_id}; expected 0-{self.lane_count - 1}")
        return self.lanes[lane_id]

    def register_lane_target(self, lane_id: int, module_path: str, target_symbol: str) -> Dict[str, object]:
        """Attach a code target to a regeneration lane.

        This makes the lane manager able to route scar/fidelity/φ-floor events
        into the codebase-level SelfHealingReactor without inventing target paths.
        """

        lane = self._require_lane(lane_id)
        lane.module_path = module_path
        lane.target_symbol = target_symbol
        return {
            "lane_id": lane_id,
            "module_path": module_path,
            "target_symbol": target_symbol,
            "self_healing_reactor_attached": True,
        }

    def get_blastema_pool(self) -> List[Dict[str, object]]:
        """Return model-derived progenitor state for each lane."""
        pool: List[Dict[str, object]] = []
        for lane in self.lanes.values():
            pool.append(
                {
                    "lane_id": lane.lane_id,
                    "progenitor_id": lane.progenitor_id,
                    "module_id": lane.module_state.module_id,
                    "role_probabilities": {
                        role.value: probability
                        for role, probability in lane.module_state.role_probabilities().items()
                    },
                    "blastema_entropy": lane.module_state.von_neumann_entropy(),
                    "l3_residency_time_ms": None,
                    "is_primed": lane.module_state.is_in_refractory_period() is False,
                    "target_registered": bool(lane.module_path and lane.target_symbol),
                    "evidence_source": "quantum_regeneration_role_model; no measured L3 residency attached",
                }
            )
        return pool

    def get_status(self) -> Dict[str, object]:
        fidelities = [event.post_recovery_fidelity for event in self.fidelity_history]
        return {
            "system_phi": self.system_phi,
            "innervation_stable": self.system_phi > PHI_FLOOR,
            "active_blastemas": len(self.lanes),
            "global_fidelity_mean": fmean(fidelities) if fidelities else 1.0,
            "regeneration_potential": "MAXIMAL" if self.system_phi > PHI_FLOOR else "LOCKED",
            "fidelity_events": len(self.fidelity_history),
            "healing_proposals_staged": len(self.healing_proposals),
            "lanes": self.get_blastema_pool(),
        }

    async def trigger_regeneration(self, lane_id: int) -> RegenerationEventRecord:
        """Run deterministic regeneration for one lane and persist an audit event."""
        lane = self._require_lane(lane_id)
        if self.system_phi <= PHI_FLOOR:
            raise RuntimeError("Innervation is below phi floor; regeneration is locked")

        start = time.perf_counter()
        logging.getLogger(__name__).info("Salamander regeneration requested for lane %s", lane_id)
        context = ContextSignal(
            clifford_index=lane.clifford_index,
            target_role=Role.HEALTHY_SPECIALIZED,
            confidence=1.0,
        )
        rng = np.random.default_rng(seed=(lane_id << 16) + lane.generation)
        trace = _json_safe(
            regeneration_pipeline(
                module_id=lane.module_state.module_id,
                fault_severity=0.7,
                context=context,
                rng=rng,
            )
        )
        duration_ms = (time.perf_counter() - start) * 1000.0
        fidelity = float(trace.get("fidelity_pre_collapse", 0.0))
        status = str(trace.get("status", "unknown"))
        if status == "success":
            lane.generation += 1
            lane.module_state = ModuleState.healthy(lane.module_state.module_id)
            lane.progenitor_id = f"PROG_{lane_id:02d}_GEN_{lane.generation:04d}"

        event = RegenerationEventRecord(
            timestamp=datetime.now(timezone.utc),
            lane_id=lane_id,
            module_id=lane.module_state.module_id,
            pre_injury_phi=self.system_phi,
            post_recovery_fidelity=fidelity,
            scarring_detected=fidelity < SCAR_FREE_FIDELITY_FLOOR or status != "success",
            recovery_duration_ms=duration_ms,
            status=status,
            collapsed_role=trace.get("collapsed_role"),
            trace=trace,
        )
        self.fidelity_history.append(event)
        if event.scarring_detected and lane.module_path and lane.target_symbol:
            self.stage_self_healing_for_lane(lane_id, lane.module_path, lane.target_symbol, event)
        return event

    def event_to_damage_report(self, event: RegenerationEventRecord) -> Dict[str, Any]:
        """Translate lane-level regeneration telemetry into a reactor DamageReport."""

        lane = self._require_lane(event.lane_id)
        issues: List[str] = []
        if event.pre_injury_phi <= PHI_FLOOR:
            issues.append("φ-floor breach detected in Salamander lane")
        if event.scarring_detected:
            issues.append("scarring/fidelity anomaly detected in Salamander lane")
        if event.status != "success":
            issues.append(f"regeneration status anomaly: {event.status}")
        if event.trace.get("innervation_failure"):
            issues.append("innervation failure detected during redifferentiation")
        if not issues:
            issues.append("lane telemetry routed for sovereign audit")

        return {
            "needs_repair": bool(event.scarring_detected or event.status != "success" or event.pre_injury_phi <= PHI_FLOOR),
            "lane_id": event.lane_id,
            "module_path": lane.module_path,
            "target_name": lane.target_symbol,
            "issues": issues,
            "blastema_state": {
                "module_id": lane.module_state.module_id,
                "role_probabilities": {
                    role.value: probability for role, probability in lane.module_state.role_probabilities().items()
                },
                "entropy": lane.module_state.von_neumann_entropy(),
            },
            "progenitor_state": {
                "progenitor_id": lane.progenitor_id,
                "generation": lane.generation,
                "clifford_index": lane.clifford_index,
            },
            "metrics_before": {
                "pre_injury_phi": event.pre_injury_phi,
                "post_recovery_fidelity": event.post_recovery_fidelity,
                "recovery_duration_ms": event.recovery_duration_ms,
            },
            "metrics_target": {
                "minimum_fidelity": SCAR_FREE_FIDELITY_FLOOR,
                "minimum_phi": PHI_FLOOR,
                "scarring_detected": False,
            },
            "performance_impact": "LANE_LOCAL" if event.recovery_duration_ms < 1000 else "LATENCY_RISK",
            "stability_impact": "SCARRING_RISK" if event.scarring_detected else "STABLE",
            "architecture_impact": "LOCAL_LIMB",
        }

    def stage_self_healing_for_lane(
        self,
        lane_id: int,
        module_path: str,
        target_name: str,
        event: Optional[RegenerationEventRecord] = None,
    ) -> Dict[str, Any]:
        """Route a lane event to the codebase-level SelfHealingReactor.

        The result is stored as a proposal and remains non-deployable until a
        sovereign human approval event exists outside this manager.
        """

        if event is None:
            event = RegenerationEventRecord(
                timestamp=datetime.now(timezone.utc),
                lane_id=lane_id,
                module_id=self._require_lane(lane_id).module_state.module_id,
                pre_injury_phi=self.system_phi,
                post_recovery_fidelity=0.0,
                scarring_detected=True,
                recovery_duration_ms=0.0,
                status="manual_self_healing_request",
                collapsed_role=None,
                trace={"manual": True},
            )
        report = self.event_to_damage_report(event)
        report["module_path"] = module_path
        report["target_name"] = target_name
        packet = self.self_healing_reactor.heal_damage(report, module_path, target_name)
        packet["deployable_without_approval"] = False
        self.healing_proposals.append(packet)
        return packet

    def analyse_organism_governance(self, pulvini_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return CLRI/TRM/predictive/rewiring/benchmark/evidence organism report.

        This is the manager-level entrypoint for Salamander's multi-scale
        autonomic substrate. It stages intelligence and evidence only; it does
        not apply rewires, deploy repairs, or alter Stable Core boundaries.
        """

        from pythia_self_healing.autonomic_organism_governor import SalamanderOrganismGovernor

        governor = SalamanderOrganismGovernor()
        return governor.analyse_manager(self, pulvini_state=pulvini_state)


_MANAGER = RegenerationManager()


def get_regeneration_manager() -> RegenerationManager:
    """Return process-local regeneration manager singleton."""
    return _MANAGER
