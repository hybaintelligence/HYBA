"""PYTHIA One Block Mission Memory.

This module encodes the mission memory that PYTHIA wakes with: the full quantum
search doctrine, pool selection policy, hashrate limits, and completion condition.

Mission: one_pool_confirmed_block_then_shutdown

The mission memory is seeded at startup and governs:
- Autonomy from startup (no human intervention required)
- Default pool selection by validated priority
- 1 EH/s hashrate limit enforcement
- Distinction between accepted share (learning) and accepted block (completion)
- Shutdown after one pool-confirmed accepted block
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Mission constants
MAX_AUTONOMOUS_HASHRATE_EHS = 1.0  # Hard limit: 1 EH/s
MISSION_PROTOCOL = "PYTHIA_ONE_BLOCK_MISSION_MEMORY_V1"
PHI_CONTRACT_VERSION = "PHI_CONTRACT_V1"


class MissionStatus(str, Enum):
    """Lifecycle status of the one-block mission."""

    SEEDED = "seeded"
    SEARCHING = "searching"
    LEARNING = "learning"  # Accepted share received, continue mining
    COMPLETED = "completed"  # Pool-confirmed accepted block, shutdown
    ABORTED = "aborted"  # Mission aborted due to error or limit violation


@dataclass(frozen=True)
class SessionIntention:
    """Operator-declared search intention that locks PYTHIA onto a deterministic manifold."""

    mode: str = "AUTONOMOUS"
    pool: str = "ViaBTC"
    eh_limit: float = MAX_AUTONOMOUS_HASHRATE_EHS
    objective: str = "phi_dense_candidate_clusters"
    constraints: Dict[str, Any] = field(default_factory=lambda: {
        "governance": True,
        "operator_approval_required": True,
        "max_entropy_sources": ["job_stream", "local_prng"],
    })
    telemetry_contract: Dict[str, Any] = field(default_factory=lambda: {
        "min_phi_density": 0.70,
        "max_entropy_drift": 0.25,
        "expected_rejection_profile": "hash_above_target-dominant",
    })


@dataclass(frozen=True)
class PhiContract:
    """Active phi-contract that governs search behaviour."""

    status: str = "ACTIVE"
    phi_density_floor: float = 0.70
    entropy_drift_limit: float = 0.25
    coverage_envelope: str = "stratified"
    solver_heuristics_required: Tuple[str, ...] = (
        "pulvini_compression",
        "hendrix_structured_traversal",
        "sha256d_final_oracle",
    )

    def check_telemetry(self, phi_density: float, entropy_drift: float) -> str:
        """Return CONTINUE, RESEED_MANIFOLD, or PAUSE_AND_REPORT."""
        if phi_density < self.phi_density_floor:
            return "RESEED_MANIFOLD"
        if entropy_drift > self.entropy_drift_limit:
            return "PAUSE_AND_REPORT"
        return "CONTINUE"


class ShareOutcome(str, Enum):
    """Classification of pool responses."""

    ACCEPTED_SHARE = "accepted_share"  # Learning event, continue mission
    ACCEPTED_BLOCK = "accepted_block"  # Mission completion condition
    REJECTED = "rejected"  # Learning event, continue mission
    STALE = "stale"  # Learning event, continue mission


@dataclass(frozen=True)
class MissionTarget:
    """The completion condition for the one-block mission."""

    accepted_blocks: int = 1
    pool_side_confirmation_required: bool = True
    shutdown_after_completion: bool = True

    def is_complete(self, accepted_block_count: int) -> bool:
        """Check if mission is complete."""
        return accepted_block_count >= self.accepted_blocks


@dataclass(frozen=True)
class HashrateLimit:
    """Hashrate enforcement boundary."""

    max_autonomous_hashrate_ehs: float = MAX_AUTONOMOUS_HASHRATE_EHS
    enforcement_mode: str = "hard_limit"  # hard_limit, soft_warning, advisory

    def is_violated(self, current_hashrate_ehs: float) -> bool:
        """Check if current hashrate exceeds limit."""
        return current_hashrate_ehs > self.max_autonomous_hashrate_ehs

    def safe_hashrate(self, requested_hashrate_ehs: float) -> float:
        """Clamp hashrate to safe limit."""
        return min(requested_hashrate_ehs, self.max_autonomous_hashrate_ehs)


@dataclass(frozen=True)
class QuantumDoctrine:
    """The quantum search doctrine that guides PYTHIA's search behavior."""

    quantum_doctrine: Tuple[str, ...] = (
        "quantum mathematics first",
        "substrate-independent execution",
        "golden-ratio computational grammar",
        "1000-site qubit-formalism tensor prior",
        "PULVINI reversible compression with retained kernels",
        "HENDRIX-Φ structured traversal",
        "Deutschian criticism from pool outcomes",
    )

    structure_targets: Tuple[str, ...] = (
        "block height",
        "difficulty and target pressure",
        "retarget epoch phase",
        "historical nonce resonance",
        "dodecahedral domains",
        "icosahedral faces",
        "mass-gap valleys",
        "entanglement spectrum",
        "large nonce gaps",
        "sector coverage",
        "golden-angle alignment",
        "birthday echoes",
        "Phi^15 as one lane among many",
    )

    search_workflow: Tuple[str, ...] = (
        "read current chain context",
        "load empirical structure packet",
        "rank dodecahedral and icosahedral priority surfaces",
        "compress active search with PULVINI retained kernels",
        "collapse priority surface into bounded solver ranges",
        "verify every candidate with exact SHA-256d",
        "submit verifier-passing candidate to configured pool",
        "feed accepted/rejected pool result into Deutsch memory",
        "stop immediately after one pool-confirmed accepted block",
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quantum_doctrine": list(self.quantum_doctrine),
            "structure_targets": list(self.structure_targets),
            "search_workflow": list(self.search_workflow),
        }


