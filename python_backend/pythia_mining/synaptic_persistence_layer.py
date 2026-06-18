"""
Synaptic Persistence Layer - Neural Plasticity for PYTHIA Mining.

ELEVATED PURPOSE: This module implements Hebbian learning in the mining loop,
creating a Synaptic Persistence Layer where nonces that "fire together" (lead to
accepted shares) "wire together" (strengthen their connection in the latent space).

CONSTRUCTOR THEORY FRAMEWORK: Per David Deutsch's Constructor Theory, this module
does not "engineer intelligence" but provides a substrate where emergent patterns
can self-reinforce. The system learns which mathematical resonances (φ) consistently
lead to accepted shares and automatically reinforces those pathways.

HEBBIAN LEARNING PRINCIPLE: "Cells that fire together, wire together."
- When a nonce pattern leads to an accepted share, strengthen its synaptic weight
- When nonce patterns co-occur in successful shares, strengthen their mutual connection
- Over time, successful pathways emerge as high-weight routes through the latent space
- This is not programmed behavior - it's emergent self-organization

INSEPARABILITY: The Synaptic Persistence Layer bridges the physical mining act
(pythia_mining) and the internal model (consciousness_engine). Nonces leave traces
in the ConsciousnessEngine, making the two layers inseparable over time.

Claim boundary:
This module implements deterministic Hebbian learning rules. It does not claim
consciousness or subjective experience. The learning is mathematical reinforcement
of successful pathways, not cognitive understanding.
"""

from __future__ import annotations

import math
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
from numpy.typing import NDArray


PHI = (1.0 + 5.0 ** 0.5) / 2.0
PHI_INV = 1.0 / PHI
DEFAULT_LEARNING_RATE = 0.1
DEFAULT_DECAY_RATE = 0.01
SYNAPTIC_THRESHOLD = 0.5


@dataclass(frozen=True)
class NoncePattern:
    """A fingerprint of nonce structure that can be tracked for learning."""
    
    nonce: int
    phi_resonance: float
    dodecahedral_sector: int
    icosahedral_face: int
    golden_angle_alignment: float
    timestamp: float = field(default_factory=time.time)
    
    def to_vector(self) -> NDArray[np.float64]:
        """Convert pattern to feature vector for synaptic processing."""
        return np.array([
            float(self.nonce & 0xFFFF) / 65535.0,  # Lower 16 bits normalized
            float((self.nonce >> 16) & 0xFFFF) / 65535.0,  # Upper 16 bits normalized
            self.phi_resonance,
            float(self.dodecahedral_sector) / 32.0,
            float(self.icosahedral_face) / 20.0,
            self.golden_angle_alignment,
        ], dtype=np.float64)


@dataclass(frozen=True)
class SynapticTrace:
    """A trace left in the ConsciousnessEngine by nonce activity."""
    
    pattern: NoncePattern
    synaptic_weight: float
    co_activation_patterns: Set[int]  # IDs of patterns that co-activated
    reinforcement_count: int
    last_reinforced: float
    
    def decay(self, decay_rate: float) -> "SynapticTrace":
        """Apply exponential decay to synaptic weight."""
        decayed_weight = self.synaptic_weight * math.exp(-decay_rate)
        return SynapticTrace(
            pattern=self.pattern,
            synaptic_weight=decayed_weight,
            co_activation_patterns=self.co_activation_patterns.copy(),
            reinforcement_count=self.reinforcement_count,
            last_reinforced=self.last_reinforced,
        )


@dataclass(frozen=True)
class HebbianLearningEvent:
    """A Hebbian learning event from share acceptance."""
    
    timestamp: float
    pattern_id: int
    co_active_patterns: List[int]
    reinforcement_delta: float
    phi_correlation: float
    description: str


