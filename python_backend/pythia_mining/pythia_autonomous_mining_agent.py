"""PYTHIA-owned autonomous mining lifecycle.

This module implements the concrete autonomous mining layer requested by the
structured-search doctrine.  It does not rename brute force as quantum search:
PYTHIA owns the lifecycle, turns empirical blockchain structure into a bounded
search prior, modulates requested hashpower, records persistent memory/audit
state, and keeps final acceptance behind exact share validation.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional, Protocol

from .blockchain_structure_intelligence import PythiaStructureIntelligencePacket


@dataclass(frozen=True)
class MiningChainState:
    """Current blockchain/pool facts consumed by PYTHIA."""

    block_height: int
    pool_difficulty: float
    target: int
    nonce_ranges: tuple[tuple[int, int], ...]
    job_id: Optional[str] = None
    extranonce2: str = "00000000"


@dataclass(frozen=True)
class PythiaSearchSeed:
    """Auditable seed derived from repo, evidence, and chain state."""

    digest: str
    source: str
    created_at: float


@dataclass(frozen=True)
class PythiaMiningPlan:
    """One autonomous mining plan produced by PYTHIA."""

    seed_digest: str
    block_height: int
    pool_difficulty: float
    target: int
    requested_hashrate_ehs: float
    candidate_order: tuple[int, ...]
    search_mode: str = "pythia_structured_autonomous_search"
    grover_amplification_enabled: bool = False
    directives: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PythiaMiningObservation:
    """Outcome of executing one autonomous plan."""

    nonce: Optional[int]
    hash_value: Optional[int]
    accepted: bool
    submitted: bool
    attempts: int
    reason: str
    block_height: int
    requested_hashrate_ehs: float
    elapsed_ms: float


class HashVerifier(Protocol):
    """Protocol for exact PoW validation over a candidate nonce."""

    def __call__(self, nonce: int, chain_state: MiningChainState) -> int:
        """Return the integer hash for ``nonce`` under ``chain_state``."""


class ShareSubmitter(Protocol):
    """Protocol for governed pool/share submission."""

    def __call__(self, nonce: int, hash_value: int, chain_state: MiningChainState) -> bool:
        """Submit a verified share and return whether the pool accepted it."""


class PythiaPersistentMiningMemory:
    """Small JSON-backed memory surface for autonomous PYTHIA mining."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else None
        self.void_nonces: set[int] = set()
        self.accepted_nonces: list[int] = []
        self.audit_events: list[dict[str, Any]] = []
        if self.path is not None and self.path.exists():
            self._load()

    def remember_void(self, nonce: int) -> None:
        self.void_nonces.add(int(nonce))

    def remember_acceptance(self, nonce: int) -> None:
        self.accepted_nonces.append(int(nonce))

    def record_event(self, event_type: str, payload: Mapping[str, Any]) -> None:
        event = {
            "event_type": event_type,
            "timestamp": time.time(),
            "payload": dict(payload),
        }
        self.audit_events.append(event)
        self.flush()

    def flush(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.as_dict(), indent=2, sort_keys=True), encoding="utf-8"
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "void_nonces": sorted(self.void_nonces),
            "accepted_nonces": list(self.accepted_nonces),
            "audit_events": list(self.audit_events),
        }

    def _load(self) -> None:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        self.void_nonces = {int(n) for n in payload.get("void_nonces", [])}
        self.accepted_nonces = [int(n) for n in payload.get("accepted_nonces", [])]
        self.audit_events = list(payload.get("audit_events", []))


