"""Post-Turing Telemetry and Observability Layer.

Makes geodesic navigation observable for:
- Debugging
- Sovereign audits
- Research papers
- Performance tuning

Every geodesic traversal is logged with cryptographic proof.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

UTC = timezone.utc


@dataclass(frozen=True)
class GeodesicTelemetryEvent:
    """A single event in geodesic traversal."""

    event_id: str
    timestamp: str
    event_type: str  # "geodesic_start", "fold_transition", "resonance_update", "solution_found"
    problem_id: str
    curvature: float
    geodesic_length: int
    resonance_stability: float
    fold_depth: int
    automorphism_orbit: int
    orbit_size: int
    evidence_hash: str
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PostTuringTelemetryCollector:
    """Collect and audit geodesic navigation telemetry."""

    def __init__(self):
        self._lock = threading.RLock()
        self._events: List[GeodesicTelemetryEvent] = []
        self._event_counter = 0

    def log_geodesic_start(
        self,
        *,
        problem_id: str,
        search_space_size: int,
        initial_curvature: float,
    ) -> GeodesicTelemetryEvent:
        """Log the start of geodesic traversal."""
        now = datetime.now(UTC).isoformat()
        event_id = f"geo_start_{self._new_event_id()}"

        details = {
            "problem_id": problem_id,
            "search_space_size": search_space_size,
            "initial_curvature": initial_curvature,
        }
        details_str = json.dumps(details, sort_keys=True, default=str)
        evidence_hash = hashlib.sha256(details_str.encode()).hexdigest()

        event = GeodesicTelemetryEvent(
            event_id=event_id,
            timestamp=now,
            event_type="geodesic_start",
            problem_id=problem_id,
            curvature=initial_curvature,
            geodesic_length=0,
            resonance_stability=0.0,
            fold_depth=0,
            automorphism_orbit=0,
            orbit_size=0,
            evidence_hash=evidence_hash,
            details=details,
        )

        with self._lock:
            self._events.append(event)

        return event

    def log_fold_transition(
        self,
        *,
        problem_id: str,
        fold_depth: int,
        automorphism_orbit: int,
        orbit_size: int,
        geodesic_length: int,
    ) -> GeodesicTelemetryEvent:
        """Log a φ-fold transition during geodesic traversal."""
        now = datetime.now(UTC).isoformat()
        event_id = f"geo_fold_{self._new_event_id()}"

        details = {
            "fold_depth": fold_depth,
            "automorphism_orbit": automorphism_orbit,
            "orbit_size": orbit_size,
            "geodesic_length": geodesic_length,
        }
        details_str = json.dumps(details, sort_keys=True, default=str)
        evidence_hash = hashlib.sha256(details_str.encode()).hexdigest()

        event = GeodesicTelemetryEvent(
            event_id=event_id,
            timestamp=now,
            event_type="fold_transition",
            problem_id=problem_id,
            curvature=0.0,
            geodesic_length=geodesic_length,
            resonance_stability=0.0,
            fold_depth=fold_depth,
            automorphism_orbit=automorphism_orbit,
            orbit_size=orbit_size,
            evidence_hash=evidence_hash,
            details=details,
        )

        with self._lock:
            self._events.append(event)

        return event

    def log_resonance_stability(
        self,
        *,
        problem_id: str,
        resonance_stability: float,
        curvature: float,
        geodesic_length: int,
        orbit_equivalence_class: int,
    ) -> GeodesicTelemetryEvent:
        """Log resonance stability check during traversal."""
        now = datetime.now(UTC).isoformat()
        event_id = f"geo_resonance_{self._new_event_id()}"

        details = {
            "resonance_stability": resonance_stability,
            "curvature": curvature,
            "orbit_equivalence_class": orbit_equivalence_class,
        }
        details_str = json.dumps(details, sort_keys=True, default=str)
        evidence_hash = hashlib.sha256(details_str.encode()).hexdigest()

        event = GeodesicTelemetryEvent(
            event_id=event_id,
            timestamp=now,
            event_type="resonance_update",
            problem_id=problem_id,
            curvature=curvature,
            geodesic_length=geodesic_length,
            resonance_stability=resonance_stability,
            fold_depth=0,
            automorphism_orbit=orbit_equivalence_class,
            orbit_size=0,
            evidence_hash=evidence_hash,
            details=details,
        )

        with self._lock:
            self._events.append(event)

        return event

    def log_automorphism_transition(
        self,
        *,
        problem_id: str,
        from_orbit: int,
        to_orbit: int,
        orbit_size: int,
        transition_cost: float,
    ) -> GeodesicTelemetryEvent:
        """Log a transition between automorphism orbits."""
        now = datetime.now(UTC).isoformat()
        event_id = f"geo_aut_{self._new_event_id()}"

        details = {
            "from_orbit": from_orbit,
            "to_orbit": to_orbit,
            "orbit_size": orbit_size,
            "transition_cost": transition_cost,
        }
        details_str = json.dumps(details, sort_keys=True, default=str)
        evidence_hash = hashlib.sha256(details_str.encode()).hexdigest()

        event = GeodesicTelemetryEvent(
            event_id=event_id,
            timestamp=now,
            event_type="automorphism_transition",
            problem_id=problem_id,
            curvature=0.0,
            geodesic_length=0,
            resonance_stability=0.0,
            fold_depth=0,
            automorphism_orbit=to_orbit,
            orbit_size=orbit_size,
            evidence_hash=evidence_hash,
            details=details,
        )

        with self._lock:
            self._events.append(event)

        return event

    def log_solution_found(
        self,
        *,
        problem_id: str,
        geodesic_length: int,
        total_search_steps: int,
        resonance_stability: float,
        solution_hash: str,
    ) -> GeodesicTelemetryEvent:
        """Log when a solution is found."""
        now = datetime.now(UTC).isoformat()
        event_id = f"geo_solution_{self._new_event_id()}"

        details = {
            "geodesic_length": geodesic_length,
            "total_search_steps": total_search_steps,
            "resonance_stability": resonance_stability,
            "solution_hash": solution_hash,
            "efficiency_ratio": geodesic_length / max(total_search_steps, 1),
        }
        details_str = json.dumps(details, sort_keys=True, default=str)
        evidence_hash = hashlib.sha256(details_str.encode()).hexdigest()

        event = GeodesicTelemetryEvent(
            event_id=event_id,
            timestamp=now,
            event_type="solution_found",
            problem_id=problem_id,
            curvature=0.0,
            geodesic_length=geodesic_length,
            resonance_stability=resonance_stability,
            fold_depth=0,
            automorphism_orbit=0,
            orbit_size=0,
            evidence_hash=evidence_hash,
            details=details,
        )

        with self._lock:
            self._events.append(event)

        return event

    def get_event_stream(
        self,
        *,
        problem_id: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get filtered event stream."""
        with self._lock:
            events = self._events
            if problem_id:
                events = [e for e in events if e.problem_id == problem_id]
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            return [e.to_dict() for e in events]

    def generate_telemetry_report(
        self, *, problem_id: str
    ) -> Dict[str, Any]:
        """Generate a comprehensive telemetry report for a problem."""
        with self._lock:
            events = [e for e in self._events if e.problem_id == problem_id]

        if not events:
            return {
                "problem_id": problem_id,
                "error": "No events found",
            }

        # Aggregate statistics
        fold_events = [e for e in events if e.event_type == "fold_transition"]
        resonance_events = [e for e in events if e.event_type == "resonance_update"]
        solution_events = [e for e in events if e.event_type == "solution_found"]

        avg_resonance = (
            sum(e.resonance_stability for e in resonance_events)
            / len(resonance_events)
            if resonance_events
            else 0.0
        )
        max_geodesic_length = (
            max(e.geodesic_length for e in events)
            if events
            else 0
        )
        max_fold_depth = (
            max(e.fold_depth for e in fold_events)
            if fold_events
            else 0
        )

        # Build audit chain
        event_chain = json.dumps(
            [e.to_dict() for e in events],
            sort_keys=True,
            default=str,
        )
        chain_seal = hashlib.sha256(event_chain.encode()).hexdigest()

        report = {
            "problem_id": problem_id,
            "timestamp_generated": datetime.now(UTC).isoformat(),
            "total_events": len(events),
            "event_types": list(set(e.event_type for e in events)),
            "fold_transitions": len(fold_events),
            "max_fold_depth": max_fold_depth,
            "resonance_updates": len(resonance_events),
            "avg_resonance_stability": avg_resonance,
            "solutions_found": len(solution_events),
            "max_geodesic_length": max_geodesic_length,
            "events": [e.to_dict() for e in events],
            "audit_chain_seal": chain_seal,
        }

        return report

    def _new_event_id(self) -> int:
        """Generate a unique event ID."""
        with self._lock:
            self._event_counter += 1
            return self._event_counter


# Singleton instance
_telemetry_collector = PostTuringTelemetryCollector()


def get_telemetry_collector() -> PostTuringTelemetryCollector:
    """Get the global telemetry collector."""
    return _telemetry_collector


__all__ = [
    "GeodesicTelemetryEvent",
    "PostTuringTelemetryCollector",
    "get_telemetry_collector",
]
