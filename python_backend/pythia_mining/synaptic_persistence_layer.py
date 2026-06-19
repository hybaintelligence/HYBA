"""Synaptic persistence layer — Hebbian learning from nonce/share patterns."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

PHI = 1.618033988749895
logger = logging.getLogger(__name__)

VERSION = "SYNAPTIC_PERSISTENCE_V1"


def _sector_pattern_key(dodecahedral_sector: int, phi_resonance: float) -> str:
    return f"s{dodecahedral_sector}_p{phi_resonance:.1f}"


@dataclass
class NoncePattern:
    """A fingerprint of nonce structure that can be tracked for learning."""
    nonce: int
    phi_resonance: float
    dodecahedral_sector: int = 0
    icosahedral_face: int = 0
    golden_angle_alignment: float = 0.0

    def to_vector(self) -> np.ndarray:
        """Convert pattern to feature vector for synaptic processing."""
        return np.array([
            (self.nonce & 0xFFFF) / 65535.0,
            ((self.nonce >> 16) & 0xFFFF) / 65535.0,
            self.phi_resonance,
            self.dodecahedral_sector / 32.0,
            self.icosahedral_face / 20.0,
            self.golden_angle_alignment,
        ], dtype=float)


@dataclass
class SynapticTrace:
    """A trace left in the ConsciousnessEngine by nonce activity."""
    pattern: NoncePattern
    synaptic_weight: float = 0.0
    reinforcement_count: int = 0
    connections: Dict[int, float] = field(default_factory=dict)

    def decay(self, decay_rate: float) -> None:
        """Apply exponential decay to synaptic weight."""
        self.synaptic_weight *= (1.0 - decay_rate)


@dataclass
class HebbianLearningEvent:
    """A Hebbian learning event from share acceptance."""
    timestamp: float
    pattern_id: int
    reinforcement_delta: float
    phi_correlation: float
    co_active_patterns: List[int] = field(default_factory=list)
    description: str = ""


class SynapticPersistenceLayer:
    """Hebbian learning layer — nonces that fire together wire together."""

    VERSION = VERSION

    def __init__(
        self,
        learning_rate: float = 0.1,
        decay_rate: float = 0.01,
        synaptic_threshold: float = 0.5,
    ) -> None:
        self.learning_rate = learning_rate
        self.decay_rate = decay_rate
        self.synaptic_threshold = synaptic_threshold
        self.synaptic_memory: Dict[int, SynapticTrace] = {}
        self._next_id: int = 0
        self._learning_rate_history: List[Tuple[float, float, str]] = []
        self._decay_rate_history: List[Tuple[float, float, str]] = []
        self._total_decays: int = 0

    def extract_pattern(
        self,
        nonce: int,
        phi_resonance: float,
        dodecahedral_sector: int = 0,
        icosahedral_face: int = 0,
        golden_angle_alignment: float = 0.0,
    ) -> NoncePattern:
        """Extract a learnable pattern from a nonce and its context."""
        return NoncePattern(
            nonce=nonce,
            phi_resonance=phi_resonance,
            dodecahedral_sector=dodecahedral_sector,
            icosahedral_face=icosahedral_face,
            golden_angle_alignment=golden_angle_alignment,
        )

    def register_or_reinforce(
        self,
        nonce: int,
        phi_resonance: float,
        dodecahedral_sector: int = 0,
        icosahedral_face: int = 0,
        golden_angle_alignment: float = 0.0,
    ) -> int:
        key = nonce % 2_147_483_648
        for pid, trace in self.synaptic_memory.items():
            if trace.pattern.nonce == key:
                trace.synaptic_weight = min(1.0, trace.synaptic_weight + self.learning_rate)
                trace.reinforcement_count += 1
                return pid
        pattern = self.extract_pattern(
            nonce, phi_resonance, dodecahedral_sector, icosahedral_face, golden_angle_alignment
        )
        return self.register_pattern(pattern)

    def register_pattern(self, pattern: NoncePattern) -> int:
        """Register a new pattern and return its ID."""
        pid = self._next_id
        self._next_id += 1
        self.synaptic_memory[pid] = SynapticTrace(
            pattern=pattern, synaptic_weight=0.0, reinforcement_count=0
        )
        return pid

    def reinforce_pattern(
        self,
        pattern_id: int,
        phi_correlation: float = 1.0,
        co_active_patterns: Optional[List[int]] = None,
    ) -> HebbianLearningEvent:
        """Hebbian reinforcement: pattern weight strengthened on share acceptance."""
        if pattern_id not in self.synaptic_memory:
            raise KeyError(f"Pattern {pattern_id} not registered")
        trace = self.synaptic_memory[pattern_id]
        delta = self.learning_rate * phi_correlation
        old_weight = trace.synaptic_weight
        trace.synaptic_weight = min(1.0, trace.synaptic_weight + delta)
        trace.reinforcement_count += 1
        logger.debug(
            f"Hebbian reinforcement: pattern {pattern_id} weight "
            f"{old_weight:.6f} -> {trace.synaptic_weight:.6f}"
        )
        for co_id in (co_active_patterns or []):
            self._strengthen_connection(pattern_id, co_id, delta * 0.5)
        return HebbianLearningEvent(
            timestamp=time.time(),
            pattern_id=pattern_id,
            reinforcement_delta=delta,
            phi_correlation=phi_correlation,
            co_active_patterns=list(co_active_patterns or []),
            description=f"Reinforced pattern {pattern_id}",
        )

    def _strengthen_connection(self, from_id: int, to_id: int, delta: float) -> None:
        """Strengthen synaptic connection between two patterns."""
        if from_id in self.synaptic_memory:
            conns = self.synaptic_memory[from_id].connections
            conns[to_id] = min(1.0, conns.get(to_id, 0.0) + delta)

    def apply_decay(self) -> None:
        """Apply exponential decay to all synaptic weights."""
        for trace in self.synaptic_memory.values():
            trace.decay(self.decay_rate)
        self._total_decays += 1

    def get_emergent_pathways(self, threshold: Optional[float] = None) -> List[Tuple[int, float]]:
        t = threshold if threshold is not None else self.synaptic_threshold
        return sorted(
            [(pid, tr.synaptic_weight) for pid, tr in self.synaptic_memory.items()
             if tr.synaptic_weight >= t],
            key=lambda x: x[1], reverse=True,
        )

    def get_pattern_similarity(self, pattern_id1: int, pattern_id2: int) -> float:
        """Compute similarity between two patterns based on co-activation strength."""
        if pattern_id1 not in self.synaptic_memory or pattern_id2 not in self.synaptic_memory:
            return 0.0
        conns = self.synaptic_memory[pattern_id1].connections
        return conns.get(pattern_id2, 0.0)

    def suggest_nonce_priority(
        self, current_nonce: int, phi_resonance: float, top_k: int = 5
    ) -> List[Tuple[int, float]]:
        if not self.synaptic_memory:
            return []
        current_vec = NoncePattern(
            nonce=current_nonce, phi_resonance=phi_resonance
        ).to_vector()
        scored = []
        for pid, trace in self.synaptic_memory.items():
            v = trace.pattern.to_vector()
            dot = float(np.dot(current_vec, v))
            norm = float(np.linalg.norm(current_vec) * np.linalg.norm(v))
            sim = dot / max(norm, 1e-9) * trace.synaptic_weight
            scored.append((pid, sim))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def get_statistics(self) -> dict:
        """Return statistics about the synaptic persistence layer."""
        weights = [tr.synaptic_weight for tr in self.synaptic_memory.values()]
        return {
            "total_patterns": len(self.synaptic_memory),
            "average_synaptic_weight": float(np.mean(weights)) if weights else 0.0,
            "max_synaptic_weight": float(max(weights)) if weights else 0.0,
            "emergent_pathways_count": len(self.get_emergent_pathways()),
            "total_decays": self._total_decays,
            "learning_rate": self.learning_rate,
            "decay_rate": self.decay_rate,
            "synaptic_threshold": self.synaptic_threshold,
        }

    def adjust_learning_rate(self, new_rate: float, reason: str = "") -> None:
        """Learning rate adjusted."""
        new_rate = max(0.001, min(1.0, new_rate))
        old = self.learning_rate
        self._learning_rate_history.append((time.time(), old, reason))
        if len(self._learning_rate_history) > 100:
            self._learning_rate_history = self._learning_rate_history[-100:]
        self.learning_rate = new_rate

    def get_learning_rate_history(self) -> List[Tuple[float, float, str]]:
        return list(self._learning_rate_history)

    def adjust_decay_rate(self, new_rate: float, reason: str = "") -> None:
        """Decay rate adjusted."""
        new_rate = max(0.001, min(0.5, new_rate))
        old = self.decay_rate
        self._decay_rate_history.append((time.time(), old, reason))
        if len(self._decay_rate_history) > 100:
            self._decay_rate_history = self._decay_rate_history[-100:]
        self.decay_rate = new_rate

    def get_decay_rate_history(self) -> List[Tuple[float, float, str]]:
        return list(self._decay_rate_history)

    def export_state(self) -> dict:
        """Export synaptic state for persistence or analysis."""
        return {
            "version": self.VERSION,
            "learning_rate": self.learning_rate,
            "decay_rate": self.decay_rate,
            "synaptic_threshold": self.synaptic_threshold,
            "total_patterns": len(self.synaptic_memory),
            "total_decays": self._total_decays,
            "patterns": [
                {"pattern_id": pid, "synaptic_weight": tr.synaptic_weight,
                 "reinforcement_count": tr.reinforcement_count,
                 "nonce": tr.pattern.nonce, "phi_resonance": tr.pattern.phi_resonance}
                for pid, tr in self.synaptic_memory.items()
            ],
        }
