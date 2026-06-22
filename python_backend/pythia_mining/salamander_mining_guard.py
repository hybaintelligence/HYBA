"""Salamander mining guard for same-day live mining deployment.

The guard is the seam between the production mining organism and the
Salamander regeneration substrate.  It does not mine, submit shares, or change
runtime parameters.  It proves that the 32-lane blastema pool is present,
registers the mining targets that Salamander may repair, warms representative
lanes, stages repair proposals when scar/fidelity anomalies are detected, and
returns a JSON-safe gate report for deployment evidence.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from .regeneration_manager import PHI_FLOOR, RegenerationEventRecord, RegenerationManager, get_regeneration_manager


@dataclass(frozen=True)
class SalamanderMiningGateReport:
    """Evidence packet emitted before mining ignition or dry-run validation."""

    timestamp: str
    source: str
    ready: bool
    strict_mode: bool
    system_phi: float
    phi_floor: float
    active_blastemas: int
    lanes_checked: List[int]
    regeneration_statuses: List[str]
    scar_events: int
    healing_proposals_staged: int
    target_registry_complete: bool
    blocker: Optional[str]
    warnings: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SalamanderMiningGuard:
    """Run Salamander preflight and evidence staging for mining operations."""

    DEFAULT_TARGETS = {
        0: ("python_backend/pythia_mining/production_mining_system.py", "ProductionMiningSystem"),
        1: ("python_backend/pythia_mining/mining_executive_controller.py", "MiningExecutiveController"),
        2: ("python_backend/pythia_mining/stratum_client.py", "StratumClient"),
    }

    def __init__(self, manager: Optional[RegenerationManager] = None):
        self.manager = manager or get_regeneration_manager()
        self.last_report: Optional[SalamanderMiningGateReport] = None

    def register_mining_targets(self) -> List[Dict[str, object]]:
        """Bind canonical mining components to deterministic Salamander lanes."""

        registrations: List[Dict[str, object]] = []
        for lane_id, (module_path, target_symbol) in self.DEFAULT_TARGETS.items():
            registrations.append(
                self.manager.register_lane_target(lane_id, module_path, target_symbol)
            )
        return registrations

    def _strict_mode(self, strict: Optional[bool]) -> bool:
        if strict is not None:
            return strict
        return os.getenv("HYBA_SALAMANDER_STRICT_PREFLIGHT", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    async def preflight(
        self,
        *,
        source: str,
        lane_ids: Iterable[int] = (0, 1, 2),
        strict: Optional[bool] = None,
    ) -> SalamanderMiningGateReport:
        """Run a mining-safe Salamander readiness gate.

        Strict mode blocks on any scar/fidelity anomaly.  Normal same-day live
        mode permits ignition when the organism is coherent and regeneration
        succeeds, while retaining scar events as staged repair proposals.
        """

        strict_mode = self._strict_mode(strict)
        self.register_mining_targets()

        status_before = self.manager.get_status()
        warnings: List[str] = []
        blocker: Optional[str] = None
        checked: List[int] = []
        events: List[RegenerationEventRecord] = []

        if not bool(status_before.get("innervation_stable")):
            blocker = "SALAMANDER_PHI_FLOOR_LOCK"
        elif int(status_before.get("active_blastemas", 0)) < self.manager.lane_count:
            blocker = "SALAMANDER_BLASTEMA_POOL_INCOMPLETE"

        if blocker is None:
            for lane_id in lane_ids:
                checked.append(int(lane_id))
                try:
                    events.append(await self.manager.trigger_regeneration(int(lane_id)))
                except Exception as exc:  # pragma: no cover - defensive live guard
                    blocker = "SALAMANDER_REGENERATION_EXCEPTION"
                    warnings.append(f"lane_{lane_id}: {exc}")
                    break

        scar_events = sum(1 for event in events if event.scarring_detected)
        statuses = [event.status for event in events]
        failed_statuses = [status for status in statuses if status != "success"]
        target_registry_complete = all(
            bool(self.manager.lanes[lane_id].module_path and self.manager.lanes[lane_id].target_symbol)
            for lane_id in self.DEFAULT_TARGETS
        )

        if failed_statuses and blocker is None:
            blocker = "SALAMANDER_REGENERATION_STATUS_FAILURE"
        if scar_events:
            warnings.append(
                f"{scar_events} scar/fidelity event(s) staged as repair evidence before mining ignition"
            )
            if strict_mode and blocker is None:
                blocker = "SALAMANDER_STRICT_SCAR_LOCK"
        if not target_registry_complete and blocker is None:
            blocker = "SALAMANDER_TARGET_REGISTRY_INCOMPLETE"

        report = SalamanderMiningGateReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            source=source,
            ready=blocker is None,
            strict_mode=strict_mode,
            system_phi=float(status_before.get("system_phi", 0.0)),
            phi_floor=PHI_FLOOR,
            active_blastemas=int(status_before.get("active_blastemas", 0)),
            lanes_checked=checked,
            regeneration_statuses=statuses,
            scar_events=scar_events,
            healing_proposals_staged=len(self.manager.healing_proposals),
            target_registry_complete=target_registry_complete,
            blocker=blocker,
            warnings=warnings,
        )
        self.last_report = report
        return report

    def telemetry(self) -> Dict[str, Any]:
        """Return the last gate report plus current regeneration status."""

        return {
            "last_gate": self.last_report.to_dict() if self.last_report else None,
            "regeneration_status": self.manager.get_status(),
        }