@dataclass(frozen=True)
class SupremeInvariants:
    """Non-negotiable invariants that govern all mission behavior."""

    invariants: Tuple[str, ...] = (
        "blockchain security above all else",
        "exact SHA-256d final oracle",
        "full nonce coverage preserved",
        "no success state without pool-side confirmation",
        "accepted shares are learning events",
        "accepted block proof is mission completion",
    )


@dataclass(frozen=True)
class PoolSelectionPolicy:
    """Policy for selecting the default pool at startup."""

    policy: str = "select first validated configured pool ordered by priority"
    require_validated_profile: bool = True
    fallback_to_environment: bool = False  # If no validated profile, fail rather than fallback


@dataclass
class MissionMemory:
    """The complete mission memory that PYTHIA wakes with."""

    protocol: str = MISSION_PROTOCOL
    mission: str = "one_pool_confirmed_block_then_shutdown"
    autonomy_from_startup: bool = True
    default_pool_policy: str = "select first validated configured pool ordered by priority"
    mission_target: MissionTarget = field(default_factory=MissionTarget)
    search_identity: str = "deterministic structured traversal, not blind brute force"
    knowledge_seed: QuantumDoctrine = field(default_factory=QuantumDoctrine)
    supreme_invariants: SupremeInvariants = field(default_factory=SupremeInvariants)
    pool_selection_policy: PoolSelectionPolicy = field(default_factory=PoolSelectionPolicy)
    hashrate_limit: HashrateLimit = field(default_factory=HashrateLimit)
    intention: SessionIntention = field(default_factory=SessionIntention)
    phi_contract: PhiContract = field(default_factory=PhiContract)
    seed_vector: Optional[str] = None
    operator_session_id: Optional[str] = None

    # Runtime state (not frozen)
    status: MissionStatus = MissionStatus.SEEDED
    accepted_shares: int = 0
    accepted_blocks: int = 0
    rejected_shares: int = 0
    stale_shares: int = 0
    mission_start_time: float = field(default_factory=time.time)
    mission_complete_time: Optional[float] = None
    last_share_time: Optional[float] = None

    def record_share_outcome(self, outcome: ShareOutcome) -> None:
        """Record a pool share outcome and update mission status."""
        self.last_share_time = time.time()

        if outcome == ShareOutcome.ACCEPTED_SHARE:
            self.accepted_shares += 1
            self.status = MissionStatus.LEARNING
        elif outcome == ShareOutcome.ACCEPTED_BLOCK:
            self.accepted_blocks += 1
            self.status = MissionStatus.COMPLETED
            self.mission_complete_time = time.time()
        elif outcome == ShareOutcome.REJECTED:
            self.rejected_shares += 1
            self.status = MissionStatus.SEARCHING
        elif outcome == ShareOutcome.STALE:
            self.stale_shares += 1
            self.status = MissionStatus.SEARCHING

    def is_complete(self) -> bool:
        """Check if mission is complete."""
        return self.mission_target.is_complete(self.accepted_blocks)

    def should_shutdown(self) -> bool:
        """Check if mission should shutdown."""
        return (
            self.status == MissionStatus.COMPLETED
            and self.mission_target.shutdown_after_completion
        )

    def compute_deterministic_seed(self, operator_session_id: str, initial_job_id: str) -> str:
        """Compute a deterministic seed vector from governance-relevant inputs."""
        seed_material = (
            self.intention.mode
            + self.intention.pool
            + str(self.intention.eh_limit)
            + PHI_CONTRACT_VERSION
            + operator_session_id
            + initial_job_id
            + str(self.mission_start_time)
        )
        digest = hashlib.sha256(seed_material.encode("utf-8")).hexdigest()
        self.seed_vector = digest
        self.operator_session_id = operator_session_id
        return digest

    def enforce_hashrate_limit(self, current_hashrate_ehs: float) -> float:
        """Enforce hashrate limit and return safe hashrate."""
        if self.hashrate_limit.is_violated(current_hashrate_ehs):
            # Log violation (in production, this would trigger alert)
            pass
        return self.hashrate_limit.safe_hashrate(current_hashrate_ehs)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize mission memory to dictionary."""
        return {
            "protocol": self.protocol,
            "mission": self.mission,
            "autonomy_from_startup": self.autonomy_from_startup,
            "default_pool_policy": self.default_pool_policy,
            "mission_target": asdict(self.mission_target),
            "search_identity": self.search_identity,
            "knowledge_seed": self.knowledge_seed.to_dict(),
            "supreme_invariants": list(self.supreme_invariants.invariants),
            "pool_selection_policy": asdict(self.pool_selection_policy),
            "hashrate_limit": asdict(self.hashrate_limit),
            "intention": asdict(self.intention),
            "phi_contract": asdict(self.phi_contract),
            "seed_vector": self.seed_vector,
            "operator_session_id": self.operator_session_id,
            "runtime_state": {
                "status": self.status.value,
                "accepted_shares": self.accepted_shares,
                "accepted_blocks": self.accepted_blocks,
                "rejected_shares": self.rejected_shares,
                "stale_shares": self.stale_shares,
                "mission_start_time": self.mission_start_time,
                "mission_complete_time": self.mission_complete_time,
                "last_share_time": self.last_share_time,
                "is_complete": self.is_complete(),
                "should_shutdown": self.should_shutdown(),
            },
        }

    def to_json(self) -> str:
        """Serialize mission memory to JSON."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True, default=str)


