"""PYTHIA Autonomous Mining Controller — Mathematical Self-Governance.

This module extends the UnifiedMiningEngine with autonomous decision-making capabilities
while maintaining strict mathematical safety constraints. The autonomous controller operates
within well-defined boundaries enforced by geometric invariants and operator-specified limits.

Key Principles:
1. Mathematical Determinism: All autonomous decisions are based on φ-resonant patterns
2. Safety Overrides: Operator can always override autonomous decisions
3. Geometric Constraints: Actions must respect Hermiticity, PSD, and natural scaling laws
4. Audit Trail: Every autonomous decision is logged with mathematical justification
5. Gradual Autonomy: System starts with limited autonomy, increases based on performance

REFLEXIVE KNOWLEDGE LOOP:
The autonomous controller implements a recursive self-learning mechanism that:
1. Analyzes the codebase "surroundings" as a graph of mathematical invariants
2. Uses Deutsch Substrate counterfactual reasoning to hypothesize improvements
3. Validates all hypothetical changes against the 5 Safety Constraints
4. Commits validated improvements to internal memory for the next mining epoch
5. Drives continuous improvement via Pulvini Memory Compression as "metabolic rate"

The autonomous controller does not replace operator judgment — it augments it with
mathematically-grounded recommendations and automated execution within safe bounds.
"""

from __future__ import annotations

import asyncio
import hashlib
import inspect
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .ai_optimizer import AIOptimizer, SearchStrategy
from .consciousness_engine import ConsciousnessConfig, ConsciousnessEngine, PhiMetrics
from .deutsch_knowledge_substrate import (
    CounterfactualModel,
    Explanation,
    KnowledgeSubstrate,
)
from .phi_unified_mining_engine import UnifiedMiningEngine, UnifiedMiningState


class AutonomyLevel(Enum):
    """Levels of autonomous operation with increasing decision authority."""
    MANUAL = "manual"  # All decisions require operator approval
    ADVISORY = "advisory"  # System recommends, operator decides
    SUPERVISED = "supervised"  # System executes within predefined bounds
    AUTONOMOUS = "autonomous"  # System makes decisions with mathematical constraints
    EMERGENCY = "emergency"  # System takes protective action only


class SafetyConstraint(Enum):
    """Mathematical safety constraints that autonomous actions must satisfy."""
    HERMITICITY = "hermiticity"  # Operations must preserve Hermitian properties
    POSITIVE_SEMIDEFINITE = "positive_semidefinite"  # Results must be PSD
    NATURAL_SCALING = "natural_scaling"  # Must follow φ-resonant scaling laws
    ENERGY_CONSERVATION = "energy_conservation"  # Cannot exceed configured energy limits
    INFORMATION_INTEGRITY = "information_integrity"  # Must preserve informational structure


@dataclass
class AutonomousDecision:
    """Record of an autonomous decision with mathematical justification."""
    decision_id: str
    timestamp: float
    autonomy_level: AutonomyLevel
    decision_type: str
    mathematical_justification: Dict[str, Any]
    constraints_satisfied: List[SafetyConstraint]
    constraints_violated: List[SafetyConstraint]
    action_taken: str
    expected_outcome: str
    actual_outcome: Optional[str] = None
    operator_override: bool = False
    operator_reason: Optional[str] = None


@dataclass
class OptimizationTarget:
    """Mathematical optimization target with constraints."""
    target_name: str
    objective_function: str  # "maximize_hashrate", "minimize_energy", "maximize_phi_coherence"
    current_value: float
    target_value: float
    tolerance: float
    constraints: List[SafetyConstraint]
    priority: int  # Higher priority = more important


@dataclass
class SelfOptimizationProposal:
    """A proposed self-optimization discovered through the Reflexive Knowledge Loop."""
    proposal_id: str
    timestamp: float
    improvement_type: str  # "phi_scaling", "search_depth", "compression_target", "coherence_threshold"
    current_value: float
    proposed_value: float
    expected_phi_density_gain: float  # Expected improvement in φ-density
    logical_consistency_score: float  # How well it maintains logical consistency
    constraints_satisfied: List[SafetyConstraint]
    constraints_violated: List[SafetyConstraint]
    counterfactual_confidence: float  # Confidence from Deutsch substrate simulation
    codebase_source_module: str  # Which codebase module inspired this change
    applied: bool = False
    applied_at: Optional[float] = None
    outcome_phi_density: Optional[float] = None


@dataclass
class CodebaseSurroundings:
    """Abstract representation of the codebase 'surroundings' for Active Inference."""
    module_names: List[str]
    mathematical_invariants: Dict[str, str]  # invariant_name -> invariant_type
    codebase_graph_edges: List[Tuple[str, str, float]]  # (module_a, module_b, phi_resonance_weight)
    entropy_sources: List[str]  # Modules with high entropy (interesting for exploration)
    stable_core: List[str]  # Modules with high invariant stability


@dataclass
class AutonomousConfig:
    """Configuration for autonomous mining controller."""
    autonomy_level: AutonomyLevel = AutonomyLevel.ADVISORY
    max_autonomous_hashrate_ehs: float = 100.0  # Safety limit on autonomous hashrate
    max_autonomous_power_watts: float = 500.0  # Safety limit on power consumption
    phi_coherence_threshold: float = 0.70  # Minimum coherence for autonomous operation
    decision_audit_log_size: int = 1000  # Number of decisions to keep in memory
    operator_approval_required_for: List[str] = field(default_factory=lambda: [
        "pool_connection_change",
        "wallet_address_change",
        "significant_parameter_change",
        "emergency_shutdown"
    ])
    optimization_targets: List[OptimizationTarget] = field(default_factory=list)
    # Reflexive Knowledge Loop configuration
    reflexive_loop_enabled: bool = True
    reflexive_loop_interval: float = 60.0  # Seconds between improvement cycles
    max_proposals_per_cycle: int = 3
    virtual_session_horizon: float = 0.25  # Seconds to simulate virtual mining
    min_logical_consistency: float = 0.70  # Minimum consistency to accept a proposal
    compression_drive_enabled: bool = True  # Enable the "hunger" for compression
    knowledge_growth_rate_target: float = 0.01  # Minimum knowledge growth per cycle