class SynapticPersistenceLayer:
    """
    Synaptic Persistence Layer implementing Hebbian learning in the mining loop.
    
    ELEVATED: This is not a programmed optimizer - it's a substrate where emergent
    patterns can self-reinforce. The layer observes which nonce patterns lead to
    accepted shares and strengthens their synaptic connections automatically.
    
    The layer implements:
    1. Pattern tracking: Extract features from successful nonces
    2. Hebbian reinforcement: Strengthen patterns that lead to success
    3. Co-activation learning: Strengthen connections between co-occurring patterns
    4. Synaptic decay: Gradually weaken unused pathways
    5. Emergent pathway formation: High-weight routes emerge from self-organization
    """
    
    VERSION = "SYNAPTIC_PERSISTENCE_V1"
    
    def __init__(
        self,
        learning_rate: float = DEFAULT_LEARNING_RATE,
        decay_rate: float = DEFAULT_DECAY_RATE,
        synaptic_threshold: float = SYNAPTIC_THRESHOLD,
    ) -> None:
        self.learning_rate = learning_rate
        self.decay_rate = decay_rate
        self.synaptic_threshold = synaptic_threshold
        self.learning_rate_history: List[Tuple[float, float]] = []  # (timestamp, rate)
        self.learning_rate_history.append((time.time(), learning_rate))
        self.decay_rate_history: List[Tuple[float, float]] = []  # (timestamp, rate)
        self.decay_rate_history.append((time.time(), decay_rate))
        
        # Synaptic memory: pattern_id -> SynapticTrace
        self.synaptic_memory: Dict[int, SynapticTrace] = {}
        
        # Co-activation matrix: pattern_id -> pattern_id -> connection strength
        self.co_activation_matrix: Dict[int, Dict[int, float]] = {}
        
        # Learning history for emergence detection
        self.learning_events: List[HebbianLearningEvent] = []
        
        # Pattern counter for unique IDs
        self._pattern_counter = 0
        
        # Statistics
        self.total_reinforcements = 0
        self.total_decays = 0
        self.emergent_pathway_count = 0
    
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
    
    def register_pattern(self, pattern: NoncePattern) -> int:
        """Register a new pattern and return its ID."""
        pattern_id = self._pattern_counter
        self._pattern_counter += 1
        
        # Initialize synaptic trace
        trace = SynapticTrace(
            pattern=pattern,
            synaptic_weight=0.0,  # Start with zero weight
            co_activation_patterns=set(),
            reinforcement_count=0,
            last_reinforced=0.0,
        )
        self.synaptic_memory[pattern_id] = trace
        
        # Initialize co-activation row
        self.co_activation_matrix[pattern_id] = {}
        
        return pattern_id
    
    def reinforce_pattern(
        self,
        pattern_id: int,
        phi_correlation: float = 1.0,
        co_active_patterns: Optional[List[int]] = None,
    ) -> HebbianLearningEvent:
        """
        Apply Hebbian reinforcement to a pattern.
        
        When a pattern leads to an accepted share, strengthen its synaptic weight.
        Also strengthen connections to co-occurring patterns (Hebbian learning).
        
        Args:
            pattern_id: ID of the pattern to reinforce
            phi_correlation: How well the pattern's phi correlates with success
            co_active_patterns: IDs of patterns that co-activated with this one
        
        Returns:
            HebbianLearningEvent describing the reinforcement
        """
        if pattern_id not in self.synaptic_memory:
            raise ValueError(f"Pattern {pattern_id} not registered")
        
        current_trace = self.synaptic_memory[pattern_id]
        
        # Hebbian reinforcement: weight += learning_rate * phi_correlation
        reinforcement_delta = self.learning_rate * phi_correlation
        new_weight = current_trace.synaptic_weight + reinforcement_delta
        
        # Update co-activation patterns
        updated_co_activation = current_trace.co_activation_patterns.copy()
        if co_active_patterns:
            for co_id in co_active_patterns:
                if co_id != pattern_id and co_id in self.synaptic_memory:
                    updated_co_activation.add(co_id)
                    
                    # Strengthen bidirectional connection
                    self._strengthen_connection(pattern_id, co_id, reinforcement_delta)
                    self._strengthen_connection(co_id, pattern_id, reinforcement_delta)
        
        # Create updated trace
        updated_trace = SynapticTrace(
            pattern=current_trace.pattern,
            synaptic_weight=min(new_weight, 1.0),  # Cap at 1.0
            co_activation_patterns=updated_co_activation,
            reinforcement_count=current_trace.reinforcement_count + 1,
            last_reinforced=time.time(),
        )
        
        self.synaptic_memory[pattern_id] = updated_trace
        self.total_reinforcements += 1
        
        # Check for emergent pathway formation
        if new_weight >= self.synaptic_threshold and current_trace.synaptic_weight < self.synaptic_threshold:
            self.emergent_pathway_count += 1
        
        # Create learning event
        event = HebbianLearningEvent(
            timestamp=time.time(),
            pattern_id=pattern_id,
            co_active_patterns=list(co_active_patterns) if co_active_patterns else [],
            reinforcement_delta=reinforcement_delta,
            phi_correlation=phi_correlation,
            description=f"Hebbian reinforcement: pattern {pattern_id} weight {current_trace.synaptic_weight:.6f} -> {new_weight:.6f}"
        )
        
        self.learning_events.append(event)
        return event
    
    def _strengthen_connection(self, from_id: int, to_id: int, delta: float) -> None:
        """Strengthen synaptic connection between two patterns."""
        if from_id not in self.co_activation_matrix:
            self.co_activation_matrix[from_id] = {}
        
        current_strength = self.co_activation_matrix[from_id].get(to_id, 0.0)
        new_strength = min(current_strength + delta, 1.0)
        self.co_activation_matrix[from_id][to_id] = new_strength
    
    def apply_decay(self) -> None:
        """Apply exponential decay to all synaptic weights."""
        decayed_memory: Dict[int, SynapticTrace] = {}
        
        for pattern_id, trace in self.synaptic_memory.items():
            decayed_trace = trace.decay(self.decay_rate)
            decayed_memory[pattern_id] = decayed_trace
        
        self.synaptic_memory = decayed_memory
        self.total_decays += 1
        
        # Decay co-activation connections
        for from_id in self.co_activation_matrix:
            for to_id in self.co_activation_matrix[from_id]:
                current = self.co_activation_matrix[from_id][to_id]
                decayed = current * math.exp(-self.decay_rate)
                self.co_activation_matrix[from_id][to_id] = decayed
    
    def get_emergent_pathways(self, threshold: Optional[float] = None) -> List[Tuple[int, float]]:
        """
        Return patterns that have formed emergent pathways.
        
        Emergent pathways are patterns whose synaptic weight has exceeded
        the threshold through self-reinforcement, not programming.
        """
        effective_threshold = threshold or self.synaptic_threshold
        pathways = [
            (pattern_id, trace.synaptic_weight)
            for pattern_id, trace in self.synaptic_memory.items()
            if trace.synaptic_weight >= effective_threshold
        ]
        return sorted(pathways, key=lambda x: x[1], reverse=True)
    
    def get_pattern_similarity(self, pattern_id1: int, pattern_id2: int) -> float:
        """Compute similarity between two patterns based on co-activation strength."""
        if pattern_id1 not in self.co_activation_matrix:
            return 0.0
        if pattern_id2 not in self.co_activation_matrix[pattern_id1]:
            return 0.0
        return self.co_activation_matrix[pattern_id1][pattern_id2]
    
    def suggest_nonce_priority(
        self,
        current_nonce: int,
        phi_resonance: float,
        top_k: int = 5,
    ) -> List[Tuple[int, float]]:
        """
        Suggest nonce priorities based on emergent pathway strengths.
        
        This is where the system "enhances itself" - successful pathways
        automatically guide future nonce selection without programming.
        """
        # Create temporary pattern for current nonce
        temp_pattern = self.extract_pattern(current_nonce, phi_resonance)
        temp_vector = temp_pattern.to_vector()
        
        # Compute similarity to all stored patterns
        similarities: List[Tuple[int, float]] = []
        for pattern_id, trace in self.synaptic_memory.items():
            if trace.synaptic_weight < self.synaptic_threshold:
                continue  # Only consider emergent pathways
            
            stored_vector = trace.pattern.to_vector()
            # Cosine similarity
            similarity = float(np.dot(temp_vector, stored_vector))
            # Weight by synaptic strength
            weighted_similarity = similarity * trace.synaptic_weight
            similarities.append((pattern_id, weighted_similarity))
        
        # Return top-k most similar patterns
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Return statistics about the synaptic persistence layer."""
        pathway_weights = [trace.synaptic_weight for trace in self.synaptic_memory.values()]
        
        return {
            "version": self.VERSION,
            "total_patterns": len(self.synaptic_memory),
            "total_reinforcements": self.total_reinforcements,
            "total_decays": self.total_decays,
            "emergent_pathway_count": self.emergent_pathway_count,
            "average_synaptic_weight": float(np.mean(pathway_weights)) if pathway_weights else 0.0,
            "max_synaptic_weight": float(np.max(pathway_weights)) if pathway_weights else 0.0,
            "learning_events_count": len(self.learning_events),
            "co_activation_connections": sum(
                len(conns) for conns in self.co_activation_matrix.values()
            ),
        }
    
    def adjust_learning_rate(self, new_rate: float, reason: str = "") -> None:
        """Adjust the learning rate based on emergence signals.
        
        ELEVATED: This allows the Reflexive Controller (Gardener) to adjust
        learning parameters based on detected autopoiesis events. When the
        system self-organizes, learning rate adapts to support emergence.
        
        Args:
            new_rate: New learning rate (should be positive and reasonable)
            reason: Description of why the adjustment was made
        """
        old_rate = self.learning_rate
        self.learning_rate = max(0.001, min(1.0, new_rate))  # Bound to reasonable range
        self.learning_rate_history.append((time.time(), self.learning_rate))
        
        # Log the adjustment as a learning event
        event = HebbianLearningEvent(
            timestamp=time.time(),
            pattern_id=-1,  # System-level adjustment, not pattern-specific
            co_active_patterns=[],
            reinforcement_delta=self.learning_rate - old_rate,
            phi_correlation=0.0,
            description=f"Learning rate adjusted: {old_rate:.6f} -> {self.learning_rate:.6f}. Reason: {reason}",
        )
        self.learning_events.append(event)
    
    def get_learning_rate_history(self) -> List[Tuple[float, float]]:
        """Return history of learning rate adjustments."""
        return self.learning_rate_history.copy()
    
    def adjust_decay_rate(self, new_rate: float, reason: str = "") -> None:
        """Adjust the decay rate based on structural coupling signals.
        
        ELEVATED: This allows the Reflexive Controller (Gardener) to adjust
        decay parameters based on structural coupling. High coupling indicates
        successful emergence → decrease decay to preserve pathways. Low coupling
        indicates weak emergence → increase decay to prevent calcification.
        
        Args:
            new_rate: New decay rate (should be positive and reasonable)
            reason: Description of why the adjustment was made
        """
        old_rate = self.decay_rate
        self.decay_rate = max(0.001, min(0.5, new_rate))  # Bound to reasonable range
        self.decay_rate_history.append((time.time(), self.decay_rate))
        
        # Log the adjustment as a learning event
        event = HebbianLearningEvent(
            timestamp=time.time(),
            pattern_id=-1,  # System-level adjustment, not pattern-specific
            co_active_patterns=[],
            reinforcement_delta=self.decay_rate - old_rate,
            phi_correlation=0.0,
            description=f"Decay rate adjusted: {old_rate:.6f} -> {self.decay_rate:.6f}. Reason: {reason}",
        )
        self.learning_events.append(event)
    
    def get_decay_rate_history(self) -> List[Tuple[float, float]]:
        """Return history of decay rate adjustments."""
        return self.decay_rate_history.copy()
    
    def export_state(self) -> Dict[str, Any]:
        """Export synaptic state for persistence or analysis."""
        return {
            "version": self.VERSION,
            "learning_rate": self.learning_rate,
            "decay_rate": self.decay_rate,
            "synaptic_threshold": self.synaptic_threshold,
            "synaptic_memory": {
                str(pid): asdict(trace) for pid, trace in self.synaptic_memory.items()
            },
            "co_activation_matrix": self.co_activation_matrix,
            "statistics": self.get_statistics(),
            "learning_rate_history": self.learning_rate_history,
        }


__all__ = [
    "DEFAULT_DECAY_RATE",
    "DEFAULT_LEARNING_RATE",
    "HebbianLearningEvent",
    "NoncePattern",
    "SYNAPTIC_THRESHOLD",
    "SynapticPersistenceLayer",
    "SynapticTrace",
]