class PythiaAutonomousMiningAgent:
    """PYTHIA-controlled autonomous miner over a structured nonce manifold.

    The agent has the architecture requested by the mining directive:
    persistent memory, auditability, block-height/pool-difficulty awareness,
    dynamic hashrate modulation, Dodecahedron+Icosahedron lane planning, and a
    submission pipeline.  Exact hash verification remains the acceptance oracle.
    """

    FACE_COUNT = 32
    MAX_AUTONOMOUS_HASHRATE_EHS = 1.0

    def __init__(
        self,
        *,
        repo_structure: Mapping[str, Any],
        memory: PythiaPersistentMiningMemory | None = None,
        structure_packet: PythiaStructureIntelligencePacket | None = None,
        hash_verifier: HashVerifier | None = None,
        share_submitter: ShareSubmitter | None = None,
    ) -> None:
        self.repo_structure = dict(repo_structure)
        self.memory = memory or PythiaPersistentMiningMemory()
        self.structure_packet = structure_packet
        self.hash_verifier = hash_verifier or self._default_hash_verifier
        self.share_submitter = share_submitter
        self._adjacency = self._build_dodecahedron_icosahedron_adjacency()

    def initialize_seed(self, chain_state: MiningChainState) -> PythiaSearchSeed:
        """Derive a reproducible seed from repo complexity and chain facts."""
        evidence_hash = self.structure_packet.packet_hash if self.structure_packet else "no_packet"
        material = json.dumps(
            {
                "repo": self.repo_structure,
                "height": chain_state.block_height,
                "difficulty": chain_state.pool_difficulty,
                "target": chain_state.target,
                "ranges": chain_state.nonce_ranges,
                "evidence": evidence_hash,
            },
            sort_keys=True,
            default=str,
        )
        digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
        seed = PythiaSearchSeed(
            digest=digest, source="repo_chain_evidence", created_at=time.time()
        )
        self.memory.record_event("pythia_seed_initialized", asdict(seed))
        return seed

    def build_plan(
        self,
        chain_state: MiningChainState,
        *,
        max_candidates: int = 1024,
        requested_hashrate_ehs: float | None = None,
    ) -> PythiaMiningPlan:
        """Let PYTHIA choose the next structured mining plan."""
        seed = self.initialize_seed(chain_state)
        target_hashrate = self._modulate_hashrate(chain_state, requested_hashrate_ehs)
        candidates = self._candidate_order(chain_state, seed.digest, max_candidates)
        directives = (
            self.structure_packet.pythia_directives if self.structure_packet is not None else {}
        )
        plan = PythiaMiningPlan(
            seed_digest=seed.digest,
            block_height=chain_state.block_height,
            pool_difficulty=chain_state.pool_difficulty,
            target=chain_state.target,
            requested_hashrate_ehs=target_hashrate,
            candidate_order=tuple(candidates),
            directives=dict(directives),
        )
        self.memory.record_event("pythia_plan_built", self._plan_for_audit(plan))
        return plan

    def execute_plan(
        self,
        chain_state: MiningChainState,
        plan: PythiaMiningPlan,
    ) -> PythiaMiningObservation:
        """Execute a PYTHIA plan and optionally submit verified shares."""
        started = time.perf_counter()
        attempts = 0
        for nonce in plan.candidate_order:
            attempts += 1
            hash_value = int(self.hash_verifier(nonce, chain_state))
            if hash_value <= chain_state.target:
                submitted = False
                if self.share_submitter is not None:
                    submitted = bool(self.share_submitter(nonce, hash_value, chain_state))
                self.memory.remember_acceptance(nonce)
                observation = PythiaMiningObservation(
                    nonce=nonce,
                    hash_value=hash_value,
                    accepted=True,
                    submitted=submitted,
                    attempts=attempts,
                    reason="target_met",
                    block_height=chain_state.block_height,
                    requested_hashrate_ehs=plan.requested_hashrate_ehs,
                    elapsed_ms=(time.perf_counter() - started) * 1000.0,
                )
                self.memory.record_event("pythia_win_observed", asdict(observation))
                return observation
            self.memory.remember_void(nonce)

        observation = PythiaMiningObservation(
            nonce=None,
            hash_value=None,
            accepted=False,
            submitted=False,
            attempts=attempts,
            reason="candidate_budget_exhausted",
            block_height=chain_state.block_height,
            requested_hashrate_ehs=plan.requested_hashrate_ehs,
            elapsed_ms=(time.perf_counter() - started) * 1000.0,
        )
        self.memory.record_event("pythia_plan_exhausted", asdict(observation))
        return observation

    def run_lifecycle(
        self,
        chain_state: MiningChainState,
        *,
        max_candidates: int = 1024,
        requested_hashrate_ehs: float | None = None,
    ) -> PythiaMiningObservation:
        """Analyze, plan, modulate hashrate, execute, and submit if verified."""
        plan = self.build_plan(
            chain_state,
            max_candidates=max_candidates,
            requested_hashrate_ehs=requested_hashrate_ehs,
        )
        return self.execute_plan(chain_state, plan)

    def _candidate_order(
        self,
        chain_state: MiningChainState,
        seed_digest: str,
        max_candidates: int,
    ) -> list[int]:
        candidates = list(self._bounded_candidates(chain_state.nonce_ranges, max_candidates))
        seed_int = int(seed_digest[:16], 16)
        candidates.sort(
            key=lambda nonce: (
                -self._structured_score(nonce, chain_state, seed_int),
                nonce,
            )
        )
        return candidates

    def _structured_score(
        self, nonce: int, chain_state: MiningChainState, seed_int: int
    ) -> float:
        face = nonce % self.FACE_COUNT
        neighbor_pressure = sum(
            1 for n in self._adjacency[face] if n not in self.memory.void_nonces
        )
        target_phase = (chain_state.target % 1_000_003) / 1_000_003.0
        nonce_phase = ((nonce ^ seed_int) % 1_000_003) / 1_000_003.0
        phase_score = 1.0 - abs(target_phase - nonce_phase)
        difficulty_score = 1.0 / (
            1.0 + max(0.0, chain_state.pool_difficulty) / 1_000_000.0
        )
        evidence_score = 0.5
        if self.structure_packet is not None:
            evidence_score = float(self.structure_packet.evidence.structure_score)
        freshness = 0.0 if nonce in self.memory.void_nonces else 1.0
        return max(
            0.0,
            min(
                1.0,
                0.35 * phase_score
                + 0.20 * (neighbor_pressure / max(1, len(self._adjacency[face])))
                + 0.20 * evidence_score
                + 0.15 * freshness
                + 0.10 * difficulty_score,
            ),
        )

    def _modulate_hashrate(
        self,
        chain_state: MiningChainState,
        requested_hashrate_ehs: float | None,
    ) -> float:
        requested = 0.05 if requested_hashrate_ehs is None else float(requested_hashrate_ehs)
        difficulty_factor = min(1.0, max(0.0, chain_state.pool_difficulty / 1_000_000.0))
        evidence_factor = 0.5
        if self.structure_packet is not None:
            evidence_factor = float(self.structure_packet.evidence.structure_score)
        modulated = requested * (0.75 + 0.25 * evidence_factor + 0.25 * difficulty_factor)
        return round(min(self.MAX_AUTONOMOUS_HASHRATE_EHS, max(0.0, modulated)), 12)

    @staticmethod
    def _bounded_candidates(
        nonce_ranges: tuple[tuple[int, int], ...], max_candidates: int
    ) -> Iterable[int]:
        emitted = 0
        for start, end in nonce_ranges:
            for nonce in range(int(start), int(end) + 1):
                yield int(nonce)
                emitted += 1
                if emitted >= max_candidates:
                    return

    @classmethod
    def _build_dodecahedron_icosahedron_adjacency(cls) -> dict[int, tuple[int, ...]]:
        return {
            face: (
                (face - 1) % cls.FACE_COUNT,
                (face + 1) % cls.FACE_COUNT,
                (face + 8) % cls.FACE_COUNT,
                (face + 13) % cls.FACE_COUNT,
            )
            for face in range(cls.FACE_COUNT)
        }

    @staticmethod
    def _default_hash_verifier(nonce: int, chain_state: MiningChainState) -> int:
        material = (
            f"{chain_state.block_height}:{chain_state.job_id}:"
            f"{chain_state.extranonce2}:{nonce}"
        )
        return int(hashlib.sha256(material.encode("utf-8")).hexdigest(), 16)

    @staticmethod
    def _plan_for_audit(plan: PythiaMiningPlan) -> dict[str, Any]:
        payload = asdict(plan)
        payload["candidate_order"] = list(plan.candidate_order[:32])
        payload["candidate_count"] = len(plan.candidate_order)
        return payload


__all__ = [
    "HashVerifier",
    "MiningChainState",
    "PythiaAutonomousMiningAgent",
    "PythiaMiningObservation",
    "PythiaMiningPlan",
    "PythiaPersistentMiningMemory",
    "PythiaSearchSeed",
    "ShareSubmitter",
]