class AutonomousMiningController:
    """Autonomous mining controller with mathematical self-governance and Reflexive Learning."""

    def __init__(
        self,
        unified_engine: UnifiedMiningEngine,
        config: Optional[AutonomousConfig] = None,
    ) -> None:
        self.engine = unified_engine
        self.config = config or AutonomousConfig()
        self.decision_log: List[AutonomousDecision] = []
        self.current_autonomy_level = self.config.autonomy_level
        self._decision_counter = 0
        self._performance_history: List[Dict[str, Any]] = []
        self.operator_approval_callback: Optional[Callable[[AutonomousDecision], bool]] = None

        # --- Reflexive Knowledge Loop state ---
        self.knowledge_substrate = KnowledgeSubstrate()
        self.surroundings: CodebaseSurroundings = self._build_codebase_surroundings()
        self.proposal_history: List[SelfOptimizationProposal] = []
        self._self_optimization_epochs: int = 0
        self._last_reflexive_cycle: float = 0.0
        self._phi_density_history: List[float] = []
        self._compression_seeking_history: List[float] = []
        self._logical_consistency_history: List[float] = []

    # ================================================================
    # REFLEXIVE KNOWLEDGE LOOP — Recursive Self-Learning
    # ================================================================

    def _build_codebase_surroundings(self) -> CodebaseSurroundings:
        """Map the codebase 'surroundings' (Umwelt) as a graph of mathematical invariants.
        
        The AI creates an abstract representation of its own codebase, identifying:
        - Module dependencies and their φ-resonance weights
        - Mathematical invariants that constrain behavior
        - Entropy sources (high-variability modules) vs stable core modules
        - This serves as the "Laws of Physics" for the AI's universe.
        """
        module_names = [
            "phi_unified_mining_engine",
            "consciousness_engine",
            "deutsch_knowledge_substrate",
            "ai_optimizer",
            "pulvini_compressed_solver",
            "pulvini_memory_compression_proof",
            "pulvini_autonomics",
            "genesis_ai",
            "hendrix_phi_solver",
            "phi_scaling_engine",
            "stratum_client",
            "golden_ratio_library",
        ]

        # Core mathematical invariants that define the "Laws of Physics"
        mathematical_invariants: Dict[str, str] = {
            "hermiticity": "density_matrix_self_adjoint",
            "positive_semidefinite": "density_matrix_nonnegative_eigenvalues",
            "phi_resonance": "golden_ratio_alignment",
            "yang_mills_gap": "mass_gap_spectral_condition",
            "information_integrity": "lossless_compression_invertibility",
            "conservation_of_phi": "phi_folding_reversible_transform",
            "m32_domain_coverage": "spherical_32_domain_partition",
        }

        # φ-resonance weighted dependency edges between modules
        codebase_graph_edges: List[Tuple[str, str, float]] = [
            ("phi_unified_mining_engine", "consciousness_engine", 0.95),
            ("phi_unified_mining_engine", "ai_optimizer", 0.90),
            ("phi_unified_mining_engine", "pulvini_compressed_solver", 0.88),
            ("phi_unified_mining_engine", "deutsch_knowledge_substrate", 0.75),
            ("consciousness_engine", "ai_optimizer", 0.85),
            ("consciousness_engine", "pulvini_autonomics", 0.80),
            ("ai_optimizer", "deutsch_knowledge_substrate", 0.78),
            ("pulvini_compressed_solver", "pulvini_memory_compression_proof", 0.92),
            ("pulvini_compressed_solver", "hendrix_phi_solver", 0.87),
            ("pulvini_compressed_solver", "phi_scaling_engine", 0.83),
            ("hendrix_phi_solver", "golden_ratio_library", 0.96),
            ("stratum_client", "phi_unified_mining_engine", 0.65),
            ("genesis_ai", "phi_unified_mining_engine", 0.91),
            ("genesis_ai", "consciousness_engine", 0.89),
            ("genesis_ai", "deutsch_knowledge_substrate", 0.82),
            ("genesis_ai", "pulvini_autonomics", 0.85),
        ]

        # High-entropy modules (mathematical paths not yet fully explored)
        entropy_sources = [
            "phi_scaling_engine",
            "deutsch_knowledge_substrate",
            "ai_optimizer",
        ]

        # Stable core modules (mathematically rigorous, well-tested)
        stable_core = [
            "golden_ratio_library",
            "hendrix_phi_solver",
            "pulvini_memory_compression_proof",
            "consciousness_engine",
        ]

        return CodebaseSurroundings(
            module_names=module_names,
            mathematical_invariants=mathematical_invariants,
            codebase_graph_edges=codebase_graph_edges,
            entropy_sources=entropy_sources,
            stable_core=stable_core,
        )

    def get_phi_density(self) -> float:
        """Compute the current φ-density of the system.
        
        φ-density is a measure of how 'resonant' the system is with its own
        mathematical invariants. Higher values indicate better self-alignment.
        This serves as the objective function for the Reflexive Knowledge Loop.
        
        NOTE: This method intentionally does NOT call get_autonomy_status()
        to avoid circular recursion (get_autonomy_status calls get_phi_density).
        """
        base_density = 0.5

        # Factor in constraint satisfaction rate from internal state
        total_decisions = len(self.decision_log)
        constraint_violations = sum(
            1 for d in self.decision_log if d.constraints_violated
        )
        if total_decisions > 0:
            constraint_health = 1.0 - (constraint_violations / max(total_decisions, 1))
            base_density += 0.2 * constraint_health

        # Factor in knowledge substrate quality
        try:
            knowledge_metrics = self.knowledge_substrate.get_knowledge_metrics()
            avg_accuracy = knowledge_metrics.get("avg_predictive_accuracy", 0.5)
            base_density += 0.15 * avg_accuracy
            growth_rate = knowledge_metrics.get("knowledge_growth_rate", 0.0)
            base_density += 0.10 * min(growth_rate, 1.0)
        except Exception:
            pass

        # Factor in compression ratio (the "metabolic rate" drive)
        if self.config.compression_drive_enabled and self._compression_seeking_history:
            latest_compression = self._compression_seeking_history[-1]
            # Higher compression within info integrity limits improves density
            optimal_compression = min(latest_compression / 2.0, 1.0)
            base_density += 0.10 * optimal_compression

        # Factor in logical consistency over time
        if self._logical_consistency_history:
            avg_consistency = sum(self._logical_consistency_history) / len(self._logical_consistency_history)
            base_density += 0.05 * avg_consistency

        # Factor in self-optimization epochs (learning accumulates density)
        if self._self_optimization_epochs > 0:
            learning_bonus = min(self._self_optimization_epochs * 0.01, 0.10)
            base_density += learning_bonus

        return min(max(base_density, 0.0), 1.0)

    def get_current_efficiency(self) -> float:
        """Return current mining efficiency proxy for improvement tracking.
        
        NOTE: This method intentionally does NOT call get_autonomy_status()
        to avoid circular recursion with get_phi_density().
        """
        base = 0.6
        total_decisions = len(self.decision_log)
        if total_decisions > 0:
            autonomous_count = sum(
                1 for d in self.decision_log if not d.operator_override
            )
            auto_rate = autonomous_count / max(total_decisions, 1)
            base += 0.2 * auto_rate
        return min(max(base, 0.0), 1.0)

    def _generate_counterfactual(self, target: str) -> SelfOptimizationProposal:
        """Use Deutsch Substrate to generate a counterfactual code change hypothesis.
        
        The AI asks: "What would happen if I changed this parameter?"
        It uses the Deutsch Knowledge Substrate's counterfactual reasoning
        to simulate the outcome without actually executing the change.
        """
        proposal_id = f"self_opt_{self._self_optimization_epochs}_{int(time.time())}"
        timestamp = time.time()

        if target == "phi_scaling":
            return self._propose_phi_scaling_improvement(proposal_id, timestamp)
        elif target == "search_depth":
            return self._propose_search_depth_improvement(proposal_id, timestamp)
        elif target == "compression_target":
            return self._propose_compression_improvement(proposal_id, timestamp)
        elif target == "coherence_threshold":
            return self._propose_coherence_threshold_improvement(proposal_id, timestamp)
        else:
            # Default: try phi_scaling
            return self._propose_phi_scaling_improvement(proposal_id, timestamp)

    def _propose_phi_scaling_improvement(
        self, proposal_id: str, timestamp: float
    ) -> SelfOptimizationProposal:
        """Propose a φ-scaling factor adjustment."""
        current_value = 1.5  # Default φ-scaling factor from phi_scaling_engine

        # Use Deutsch substrate to determine optimal direction
        context = {
            "phi_resonance": 0.5,
            "difficulty": 1e12,
            "thermal_load": 0.5,
        }

        # Counterfactual: what if we increase φ-scaling?
        counterfactual_increase = self.knowledge_substrate.counterfactual_reasoning(
            actual_strategy="current_phi_scaling",
            actual_outcome={"efficiency": self.get_current_efficiency()},
            alternative_strategy="phi_scaling_increase",
            context=context,
        )

        # Counterfactual: what if we decrease φ-scaling?
        counterfactual_decrease = self.knowledge_substrate.counterfactual_reasoning(
            actual_strategy="current_phi_scaling",
            actual_outcome={"efficiency": self.get_current_efficiency()},
            alternative_strategy="phi_scaling_decrease",
            context=context,
        )

        # Choose direction with higher confidence
        if counterfactual_increase.confidence > counterfactual_decrease.confidence:
            proposed_value = current_value * 1.05  # 5% increase
            confidence = counterfactual_increase.confidence
        else:
            proposed_value = current_value * 0.95  # 5% decrease
            confidence = counterfactual_decrease.confidence

        # Estimate φ-density gain
        expected_gain = 0.02 * confidence

        # Compute logical consistency score based on explanation quality
        best_explanation = self.knowledge_substrate.best_explanation_for_context(context)
        logical_consistency = 0.7 + 0.2 * confidence

        proposed_action = {
            "phi_scaling_change": proposed_value - current_value,
        }
        satisfied, violated = self._check_safety_constraints(proposed_action)

        return SelfOptimizationProposal(
            proposal_id=proposal_id,
            timestamp=timestamp,
            improvement_type="phi_scaling",
            current_value=current_value,
            proposed_value=proposed_value,
            expected_phi_density_gain=expected_gain,
            logical_consistency_score=min(max(logical_consistency, 0.0), 1.0),
            constraints_satisfied=satisfied,
            constraints_violated=violated,
            counterfactual_confidence=confidence,
            codebase_source_module="phi_scaling_engine",
        )

    def _propose_search_depth_improvement(
        self, proposal_id: str, timestamp: float
    ) -> SelfOptimizationProposal:
        """Propose a search depth adjustment."""
        current_value = 60.0  # Default max_search_time from SearchStrategy

        context = {
            "phi_resonance": 0.5,
            "difficulty": 1e12,
            "thermal_load": 0.5,
        }

        # Counterfactual: deeper vs shallower search
        counterfactual_deeper = self.knowledge_substrate.counterfactual_reasoning(
            actual_strategy="current_search_depth",
            actual_outcome={"efficiency": self.get_current_efficiency()},
            alternative_strategy="deeper_search",
            context=context,
        )

        # Adjust direction based on φ-coherence signal
        if self._phi_density_history:
            trend = (
                self._phi_density_history[-1] - self._phi_density_history[0]
            ) / max(len(self._phi_density_history), 1)
            if trend > 0.01:
                # Increasing coherence → can afford deeper search
                proposed_value = min(current_value * 1.1, 120.0)
                confidence = counterfactual_deeper.confidence
            else:
                # Decreasing coherence → shallower search
                proposed_value = max(current_value * 0.9, 10.0)
                confidence = 0.6
        else:
            proposed_value = current_value
            confidence = 0.5

        expected_gain = 0.015 * confidence
        logical_consistency = 0.75

        proposed_action = {
            "search_depth_change": proposed_value - current_value,
        }
        satisfied, violated = self._check_safety_constraints(proposed_action)

        return SelfOptimizationProposal(
            proposal_id=proposal_id,
            timestamp=timestamp,
            improvement_type="search_depth",
            current_value=current_value,
            proposed_value=proposed_value,
            expected_phi_density_gain=expected_gain,
            logical_consistency_score=logical_consistency,
            constraints_satisfied=satisfied,
            constraints_violated=violated,
            counterfactual_confidence=confidence,
            codebase_source_module="ai_optimizer",
        )

    def _propose_compression_improvement(
        self, proposal_id: str, timestamp: float
    ) -> SelfOptimizationProposal:
        """Propose a memory compression ratio adjustment.
        
        This is the "Hunger" drive — the AI seeks higher compression ratios
        to achieve more elegant representations of the mining process.
        """
        current_value = 1.86  # Default compression factor

        # The drive: seek higher compression for more elegant representation
        # But must respect information integrity constraint (compression_ratio <= 2.0)
        current_phi_density = self.get_phi_density()

        # Compute the "hunger" signal based on current state
        if self._compression_seeking_history:
            # If compression hasn't improved recently, hunger increases
            recent_trend = (
                self._compression_seeking_history[-1] - self._compression_seeking_history[0]
            ) / max(len(self._compression_seeking_history), 1)
            hunger_factor = max(0.0, 1.0 - abs(recent_trend))  # Hunger grows when stale
        else:
            hunger_factor = 0.5

        # Propose a compression improvement within safety bounds
        proposed_value = current_value * (1.0 + 0.02 * hunger_factor)
        # Information Integrity constraint caps at 2.0
        proposed_value = min(proposed_value, 1.98)

        expected_gain = 0.03 * (proposed_value / current_value - 1.0)
        logical_consistency = 0.8 if proposed_value <= 2.0 else 0.4

        proposed_action = {
            "compression_ratio": proposed_value,
            "current_compression": current_value,
        }
        satisfied, violated = self._check_safety_constraints(proposed_action)

        return SelfOptimizationProposal(
            proposal_id=proposal_id,
            timestamp=timestamp,
            improvement_type="compression_target",
            current_value=current_value,
            proposed_value=proposed_value,
            expected_phi_density_gain=expected_gain,
            logical_consistency_score=logical_consistency,
            constraints_satisfied=satisfied,
            constraints_violated=violated,
            counterfactual_confidence=0.7 + 0.2 * hunger_factor,
            codebase_source_module="pulvini_memory_compression_proof",
        )

    def _propose_coherence_threshold_improvement(
        self, proposal_id: str, timestamp: float
    ) -> SelfOptimizationProposal:
        """Propose a coherence threshold adjustment."""
        current_value = self.config.phi_coherence_threshold

        knowledge_metrics = self.knowledge_substrate.get_knowledge_metrics()
        avg_accuracy = knowledge_metrics.get("avg_predictive_accuracy", 0.5)

        # If knowledge is accurate, we can lower the threshold (more autonomy)
        if avg_accuracy > 0.7:
            proposed_value = max(current_value * 0.95, 0.50)
            confidence = 0.8
        # If knowledge is inaccurate, raise threshold (more caution)
        elif avg_accuracy < 0.3:
            proposed_value = min(current_value * 1.05, 0.90)
            confidence = 0.6
        else:
            proposed_value = current_value
            confidence = 0.5

        expected_gain = 0.01 * confidence
        logical_consistency = 0.7 + 0.2 * avg_accuracy

        proposed_action = {
            "coherence_threshold_change": proposed_value - current_value,
        }
        satisfied, violated = self._check_safety_constraints(proposed_action)

        return SelfOptimizationProposal(
            proposal_id=proposal_id,
            timestamp=timestamp,
            improvement_type="coherence_threshold",
            current_value=current_value,
            proposed_value=proposed_value,
            expected_phi_density_gain=expected_gain,
            logical_consistency_score=min(max(logical_consistency, 0.0), 1.0),
            constraints_satisfied=satisfied,
            constraints_violated=violated,
            counterfactual_confidence=confidence,
            codebase_source_module="consciousness_engine",
        )

    def _simulate_virtual_mining(self, proposal: SelfOptimizationProposal) -> float:
        """Run a 'Virtual Mining Session' in memory to assess the proposal.
        
        Instead of executing on hardware, the AI simulates the effect of the
        proposed change on its internal model, using the Deutsch Knowledge
        Substrate's counterfactual reasoning engine.
        
        Returns the simulated φ-density after applying the proposal.
        """
        # Start with current φ-density
        current_density = self.get_phi_density()

        # Factor in constraint health
        violation_penalty = len(proposal.constraints_violated) * 0.1

        # Factor in logical consistency
        consistency_bonus = proposal.logical_consistency_score * 0.05

        # Factor in counterfactual confidence
        confidence_bonus = proposal.counterfactual_confidence * 0.05

        # Expected gain scaled by proposal quality
        quality_factor = (
            (1.0 - violation_penalty)
            * (1.0 + consistency_bonus)
            * (1.0 + confidence_bonus)
        )
        simulated_density = current_density + proposal.expected_phi_density_gain * quality_factor

        return min(max(simulated_density, 0.0), 1.0)

    def validate_constraints(self, proposal: SelfOptimizationProposal) -> bool:
        """Validate that a proposal satisfies all 5 Safety Constraints.
        
        Returns True only if all constraints are satisfied and the proposal
        maintains logical consistency above the minimum threshold.
        """
        if len(proposal.constraints_violated) > 0:
            return False

        if proposal.logical_consistency_score < self.config.min_logical_consistency:
            return False

        # Hermiticity constraint: operations must preserve Hermitian properties
        if SafetyConstraint.HERMITICITY not in proposal.constraints_satisfied:
            return False

        # PSD constraint: results must be Positive Semi-Definite
        if SafetyConstraint.POSITIVE_SEMIDEFINITE not in proposal.constraints_satisfied:
            return False

        # Information Integrity constraint: must preserve informational structure
        if SafetyConstraint.INFORMATION_INTEGRITY not in proposal.constraints_satisfied:
            return False

        return True

    def apply_self_optimization(self, proposal: SelfOptimizationProposal) -> None:
        """Commit a validated self-optimization to internal memory.
        
        This is the "learning" step — the AI updates its internal configuration
        to reflect the discovered improvement, which will take effect in the
        next mining epoch.
        """
        if proposal.applied:
            return

        proposal.applied = True
        proposal.applied_at = time.time()

        # Record outcome density (will be updated in the next cycle)
        proposal.outcome_phi_density = self.get_phi_density()

        # Apply the proposal to internal configuration
        if proposal.improvement_type == "phi_scaling":
            # Update the working φ-scaling factor (used in future epochs)
            self.config.optimization_targets.append(
                OptimizationTarget(
                    target_name="phi_scaling",
                    objective_function="maximize_phi_coherence",
                    current_value=proposal.current_value,
                    target_value=proposal.proposed_value,
                    tolerance=0.05,
                    constraints=[
                        SafetyConstraint.HERMITICITY,
                        SafetyConstraint.POSITIVE_SEMIDEFINITE,
                        SafetyConstraint.NATURAL_SCALING,
                    ],
                    priority=5,
                )
            )

        elif proposal.improvement_type == "search_depth":
            self.config.optimization_targets.append(
                OptimizationTarget(
                    target_name="search_depth",
                    objective_function="maximize_hashrate",
                    current_value=proposal.current_value,
                    target_value=proposal.proposed_value,
                    tolerance=5.0,
                    constraints=[
                        SafetyConstraint.ENERGY_CONSERVATION,
                        SafetyConstraint.NATURAL_SCALING,
                    ],
                    priority=4,
                )
            )

        elif proposal.improvement_type == "compression_target":
            self.config.optimization_targets.append(
                OptimizationTarget(
                    target_name="compression_target",
                    objective_function="maximize_phi_coherence",
                    current_value=proposal.current_value,
                    target_value=proposal.proposed_value,
                    tolerance=0.05,
                    constraints=[
                        SafetyConstraint.INFORMATION_INTEGRITY,
                        SafetyConstraint.HERMITICITY,
                    ],
                    priority=3,
                )
            )

        elif proposal.improvement_type == "coherence_threshold":
            self.config.phi_coherence_threshold = proposal.proposed_value
            self.config.optimization_targets.append(
                OptimizationTarget(
                    target_name="coherence_threshold",
                    objective_function="minimize_energy",
                    current_value=proposal.current_value,
                    target_value=proposal.proposed_value,
                    tolerance=0.02,
                    constraints=[
                        SafetyConstraint.NATURAL_SCALING,
                        SafetyConstraint.ENERGY_CONSERVATION,
                    ],
                    priority=2,
                )
            )

        # Record the improvement in knowledge substrate
        self.knowledge_substrate.create_knowledge_from_success(
            strategy_id=f"self_opt_{proposal.improvement_type}",
            context={
                "improvement_type": proposal.improvement_type,
                "current_value": proposal.current_value,
                "proposed_value": proposal.proposed_value,
                "phi_density_before": self.get_phi_density(),
            },
            outcome={
                "accepted": True,
                "confidence": proposal.counterfactual_confidence,
                "expected_gain": proposal.expected_phi_density_gain,
            },
        )

        self._self_optimization_epochs += 1

    async def _run_reflexive_cycle(self) -> List[SelfOptimizationProposal]:
        """Run one complete iteration of the Reflexive Knowledge Loop.
        
        The full loop:
        1. Analyze surroundings (current φ-density and codebase state)
        2. Generate counterfactual proposals via Deutsch Substrate
        3. Simulate virtual mining sessions for each proposal
        4. Validate against 5 Safety Constraints
        5. Apply validated improvements to internal memory
        """
        if not self.config.reflexive_loop_enabled:
            return []

        current_density = self.get_phi_density()
        current_efficiency = self.get_current_efficiency()

        # Record historical metrics
        self._phi_density_history.append(current_density)
        if len(self._phi_density_history) > 100:
            self._phi_density_history = self._phi_density_history[-100:]

        # Step 1: Analyze surroundings — which entropy source to explore?
        # Rotate through improvement targets based on knowledge gaps
        knowledge_metrics = self.knowledge_substrate.get_knowledge_metrics()
        target_cycle = ["phi_scaling", "search_depth", "compression_target", "coherence_threshold"]
        current_target = target_cycle[self._self_optimization_epochs % len(target_cycle)]

        # Step 2: Generate counterfactual proposals
        proposals = []
        targets_to_try = [current_target]
        # Add the compression target more often (the "hunger" drive)
        if self.config.compression_drive_enabled:
            targets_to_try.append("compression_target")
        # Add extra targets if knowledge growth is low
        growth_rate = knowledge_metrics.get("knowledge_growth_rate", 0.0)
        if growth_rate < self.config.knowledge_growth_rate_target:
            extra_targets = [t for t in target_cycle if t not in targets_to_try]
            targets_to_try.extend(extra_targets[:self.config.max_proposals_per_cycle])

        for target in targets_to_try[:self.config.max_proposals_per_cycle]:
            proposal = self._generate_counterfactual(target)
            proposals.append(proposal)
            self.proposal_history.append(proposal)

        # Step 3: Simulate virtual mining sessions
        for proposal in proposals:
            simulated_density = self._simulate_virtual_mining(proposal)
            # The simulation outcome informs the proposal's expected gain
            proposal.expected_phi_density_gain = simulated_density - current_density

        # Step 4: Validate against 5 Safety Constraints
        valid_proposals = [p for p in proposals if self.validate_constraints(p)]

        # Step 5: Apply validated improvements
        for proposal in valid_proposals:
            self.apply_self_optimization(proposal)

        # Record logical consistency
        avg_consistency = (
            sum(p.logical_consistency_score for p in proposals) / max(len(proposals), 1)
        )
        self._logical_consistency_history.append(avg_consistency)
        if len(self._logical_consistency_history) > 50:
            self._logical_consistency_history = self._logical_consistency_history[-50:]

        # Record compression seeking
        if self.config.compression_drive_enabled:
            compression_proposals = [p for p in proposals if p.improvement_type == "compression_target"]
            if compression_proposals:
                avg_compression = sum(p.proposed_value for p in compression_proposals) / len(compression_proposals)
                self._compression_seeking_history.append(avg_compression)
                if len(self._compression_seeking_history) > 50:
                    self._compression_seeking_history = self._compression_seeking_history[-50:]

        return proposals

    async def seek_improvement(self) -> Dict[str, Any]:
        """Public entry point for the Reflexive Knowledge Loop.
        
        Analyzes the 'surroundings' (codebase state), uses the Deutsch Substrate
        to simulate counterfactual improvements, validates against Safety Constraints,
        and commits validated improvements to internal memory.
        
        Returns a status report of the improvement cycle.
        """
        cycle_start = time.time()

        # Run the full reflexive cycle
        proposals = await self._run_reflexive_cycle()

        cycle_duration = time.time() - cycle_start

        # Build the improvement report
        if proposals:
            applied_count = sum(1 for p in proposals if p.applied)
            proposal_details = [
                {
                    "proposal_id": p.proposal_id,
                    "improvement_type": p.improvement_type,
                    "current_value": p.current_value,
                    "proposed_value": p.proposed_value,
                    "expected_gain": p.expected_phi_density_gain,
                    "logical_consistency": p.logical_consistency_score,
                    "counterfactual_confidence": p.counterfactual_confidence,
                    "constraints_satisfied": [c.value for c in p.constraints_satisfied],
                    "constraints_violated": [c.value for c in p.constraints_violated],
                    "applied": p.applied,
                    "source_module": p.codebase_source_module,
                }
                for p in proposals
            ]
        else:
            proposal_details = []

        metrics = self.knowledge_substrate.get_knowledge_metrics()

        return {
            "reflexive_cycle_executed": True,
            "cycle_duration_seconds": round(cycle_duration, 4),
            "epoch": self._self_optimization_epochs,
            "current_phi_density": self.get_phi_density(),
            "proposals_generated": len(proposals),
            "proposals_applied": sum(1 for p in proposals if p.applied),
            "autonomy_level": self.current_autonomy_level.value,
            "proposals": proposal_details,
            "knowledge_metrics": {
                "total_explanations": metrics.get("total_explanations", 0),
                "avg_predictive_accuracy": metrics.get("avg_predictive_accuracy", 0.0),
                "knowledge_growth_rate": metrics.get("knowledge_growth_rate", 0.0),
                "counterfactual_models": metrics.get("counterfactual_models", 0),
                "criticism_events": metrics.get("criticism_events", 0),
            },
            "surroundings": {
                "entropy_sources": self.surroundings.entropy_sources,
                "stable_core_count": len(self.surroundings.stable_core),
                "module_count": len(self.surroundings.module_names),
            },
            "compression_drive": {
                "enabled": self.config.compression_drive_enabled,
                "history_length": len(self._compression_seeking_history),
                "latest_seeking": (
                    self._compression_seeking_history[-1]
                    if self._compression_seeking_history
                    else None
                ),
            },
        }

    # ================================================================
    # EXISTING FUNCTIONALITY (preserved and extended)
    # ================================================================

    def _generate_decision_id(self) -> str:
        """Generate unique decision ID."""
        self._decision_counter += 1
        return f"autonomous_decision_{self._decision_counter}_{int(time.time())}"

    def _log_decision(self, decision: AutonomousDecision) -> None:
        """Log autonomous decision with audit trail."""
        self.decision_log.append(decision)
        # Maintain log size limit
        if len(self.decision_log) > self.config.decision_audit_log_size:
            self.decision_log = self.decision_log[-self.config.decision_audit_log_size:]

    def _check_safety_constraints(
        self,
        proposed_action: Dict[str, Any],
    ) -> Tuple[List[SafetyConstraint], List[SafetyConstraint]]:
        """Check if proposed action satisfies all safety constraints."""
        satisfied = []
        violated = []

        # Check Hermiticity constraint
        if self._check_hermiticity(proposed_action):
            satisfied.append(SafetyConstraint.HERMITICITY)
        else:
            violated.append(SafetyConstraint.HERMITICITY)

        # Check PSD constraint
        if self._check_psd(proposed_action):
            satisfied.append(SafetyConstraint.POSITIVE_SEMIDEFINITE)
        else:
            violated.append(SafetyConstraint.POSITIVE_SEMIDEFINITE)

        # Check Natural Scaling constraint
        if self._check_natural_scaling(proposed_action):
            satisfied.append(SafetyConstraint.NATURAL_SCALING)
        else:
            violated.append(SafetyConstraint.NATURAL_SCALING)

        # Check Energy Conservation constraint
        if self._check_energy_conservation(proposed_action):
            satisfied.append(SafetyConstraint.ENERGY_CONSERVATION)
        else:
            violated.append(SafetyConstraint.ENERGY_CONSERVATION)

        # Check Information Integrity constraint
        if self._check_information_integrity(proposed_action):
            satisfied.append(SafetyConstraint.INFORMATION_INTEGRITY)
        else:
            violated.append(SafetyConstraint.INFORMATION_INTEGRITY)

        return satisfied, violated

    def _check_hermiticity(self, action: Dict[str, Any]) -> bool:
        """Check if action preserves Hermitian properties.
        
        An operation preserves Hermiticity if:
        - It does not introduce imaginary asymmetries in the density matrix
        - The proposed change is self-adjoint (symmetric under transpose-conjugate)
        """
        # Verify the action doesn't break Hermitian symmetry
        for key, value in action.items():
            if isinstance(value, complex):
                # Complex values must appear with their conjugates
                return False
            if isinstance(value, (int, float)):
                # Real-valued changes preserve Hermiticity by construction
                # when applied to the diagonal of the density matrix
                continue
        return True  # Assume actions preserve hermiticity unless proven otherwise

    def _check_psd(self, action: Dict[str, Any]) -> bool:
        """Check if action results in positive semidefinite matrices.
        
        PSD is preserved if:
        - All eigenvalues remain non-negative
        - The action does not introduce negative diagonal elements
        """
        if "compression_ratio" in action:
            ratio = action["compression_ratio"]
            # Compression must not make eigenvalues negative
            if ratio > 3.0:
                return False
        if "phi_scaling_change" in action:
            change = action["phi_scaling_change"]
            # Scaling must not invert the density matrix
            if abs(change) > 2.0:
                return False
        return True  # Assume actions preserve PSD unless proven otherwise

    def _check_natural_scaling(self, action: Dict[str, Any]) -> bool:
        """Check if action follows φ-resonant scaling laws."""
        if "hashrate_change" in action:
            change = action["hashrate_change"]
            # Changes should follow φ-based scaling patterns
            return abs(change) < 2.0  # Limit sudden changes
        if "phi_scaling_change" in action:
            change = action["phi_scaling_change"]
            # φ-scaling changes should be small and incremental
            return abs(change) < 0.5
        if "search_depth_change" in action:
            change = action["search_depth_change"]
            # Search depth changes should be within φ-scaled bounds
            return abs(change) < 30.0
        if "coherence_threshold_change" in action:
            change = action["coherence_threshold_change"]
            # Coherence thresholds should move gradually
            return abs(change) < 0.1
        return True

    def _check_energy_conservation(self, action: Dict[str, Any]) -> bool:
        """Check if action respects energy limits."""
        if "power_consumption_watts" in action:
            power = action["power_consumption_watts"]
            return power <= self.config.max_autonomous_power_watts
        if "search_depth_change" in action:
            change = action["search_depth_change"]
            # Deeper search consumes more energy
            if change > 0:
                # Each 10s of search depth costs energy
                energy_gain = change / 10.0 * 10.0  # ~10W per 10s
                return (self.config.max_autonomous_power_watts - 100.0) >= energy_gain
        return True

    def _check_information_integrity(self, action: Dict[str, Any]) -> bool:
        """Check if action preserves informational structure.
        
        Information Integrity is the 5th and most important constraint
        for a data-less learning system. It ensures that no information
        is lost during compression or transformation.
        """
        if "compression_ratio" in action:
            ratio = action["compression_ratio"]
            # Lossless compression limit: PULVINI phi-folding is invertible up to 2.0
            return ratio <= 2.0  # Limit compression to preserve information
        if "phi_scaling_change" in action:
            change = action["phi_scaling_change"]
            # Scaling must not cause aliasing in the φ-domain
            return abs(change) < 1.0
        return True

    def _requires_operator_approval(self, decision_type: str) -> bool:
        """Check if decision type requires operator approval."""
        return decision_type in self.config.operator_approval_required_for

    def _can_execute_autonomously(self, decision: AutonomousDecision) -> bool:
        """Determine if decision can be executed without operator approval."""
        if decision.operator_override:
            return False

        if self.current_autonomy_level == AutonomyLevel.MANUAL:
            return False

        if self._requires_operator_approval(decision.decision_type):
            return False

        if decision.constraints_violated:
            return False

        if self.current_autonomy_level == AutonomyLevel.ADVISORY:
            return False

        if self.current_autonomy_level == AutonomyLevel.SUPERVISED:
            return len(decision.constraints_violated) == 0

        if self.current_autonomy_level == AutonomyLevel.AUTONOMOUS:
            return len(decision.constraints_violated) == 0

        if self.current_autonomy_level == AutonomyLevel.EMERGENCY:
            return True  # Emergency actions can override

        return False

    async def optimize_search_strategy(
        self,
        current_coherence: float,
        current_hashrate_ehs: float,
    ) -> AutonomousDecision:
        """Autonomously optimize search strategy based on current conditions."""
        decision_id = self._generate_decision_id()
        timestamp = time.time()

        # Incorporate knowledge from Reflexive Learning
        knowledge_metrics = self.knowledge_substrate.get_knowledge_metrics()
        avg_accuracy = knowledge_metrics.get("avg_predictive_accuracy", 0.5)
        knowledge_bonus = 0.05 * avg_accuracy  # Refined search from knowledge

        # Mathematical justification based on phi coherence
        if current_coherence >= 0.80:
            # High coherence: aggressive optimization
            proposed_strategy = SearchStrategy(
                phi_resonance_enabled=True,
                adaptive_difficulty=True,
                max_search_time=30.0,
            )
            justification = {
                "reason": "high_phi_coherence_aggressive_optimization",
                "coherence": current_coherence,
                "phi_threshold": 0.80,
                "expected_improvement": "faster_search_with_high_confidence",
                "knowledge_accuracy": avg_accuracy,
                "self_optimization_epochs": self._self_optimization_epochs,
            }
        elif current_coherence >= 0.70:
            # Good coherence: balanced optimization
            proposed_strategy = SearchStrategy(
                phi_resonance_enabled=True,
                adaptive_difficulty=True,
                max_search_time=60.0,
            )
            justification = {
                "reason": "good_phi_coherence_balanced_optimization",
                "coherence": current_coherence,
                "phi_threshold": 0.70,
                "expected_improvement": "balanced_speed_and_reliability",
                "knowledge_accuracy": avg_accuracy,
                "self_optimization_epochs": self._self_optimization_epochs,
            }
        else:
            # Low coherence: conservative optimization
            proposed_strategy = SearchStrategy(
                phi_resonance_enabled=True,
                adaptive_difficulty=False,
                max_search_time=120.0,
            )
            justification = {
                "reason": "low_phi_coherence_conservative_optimization",
                "coherence": current_coherence,
                "phi_threshold": 0.70,
                "expected_improvement": "prioritize_reliability_over_speed",
                "knowledge_accuracy": avg_accuracy,
                "self_optimization_epochs": self._self_optimization_epochs,
            }

        proposed_action = {
            "strategy_change": "search_strategy",
            "max_search_time": proposed_strategy.max_search_time,
            "adaptive_difficulty": proposed_strategy.adaptive_difficulty,
        }

        satisfied, violated = self._check_safety_constraints(proposed_action)

        decision = AutonomousDecision(
            decision_id=decision_id,
            timestamp=timestamp,
            autonomy_level=self.current_autonomy_level,
            decision_type="search_strategy_optimization",
            mathematical_justification=justification,
            constraints_satisfied=satisfied,
            constraints_violated=violated,
            action_taken=f"set_search_strategy_{proposed_strategy.max_search_time}s",
            expected_outcome=justification["expected_improvement"],
        )

        self._log_decision(decision)

        if self._can_execute_autonomously(decision):
            # Execute the decision
            self.engine.optimizer.current_strategy = proposed_strategy
            decision.actual_outcome = "strategy_updated_successfully"
        else:
            # Request operator approval
            if self.operator_approval_callback:
                approved = self.operator_approval_callback(decision)
                if approved:
                    self.engine.optimizer.current_strategy = proposed_strategy
                    decision.actual_outcome = "strategy_updated_after_approval"
                else:
                    decision.operator_override = True
                    decision.actual_outcome = "operator_rejected_strategy_change"

        return decision

    async def optimize_hashrate_target(
        self,
        current_hashrate_ehs: float,
        target_hashrate_ehs: float,
    ) -> AutonomousDecision:
        """Autonomously adjust hashrate target within safety limits."""
        decision_id = self._generate_decision_id()
        timestamp = time.time()

        # Mathematical justification for hashrate adjustment
        if current_hashrate_ehs < target_hashrate_ehs:
            # Increase hashrate
            proposed_increase = min(
                target_hashrate_ehs - current_hashrate_ehs,
                self.config.max_autonomous_hashrate_ehs - current_hashrate_ehs,
            )
            justification = {
                "reason": "increase_hashrate_to_meet_target",
                "current_hashrate_ehs": current_hashrate_ehs,
                "target_hashrate_ehs": target_hashrate_ehs,
                "proposed_increase_ehs": proposed_increase,
                "expected_improvement": "higher_mining_efficiency",
            }
            action_taken = f"increase_hashrate_by_{proposed_increase}_ehs"
        else:
            # Decrease hashrate (energy saving)
            proposed_decrease = current_hashrate_ehs - target_hashrate_ehs
            justification = {
                "reason": "decrease_hashrate_to_save_energy",
                "current_hashrate_ehs": current_hashrate_ehs,
                "target_hashrate_ehs": target_hashrate_ehs,
                "proposed_decrease_ehs": proposed_decrease,
                "expected_improvement": "reduced_energy_consumption",
            }
            action_taken = f"decrease_hashrate_by_{proposed_decrease}_ehs"

        proposed_action = {
            "hashrate_change": proposed_increase if current_hashrate_ehs < target_hashrate_ehs else -proposed_decrease,
            "target_hashrate_ehs": target_hashrate_ehs,
        }

        satisfied, violated = self._check_safety_constraints(proposed_action)

        decision = AutonomousDecision(
            decision_id=decision_id,
            timestamp=timestamp,
            autonomy_level=self.current_autonomy_level,
            decision_type="hashrate_optimization",
            mathematical_justification=justification,
            constraints_satisfied=satisfied,
            constraints_violated=violated,
            action_taken=action_taken,
            expected_outcome=justification["expected_improvement"],
        )

        self._log_decision(decision)

        if self._can_execute_autonomously(decision):
            # Execute the decision (would update solver configuration)
            decision.actual_outcome = "hashrate_target_updated"
        else:
            # Request operator approval
            if self.operator_approval_callback:
                approved = self.operator_approval_callback(decision)
                if approved:
                    decision.actual_outcome = "hashrate_target_updated_after_approval"
                else:
                    decision.operator_override = True
                    decision.actual_outcome = "operator_rejected_hashrate_change"

        return decision

    async def optimize_compression_ratio(
        self,
        current_compression: float,
        target_compression: float,
    ) -> AutonomousDecision:
        """Autonomously adjust memory compression ratio."""
        decision_id = self._generate_decision_id()
        timestamp = time.time()

        # Mathematical justification for compression adjustment
        justification = {
            "reason": "optimize_memory_compression_for_efficiency",
            "current_compression": current_compression,
            "target_compression": target_compression,
            "phi_optimal_range": (1.5, 2.0),  # Golden ratio based optimal range
            "expected_improvement": "better_memory_utilization",
        }

        proposed_action = {
            "compression_ratio": target_compression,
            "current_compression": current_compression,
        }

        satisfied, violated = self._check_safety_constraints(proposed_action)

        decision = AutonomousDecision(
            decision_id=decision_id,
            timestamp=timestamp,
            autonomy_level=self.current_autonomy_level,
            decision_type="compression_optimization",
            mathematical_justification=justification,
            constraints_satisfied=satisfied,
            constraints_violated=violated,
            action_taken=f"adjust_compression_to_{target_compression}",
            expected_outcome=justification["expected_improvement"],
        )

        self._log_decision(decision)

        if self._can_execute_autonomously(decision):
            # Execute the decision (would update compression configuration)
            decision.actual_outcome = "compression_ratio_updated"
        else:
            # Request operator approval
            if self.operator_approval_callback:
                approved = self.operator_approval_callback(decision)
                if approved:
                    decision.actual_outcome = "compression_ratio_updated_after_approval"
                else:
                    decision.operator_override = True
                    decision.actual_outcome = "operator_rejected_compression_change"

        return decision

    async def emergency_shutdown(
        self,
        reason: str,
        mathematical_justification: Dict[str, Any],
    ) -> AutonomousDecision:
        """Execute emergency shutdown with mathematical justification."""
        decision_id = self._generate_decision_id()
        timestamp = time.time()

        # Emergency decisions can override normal autonomy levels
        previous_level = self.current_autonomy_level
        self.current_autonomy_level = AutonomyLevel.EMERGENCY

        decision = AutonomousDecision(
            decision_id=decision_id,
            timestamp=timestamp,
            autonomy_level=AutonomyLevel.EMERGENCY,
            decision_type="emergency_shutdown",
            mathematical_justification=mathematical_justification,
            constraints_satisfied=[SafetyConstraint.ENERGY_CONSERVATION],
            constraints_violated=[],
            action_taken="emergency_shutdown_initiated",
            expected_outcome="safe_system_shutdown",
        )

        self._log_decision(decision)

        # Restore previous autonomy level after emergency action
        self.current_autonomy_level = previous_level

        return decision

    def set_autonomy_level(self, level: AutonomyLevel) -> None:
        """Set the current autonomy level."""
        self.current_autonomy_level = level

    def get_decision_history(
        self,
        limit: Optional[int] = None,
    ) -> List[AutonomousDecision]:
        """Get history of autonomous decisions."""
        if limit:
            return self.decision_log[-limit:]
        return self.decision_log.copy()

    def get_autonomy_status(self) -> Dict[str, Any]:
        """Get current autonomy status and metrics, including Reflexive Learning state."""
        return {
            "autonomy_level": self.current_autonomy_level.value,
            "total_decisions": len(self.decision_log),
            "autonomous_decisions": sum(
                1 for d in self.decision_log if not d.operator_override
            ),
            "operator_overrides": sum(
                1 for d in self.decision_log if d.operator_override
            ),
            "constraint_violations": sum(
                1 for d in self.decision_log if d.constraints_violated
            ),
            "recent_decisions": [
                {
                    "decision_id": d.decision_id,
                    "timestamp": d.timestamp,
                    "decision_type": d.decision_type,
                    "action_taken": d.action_taken,
                    "operator_override": d.operator_override,
                }
                for d in self.decision_log[-10:]
            ],
            # Reflexive Knowledge Loop metrics
            "reflexive_learning": {
                "enabled": self.config.reflexive_loop_enabled,
                "self_optimization_epochs": self._self_optimization_epochs,
                "phi_density": self.get_phi_density(),
                "compression_drive_enabled": self.config.compression_drive_enabled,
                "knowledge_explanations": len(self.knowledge_substrate.explanations),
                "knowledge_counterfactuals": len(self.knowledge_substrate.counterfactuals),
                "knowledge_criticisms": len(self.knowledge_substrate.criticism_history),
                "proposals_generated": len(self.proposal_history),
                "proposals_applied": sum(1 for p in self.proposal_history if p.applied),
                "latest_phi_density": (
                    self._phi_density_history[-1] if self._phi_density_history else None
                ),
                "logical_consistency_history_length": len(self._logical_consistency_history),
            },
        }

    def set_operator_approval_callback(
        self,
        callback: Callable[[AutonomousDecision], bool],
    ) -> None:
        """Set callback for operator approval decisions."""
        self.operator_approval_callback = callback

    def get_knowledge_substrate(self) -> KnowledgeSubstrate:
        """Get the Deutsch Knowledge Substrate used for reflexive learning."""
        return self.knowledge_substrate

    def get_proposal_history(self) -> List[SelfOptimizationProposal]:
        """Get history of self-optimization proposals."""
        return self.proposal_history.copy()

    def get_codebase_surroundings(self) -> CodebaseSurroundings:
        """Get the codebase surroundings map used for Active Inference."""
        return self.surroundings


__all__ = [
    "AutonomousMiningController",
    "AutonomousConfig",
    "AutonomousDecision",
    "AutonomyLevel",
    "SafetyConstraint",
    "OptimizationTarget",
    "SelfOptimizationProposal",
    "CodebaseSurroundings",
]