def seed_mission_memory(operator_session_id: str = "operator-live-default", initial_job_id: str = "genesis") -> MissionMemory:
    """Seed PYTHIA with the canonical one-block mission memory and deterministic state."""
    memory = MissionMemory()
    memory.compute_deterministic_seed(
        operator_session_id=operator_session_id,
        initial_job_id=initial_job_id,
    )
    return memory


def validate_mission_memory(memory: MissionMemory) -> bool:
    """Validate that mission memory is correctly seeded with deterministic constraints."""
    base_checks = [
        memory.protocol == MISSION_PROTOCOL,
        memory.mission == "one_pool_confirmed_block_then_shutdown",
        memory.autonomy_from_startup is True,
        memory.hashrate_limit.max_autonomous_hashrate_ehs == MAX_AUTONOMOUS_HASHRATE_EHS,
        memory.mission_target.accepted_blocks == 1,
        memory.mission_target.pool_side_confirmation_required is True,
        memory.mission_target.shutdown_after_completion is True,
        len(memory.knowledge_seed.quantum_doctrine) > 0,
        len(memory.knowledge_seed.structure_targets) > 0,
        len(memory.knowledge_seed.search_workflow) > 0,
        len(memory.supreme_invariants.invariants) > 0,
        memory.seed_vector is not None,
        memory.operator_session_id is not None,
        memory.intention is not None,
        memory.phi_contract.status == "ACTIVE",
    ]
    return all(base_checks)


__all__ = [
    "MISSION_PROTOCOL",
    "MAX_AUTONOMOUS_HASHRATE_EHS",
    "PHI_CONTRACT_VERSION",
    "MissionMemory",
    "MissionStatus",
    "MissionTarget",
    "ShareOutcome",
    "HashrateLimit",
    "QuantumDoctrine",
    "SupremeInvariants",
    "PoolSelectionPolicy",
    "SessionIntention",
    "PhiContract",
    "seed_mission_memory",
    "validate_mission_memory",
]
