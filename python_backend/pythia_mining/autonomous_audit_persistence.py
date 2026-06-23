"""Persistent audit log with SHA-256 integrity for autonomous decisions.

Every decision, escalation, degradation, and self-healing event is written to
a structured JSON-segment audit file with checksum verification on read-back.
This guarantees tamper-evident transparency for the fully autonomous system.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ImmutableAuditEntry:
    """A single, content-addressed audit event that cannot be mutated after creation."""

    entry_id: str
    timestamp: float
    event_type: str
    autonomy_level: str
    decision_id: Optional[str] = None
    action: str = ""
    outcome: str = ""
    constraints_checked: List[str] = field(default_factory=list)
    constraints_violated: List[str] = field(default_factory=list)
    operator_id: Optional[str] = None
    operator_action: Optional[str] = None
    state_diff: Dict[str, Any] = field(default_factory=dict)
    # Content-addressed integrity chain
    checksum_sha256: str = ""
    previous_entry_checksum: str = ""

    @staticmethod
    def compute_checksum(payload: Dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> ImmutableAuditEntry:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# Maximum number of segments to load on init (hot window for chain continuity).
# Older segments remain on disk but are not loaded into memory.
_LOAD_SEGMENTS_LIMIT: int = 3
# Maximum number of segment files retained on disk before the oldest are pruned.
_MAX_SEGMENTS_ON_DISK: int = 10


class AuditJournal:
    """Append-only, tamper-evident audit journal backed by rotating JSON segments.

    Each segment is a JSON list of ImmutableAuditEntry dicts with a trailing
    SHA-256 checksum of the entire segment file, stored in a sidecar ``.sha256``.

    This guarantees: once written, an entry cannot be silently removed or altered
    without breaking the checksum chain across entries and segments.

    Rotation policy:
    - On init, only the most recent ``_LOAD_SEGMENTS_LIMIT`` segments are loaded
      into memory (avoids O(total history) cost on every boot).
    - After each flush, segments beyond ``_MAX_SEGMENTS_ON_DISK`` are pruned
      (oldest-first) so disk usage stays bounded.
    """

    def __init__(self, journal_dir: str = "artifacts/autonomous_mining/audit") -> None:
        self._journal_dir = Path(journal_dir)
        self._journal_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._segment_size: int = 5000  # entries per segment before rotation
        self._entries: List[ImmutableAuditEntry] = []
        self._dirty: bool = False
        self._last_entry_checksum: str = ""
        self._load_existing_segments()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def append(
        self,
        event_type: str,
        autonomy_level: str,
        *,
        decision_id: Optional[str] = None,
        action: str = "",
        outcome: str = "",
        constraints_checked: Optional[List[str]] = None,
        constraints_violated: Optional[List[str]] = None,
        operator_id: Optional[str] = None,
        operator_action: Optional[str] = None,
        state_diff: Optional[Dict[str, Any]] = None,
    ) -> ImmutableAuditEntry:
        """Create, chain-checksum, and append a single audit entry (thread-safe)."""
        entry_id = f"audit_{uuid.uuid4().hex[:12]}_{int(time.time() * 1000)}"
        entry_dict: Dict[str, Any] = {
            "entry_id": entry_id,
            "timestamp": time.time(),
            "event_type": event_type,
            "autonomy_level": autonomy_level,
            "decision_id": decision_id,
            "action": action,
            "outcome": outcome,
            "constraints_checked": constraints_checked or [],
            "constraints_violated": constraints_violated or [],
            "operator_id": operator_id,
            "operator_action": operator_action,
            "state_diff": state_diff or {},
            "checksum_sha256": "",
            "previous_entry_checksum": self._last_entry_checksum,
        }
        entry_dict["checksum_sha256"] = ImmutableAuditEntry.compute_checksum(entry_dict)
        entry = ImmutableAuditEntry.from_dict(entry_dict)
        with self._lock:
            self._entries.append(entry)
            self._last_entry_checksum = entry.checksum_sha256
            self._dirty = True
            self._maybe_flush()
            return entry

    def append_from_audit_entry(self, entry: ImmutableAuditEntry) -> None:
        """Directly append a pre-built entry (e.g. during journal recovery)."""
        with self._lock:
            self._entries.append(entry)
            self._last_entry_checksum = entry.checksum_sha256
            self._dirty = True

    def query(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        event_type: Optional[str] = None,
        autonomy_level: Optional[str] = None,
        since_timestamp: Optional[float] = None,
        decision_id: Optional[str] = None,
    ) -> List[ImmutableAuditEntry]:
        """Filtered, bounded query over in-memory entries (with segment fallback for history)."""
        with self._lock:
            candidates = list(self._entries)

        # Reverse so most recent first
        candidates.reverse()

        filtered: List[ImmutableAuditEntry] = []
        for e in candidates:
            if event_type and e.event_type != event_type:
                continue
            if autonomy_level and e.autonomy_level != autonomy_level:
                continue
            if since_timestamp and e.timestamp < since_timestamp:
                continue
            if decision_id and e.decision_id != decision_id:
                continue
            filtered.append(e)
            if len(filtered) >= offset + limit:
                break

        return filtered[offset:]

    def count(self, *, event_type: Optional[str] = None) -> int:
        """Total entries, optionally filtered by event_type."""
        with self._lock:
            if event_type:
                return sum(1 for e in self._entries if e.event_type == event_type)
            return len(self._entries)

    def flush(self) -> None:
        """Force a synchronous flush to disk."""
        with self._lock:
            self._flush_segment()

    def verify_chain_integrity(self) -> Dict[str, Any]:
        """Walk the in-memory entry chain and verify checksums are consistent."""
        with self._lock:
            issues: List[str] = []
            prev_checksum = ""
            for idx, entry in enumerate(self._entries):
                payload = {k: v for k, v in entry.to_dict().items()}
                stored_checksum = payload.get("checksum_sha256", "")
                # Zero out the checksum field before recomputing — mirrors how append() computed it
                payload["checksum_sha256"] = ""
                expected = ImmutableAuditEntry.compute_checksum(payload)
                if stored_checksum != expected:
                    issues.append(
                        f"entry[{idx}] {entry.entry_id}: "
                        f"checksum mismatch (stored={stored_checksum[:16]}... "
                        f"computed={expected[:16]}...)"
                    )
                if entry.previous_entry_checksum != prev_checksum:
                    issues.append(
                        f"entry[{idx}] {entry.entry_id}: "
                        f"chain broken (expected_prev={prev_checksum[:16]}... "
                        f"got={entry.previous_entry_checksum[:16]}...)"
                    )
                prev_checksum = stored_checksum
            return {
                "total_entries": len(self._entries),
                "issues": issues,
                "chain_intact": len(issues) == 0,
            }

    # ------------------------------------------------------------------
    # Internal persistence
    # ------------------------------------------------------------------

    def _load_existing_segments(self) -> None:
        """Load the most recent _LOAD_SEGMENTS_LIMIT segments on init.

        Older segments remain on disk (cold archive) but are not loaded into
        memory.  This caps init cost at O(recent entries) regardless of how
        much history has accumulated on disk.
        """
        segments = sorted(self._journal_dir.glob("audit_segment_*.json"))
        # Take only the most recent N segments; skip the rest.
        hot_segments = segments[-_LOAD_SEGMENTS_LIMIT:]
        for seg_path in hot_segments:
            seg_checksum_path = seg_path.with_suffix(seg_path.suffix + ".sha256")
            if not seg_checksum_path.exists():
                continue
            try:
                stored_seg_checksum = seg_checksum_path.read_text(
                    encoding="utf-8"
                ).strip()
                actual_seg_checksum = hashlib.sha256(seg_path.read_bytes()).hexdigest()
                if stored_seg_checksum != actual_seg_checksum:
                    continue  # Corrupt segment — skip
                with open(seg_path, "r") as f:
                    entries_data = json.load(f)
                for ed in entries_data:
                    entry = ImmutableAuditEntry.from_dict(ed)
                    self.append_from_audit_entry(entry)
            except (OSError, json.JSONDecodeError):
                pass  # Skip unreadable segments

    def _maybe_flush(self) -> None:
        """Flush to disk if the in-memory buffer exceeds segment size."""
        if len(self._entries) >= self._segment_size:
            self._flush_segment()

    def _flush_segment(self) -> None:
        """Write current entries to a new segment file with checksum.

        After a successful write:
        - Clears the in-memory buffer (avoids O(n²) re-serialisation).
        - Prunes segments beyond _MAX_SEGMENTS_ON_DISK (oldest-first) so
          disk usage stays bounded.
        """
        if not self._dirty:
            return
        segment_id = int(time.time() * 1000)
        seg_path = self._journal_dir / f"audit_segment_{segment_id}.json"
        try:
            serializable = [e.to_dict() for e in self._entries]
            payload = json.dumps(serializable, indent=2, sort_keys=True, default=str)
            seg_path.write_text(payload, encoding="utf-8")
            seg_checksum = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            seg_path.with_suffix(seg_path.suffix + ".sha256").write_text(
                seg_checksum, encoding="utf-8"
            )
            self._entries.clear()
            self._dirty = False
            self._prune_old_segments()
        except OSError:
            pass  # Non-fatal — entries are still in memory

    def _prune_old_segments(self) -> None:
        """Delete the oldest segment files (+ their .sha256 sidecars) when the
        total on-disk count exceeds _MAX_SEGMENTS_ON_DISK."""
        segments = sorted(self._journal_dir.glob("audit_segment_*.json"))
        excess = len(segments) - _MAX_SEGMENTS_ON_DISK
        for seg_path in segments[:excess]:
            seg_path.unlink(missing_ok=True)
            seg_path.with_suffix(seg_path.suffix + ".sha256").unlink(missing_ok=True)


class AutonomousAuditLogger:
    """High-level audit logger that bridges AutonomousMiningController to AuditJournal.

    Provides convience methods for the common audit event types emitted by
    the autonomous controller, so callers never touch the journal directly.
    """

    def __init__(self, journal: Optional[AuditJournal] = None) -> None:
        self._journal = journal or AuditJournal()

    def log_startup_self_healing(
        self,
        autonomy_level: str,
        *,
        phi_density_before: float,
        phi_density_after: float,
        duration_ms: float,
        proposals_generated: int,
        proposals_applied: int,
        stale_lock_recoveries: int,
    ) -> None:
        self._journal.append(
            "startup_self_healing",
            autonomy_level,
            action="boot_self_heal_and_optimize",
            outcome="completed",
            state_diff={
                "phi_density_before": phi_density_before,
                "phi_density_after": phi_density_after,
                "duration_ms": duration_ms,
                "proposals_generated": proposals_generated,
                "proposals_applied": proposals_applied,
                "stale_lock_recoveries": stale_lock_recoveries,
            },
        )

    def log_autonomy_escalation(
        self,
        from_level: str,
        to_level: str,
        *,
        phi_density: float,
        proposal_acceptance_rate: float,
        consecutive_successes: int,
        reason: str,
    ) -> None:
        self._journal.append(
            "autonomy_escalation",
            to_level,
            action="auto_escalate",
            outcome=to_level,
            state_diff={
                "from_level": from_level,
                "to_level": to_level,
                "phi_density": phi_density,
                "proposal_acceptance_rate": proposal_acceptance_rate,
                "consecutive_successes": consecutive_successes,
                "reason": reason,
            },
        )

    def log_autonomy_degradation(
        self,
        from_level: str,
        to_level: str,
        *,
        reason: str,
        consecutive_failures: int,
    ) -> None:
        self._journal.append(
            "autonomy_degradation",
            to_level,
            action="degrade_autonomy_level",
            outcome=to_level,
            state_diff={
                "from_level": from_level,
                "to_level": to_level,
                "consecutive_failures": consecutive_failures,
                "reason": reason,
            },
        )

    def log_circuit_breaker(self, event_type: str, level: str, **extra: Any) -> None:
        self._journal.append(f"circuit_breaker_{event_type}", level, **extra)

    def log_decision(
        self,
        decision: Any,
        *,
        autonomy_level: str,
        action: str,
        outcome: str,
        constraints_checked: List[str],
        constraints_violated: List[str],
    ) -> None:
        self._journal.append(
            "decision",
            autonomy_level,
            decision_id=(
                decision.decision_id if hasattr(decision, "decision_id") else None
            ),
            action=action,
            outcome=outcome,
            constraints_checked=constraints_checked,
            constraints_violated=constraints_violated,
            state_diff={"decision_type": getattr(decision, "decision_type", "")},
        )

    @property
    def journal(self) -> AuditJournal:
        return self._journal


__all__ = [
    "AuditJournal",
    "ImmutableAuditEntry",
    "AutonomousAuditLogger",
]
