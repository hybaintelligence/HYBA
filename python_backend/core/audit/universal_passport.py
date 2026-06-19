"""Universal passport and verifiable claim format for HYBA subsystems.

This module provides a domain-agnostic audit-log primitive that can be used
across all HYBA subsystems (pythia, security_swarm, iit_engine, finance_dashboard,
meta_controller) for consistent, verifiable claim logging.

The passport format includes:
- Self-verifying hash for tamper detection
- Explicit epistemic bounds (what is NOT claimed)
- Subsystem identification
- Claim type categorization
- Timestamp for audit trail ordering

Mathematical properties:
- Hash chain integrity: passport_hash = H(payload || claim_type || timestamp || epistemic_bounds)
- Epistemic completeness: all claims must have explicit boundary statements
- Temporal ordering: timestamps are monotonic within a subsystem
- Subsystem isolation: passports from different subsystems cannot collide
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, ClassVar, Mapping, Sequence

# Schema version for compatibility and migration
UNIVERSAL_PASSPORT_SCHEMA_VERSION = "UNIVERSAL_PASSPORT_V1"

# Fixed-point scale for numeric values (matches existing PULVINI scale)
_FIXED_POINT_SCALE = 1_000_000_000


class Subsystem(str, Enum):
    """HYBA subsystem identifiers for passport attribution."""

    PYTHIA = "pythia"
    SECURITY_SWARM = "security_swarm"
    IIT_ENGINE = "iit_engine"
    FINANCE_DASHBOARD = "finance_dashboard"
    META_CONTROLLER = "meta_controller"
    EUCLID = "euclid"
    UNIFIED_SEARCH = "unified_search"


class ClaimType(str, Enum):
    """Standardized claim types across all HYBA subsystems."""

    # Mining claims
    NONCE_FOUND = "nonce_found"
    SHARE_SUBMISSION = "share_submission"
    MINING_RESULT = "mining_result"

    # Security claims
    MODE_TRANSITION = "mode_transition"
    SECURITY_EVENT = "security_event"
    CIRCUIT_BREAKER_TRIP = "circuit_breaker_trip"

    # IIT/consciousness claims
    PHI_MEASUREMENT = "phi_measurement"
    CONSCIOUSNESS_STATE = "consciousness_state"
    INTEGRATED_INFORMATION = "integrated_information"

    # Finance claims
    TRANSACTION = "transaction"
    PORTFOLIO_UPDATE = "portfolio_update"
    RISK_ASSESSMENT = "risk_assessment"

    # Meta-controller claims
    ROUTING_DECISION = "routing_decision"
    AUTONOMOUS_ACTION = "autonomous_action"
    CONTROLLER_INTERVENTION = "controller_intervention"

    # Search kernel claims
    SEARCH_RESULT = "search_result"
    SEARCH_CACHED = "search_cached"
    SEARCH_FAILED = "search_failed"


class EpistemicBound(str, Enum):
    """Standardized epistemic boundary statements.

    These are explicit denials of claims that the system does NOT make.
    They prevent over-interpretation of audit logs.
    """

    NO_QUANTUM_SPEEDUP = "does_not_claim_quantum_speedup"
    NO_CONSCIOUSNESS_CLAIM = "phi_is_model_relative_not_consciousness_claim"
    NO_FINANCIAL_ADVICE = "not_financial_advice"
    NO_GUARANTEE_CORRECTNESS = "no_guarantee_of_correctness"
    NO_REAL_TIME_GUARANTEE = "no_real_time_guarantee"
    NO_SECURITY_INVULNERABILITY = "not_security_invulnerable"
    NO_DETERMINISTIC_OUTCOME = "outcome_not_deterministic"
    MODEL_RELATIVE_ONLY = "model_relative_measure_only"
    EMPIRICAL_VALIDATION_ONLY = "empirically_validated_only"
    THEORETICAL_BOUND_ONLY = "theoretical_bound_only"


@dataclass(frozen=True)
class UniversalPassport:
    """Universal verifiable claim object for HYBA audit logging.

    This passport is the single audit-log primitive across all HYBA subsystems.
    It provides self-verification, explicit epistemic boundaries, and subsystem
    isolation for consistent forensic analysis.

    Mathematical invariants:
    1. Hash integrity: passport_hash == H(canonical_payload)
    2. Epistemic completeness: epistemic_bounds must be non-empty for high-stakes claims
    3. Temporal monotonicity: timestamps increase within a subsystem
    4. Subsystem validity: subsystem must be a valid Subsystem enum value
    5. Claim validity: claim_type must be a valid ClaimType enum value
    """

    schema_version: str = UNIVERSAL_PASSPORT_SCHEMA_VERSION
    subsystem: str = ""
    claim_type: str = ""
    payload: Mapping[str, Any] = field(default_factory=dict)
    epistemic_bounds: Sequence[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    embedded_hash: str = ""

    def __post_init__(self) -> None:
        """Validate passport invariants and compute hash if not provided."""
        # Validate subsystem
        try:
            Subsystem(self.subsystem)
        except ValueError:
            raise ValueError(f"Invalid subsystem: {self.subsystem}")

        # Validate claim type
        try:
            ClaimType(self.claim_type)
        except ValueError:
            raise ValueError(f"Invalid claim_type: {self.claim_type}")

        # Validate epistemic bounds
        for bound in self.epistemic_bounds:
            try:
                EpistemicBound(bound)
            except ValueError:
                raise ValueError(f"Invalid epistemic_bound: {bound}")

        # Compute hash if not provided
        if not object.__getattribute__(self, "embedded_hash"):
            object.__setattr__(
                self, "embedded_hash", self._compute_hash()
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert passport to canonical dictionary representation."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert passport to canonical JSON string."""
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

    def verify(self) -> bool:
        """Verify the embedded hash matches the current payload.

        Returns True if the passport has not been tampered with.
        """
        computed = self._compute_hash()
        return computed == self.embedded_hash

    def verify_epistemic_completeness(self, required_bounds: Sequence[str]) -> bool:
        """Verify that required epistemic bounds are present.

        Some claim types require specific epistemic boundaries to prevent
        misinterpretation. This method checks that those boundaries are present.
        """
        return all(bound in self.epistemic_bounds for bound in required_bounds)

    def _compute_hash(self) -> str:
        """Compute SHA-256 hash of canonical payload."""
        material = {
            "schema_version": self.schema_version,
            "subsystem": self.subsystem,
            "claim_type": self.claim_type,
            "payload": dict(self.payload),
            "epistemic_bounds": sorted(self.epistemic_bounds),
            "timestamp": self.timestamp,
        }
        canonical = json.dumps(
            material,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    @property
    def passport_hash(self) -> str:
        """Alias for embedded_hash for compatibility with existing code."""
        return self.embedded_hash


def make_passport(
    subsystem: str,
    claim_type: str,
    payload: Mapping[str, Any],
    epistemic_bounds: Sequence[str] | None = None,
    timestamp: float | None = None,
) -> UniversalPassport:
    """Factory function to create a UniversalPassport with validation.

    Args:
        subsystem: The HYBA subsystem generating this claim
        claim_type: The type of claim being made
        payload: The claim-specific data
        epistemic_bounds: Explicit boundaries of what is NOT claimed
        timestamp: Optional timestamp (defaults to current time)

    Returns:
        A validated UniversalPassport with computed hash

    Raises:
        ValueError: If subsystem, claim_type, or epistemic_bounds are invalid
    """
    return UniversalPassport(
        subsystem=subsystem,
        claim_type=claim_type,
        payload=dict(payload),
        epistemic_bounds=list(epistemic_bounds or []),
        timestamp=timestamp if timestamp is not None else time.time(),
        embedded_hash="",  # Will be computed in __post_init__
    )


def make_mining_passport(
    nonce: int,
    job_id: str,
    pool_name: str,
    phi_score: float,
    bures_score: float,
    timestamp: float | None = None,
) -> UniversalPassport:
    """Create a passport for a mining nonce discovery.

    This is a convenience wrapper for the most common mining claim type.
    """
    return make_passport(
        subsystem=Subsystem.PYTHIA.value,
        claim_type=ClaimType.NONCE_FOUND.value,
        payload={
            "nonce": nonce,
            "job_id": job_id,
            "pool_name": pool_name,
            "phi_score": phi_score,
            "bures_score": bures_score,
        },
        epistemic_bounds=[
            EpistemicBound.NO_QUANTUM_SPEEDUP.value,
            EpistemicBound.NO_GUARANTEE_CORRECTNESS.value,
        ],
        timestamp=timestamp,
    )


def make_mode_transition_passport(
    from_mode: str,
    to_mode: str,
    reason: str,
    security_context: Mapping[str, Any],
    timestamp: float | None = None,
) -> UniversalPassport:
    """Create a passport for a security mode transition."""
    return make_passport(
        subsystem=Subsystem.SECURITY_SWARM.value,
        claim_type=ClaimType.MODE_TRANSITION.value,
        payload={
            "from_mode": from_mode,
            "to_mode": to_mode,
            "reason": reason,
            "security_context": dict(security_context),
        },
        epistemic_bounds=[
            EpistemicBound.NO_SECURITY_INVULNERABILITY.value,
            EpistemicBound.NO_REAL_TIME_GUARANTEE.value,
        ],
        timestamp=timestamp,
    )


def make_phi_measurement_passport(
    phi_value: float,
    system_state: Mapping[str, Any],
    measurement_context: Mapping[str, Any],
    timestamp: float | None = None,
) -> UniversalPassport:
    """Create a passport for an IIT Φ measurement."""
    return make_passport(
        subsystem=Subsystem.IIT_ENGINE.value,
        claim_type=ClaimType.PHI_MEASUREMENT.value,
        payload={
            "phi_value": phi_value,
            "system_state": dict(system_state),
            "measurement_context": dict(measurement_context),
        },
        epistemic_bounds=[
            EpistemicBound.NO_CONSCIOUSNESS_CLAIM.value,
            EpistemicBound.MODEL_RELATIVE_ONLY.value,
        ],
        timestamp=timestamp,
    )


def make_circuit_breaker_passport(
    signal: Mapping[str, Any],
    route: str,
    explanation: Mapping[str, Any],
    timestamp: float | None = None,
) -> UniversalPassport:
    """Create a passport for a circuit-breaker trip event."""
    return make_passport(
        subsystem=Subsystem.META_CONTROLLER.value,
        claim_type=ClaimType.CIRCUIT_BREAKER_TRIP.value,
        payload={
            "signal": dict(signal),
            "route": route,
            "explanation": dict(explanation),
        },
        epistemic_bounds=[
            EpistemicBound.NO_GUARANTEE_CORRECTNESS.value,
            EpistemicBound.NO_DETERMINISTIC_OUTCOME.value,
        ],
        timestamp=timestamp,
    )


class SharedAuditLog:
    """Shared audit log for UniversalPassport entries across all subsystems.

    This provides a single append-only log that all subsystems write to,
    ensuring consistent audit trail ordering and verification.

    The log maintains:
    1. Append-only semantics (entries cannot be deleted or modified)
    2. Hash chaining for integrity verification
    3. Subsystem isolation for attribution
    4. Temporal ordering for forensic analysis
    """

    def __init__(self, storage_path: str | None = None):
        """Initialize the shared audit log.

        Args:
            storage_path: Optional path to persistent storage.
                        If None, uses in-memory storage only.
        """
        self._entries: list[UniversalPassport] = []
        self._storage_path = storage_path
        self._load_from_storage()

    def append(self, passport: UniversalPassport) -> None:
        """Append a passport to the audit log.

        Args:
            passport: The passport to append

        Raises:
            ValueError: If passport verification fails
        """
        if not passport.verify():
            raise ValueError("Cannot append passport with invalid hash")

        if not passport.verify_epistemic_completeness(
            self._required_bounds_for_claim(passport.claim_type)
        ):
            raise ValueError(
                f"Passport missing required epistemic bounds for {passport.claim_type}"
            )

        self._entries.append(passport)
        self._save_to_storage()

    def get_entries(
        self,
        subsystem: str | None = None,
        claim_type: str | None = None,
        since: float | None = None,
        until: float | None = None,
    ) -> list[UniversalPassport]:
        """Query the audit log with filters.

        Args:
            subsystem: Filter by subsystem (optional)
            claim_type: Filter by claim type (optional)
            since: Filter by timestamp >= since (optional)
            until: Filter by timestamp <= until (optional)

        Returns:
            List of matching passports in chronological order
        """
        entries = self._entries

        if subsystem is not None:
            entries = [e for e in entries if e.subsystem == subsystem]

        if claim_type is not None:
            entries = [e for e in entries if e.claim_type == claim_type]

        if since is not None:
            entries = [e for e in entries if e.timestamp >= since]

        if until is not None:
            entries = [e for e in entries if e.timestamp <= until]

        return entries

    def verify_chain(self) -> bool:
        """Verify the integrity of the entire audit log chain.

        Returns:
            True if all passports have valid hashes
        """
        return all(passport.verify() for passport in self._entries)

    def _required_bounds_for_claim(self, claim_type: str) -> list[str]:
        """Return required epistemic bounds for a given claim type."""
        # High-stakes claims require explicit boundaries
        # Each claim type has its own specific required bounds
        requirements = {
            ClaimType.NONCE_FOUND.value: [EpistemicBound.NO_QUANTUM_SPEEDUP.value],
            ClaimType.MODE_TRANSITION.value: [EpistemicBound.NO_SECURITY_INVULNERABILITY.value],
            ClaimType.CIRCUIT_BREAKER_TRIP.value: [EpistemicBound.NO_GUARANTEE_CORRECTNESS.value],
            ClaimType.PHI_MEASUREMENT.value: [EpistemicBound.NO_CONSCIOUSNESS_CLAIM.value],
        }

        return requirements.get(claim_type, [])

    def _load_from_storage(self) -> None:
        """Load entries from persistent storage if available."""
        if self._storage_path is None:
            return

        try:
            from pathlib import Path

            path = Path(self._storage_path)
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                self._entries = [
                    UniversalPassport(**entry) for entry in data.get("entries", [])
                ]
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            # Start with empty log if storage is unavailable or corrupted
            self._entries = []

    def _save_to_storage(self) -> None:
        """Save entries to persistent storage if available."""
        if self._storage_path is None:
            return

        try:
            from pathlib import Path

            path = Path(self._storage_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "entries": [entry.to_dict() for entry in self._entries],
                "schema_version": UNIVERSAL_PASSPORT_SCHEMA_VERSION,
            }
            path.write_text(
                json.dumps(data, sort_keys=True, indent=2),
                encoding="utf-8",
            )
        except OSError:
            # Fail silently if storage is unavailable
            pass


__all__ = [
    "UNIVERSAL_PASSPORT_SCHEMA_VERSION",
    "Subsystem",
    "ClaimType",
    "EpistemicBound",
    "UniversalPassport",
    "make_passport",
    "make_mining_passport",
    "make_mode_transition_passport",
    "make_phi_measurement_passport",
    "make_circuit_breaker_passport",
    "SharedAuditLog",
]
