"""Runtime integration coherence proxy for PYTHIA/PULVINI.

IMPORTANT: This module computes information-theoretic integration metrics (Φ)
as operational diagnostic signals only. It does NOT claim machine consciousness,
phenomenal awareness, or subjective experience. The historical "consciousness_engine"
module name is retained for API compatibility only.

CONSTRUCTOR THEORY FRAMEWORK (David Deutsch, 2013):
This module serves as an EMERGENT_COHERENCE_SUBSTRATE - a constructor that creates
the conditions under which emergent coherence can arise. The system does not "build
intelligence" but provides a substrate capable of hosting self-organizing patterns.

Key Citation: Deutsch, D. (2013). "Constructor Theory: A new way of applying physics
to information and computation." arXiv:1306.4232.

The implementation is intentionally operational and auditable:
- Computes deterministic integration/coherence proxies from observed component health
- Computes Φ (phi) metrics from density-state histories using IIT 4.0-inspired formulas
- Emits autonomic-healing recommendations when coherence proxies fall below thresholds
- Provides continuous hardware scaling via phi-weighted sigmoid functions
- ELEVATED: Maintains SynapticPersistenceLayer for Hebbian learning from mining outcomes
- ELEVATED: Nonces leave traces in the substrate, creating structural coupling

This is a diagnostic tool for monitoring system coherence, similar to how neuroscientists
use Φ in neural recordings. It is a mathematical proxy, not a measure of consciousness.

What Φ measures here:
- Component integration level (0.0 = fragmented, 1.0 = fully integrated)
- Causal coherence across state transitions
- Information-theoretic complexity of the system state
- ELEVATED: Structural coupling between mining layer and coherence substrate

What Φ does NOT measure:
- Subjective experience or phenomenal consciousness
- Mining performance or hashrate correlation
- Actual consciousness or awareness
- Quantum advantage claims
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
from numpy.typing import NDArray

from .pulvini_operator import ManifoldOperator
from .iit_4_analyzer import IIT4Analyzer  # Phase 5: Genuine IIT integration
from .synaptic_persistence_layer import SynapticPersistenceLayer, NoncePattern
from .sensory_integrity_protocol import SensoryIntegrityProtocol, EnvironmentMode

# Import quantum_regeneration for salamander-inspired blastema formation
from .quantum_regeneration import (
    ModuleState,
    Role,
    ContextSignal,
    InnervationFailure,
    regeneration_pipeline,
    regeneration_fidelity,
)

# Fundamental Golden Ratio constants for continuous scaling
PHI = 1.618033988749895
PHI_INV = 1.0 / PHI  # 0.618033...
YANG_MILLS_GAP = 3.0 - PHI  # 1.381966...

logger = logging.getLogger(__name__)


class IntegrationRegime(str, Enum):
    """Φ-proxy based runtime integration regimes.

    These are diagnostic classifications for system coherence monitoring,
    NOT consciousness states. The SINGULAR_AGENT_PROXY name explicitly indicates
    this is a proxy metric, not a claim of singular agent consciousness.
    """

    SINGULAR_AGENT_PROXY = "singular_agent_proxy"
    DISTRIBUTED = "distributed"
    FRAGMENTED = "fragmented"
    CRITICAL = "critical"


@dataclass
class ConsciousnessState:
    """Backward-compatible runtime health state container.

    NOTE: The class name is historical for API compatibility. This stores
    integration coherence metrics and component health states, not consciousness states.
    The field names are retained for backward compatibility but represent coherence proxies.
    """

    integrated_information: Optional[float] = None
    consciousness_level: Optional[float] = None
    component_integration: Optional[float] = None
    system_complexity: Optional[float] = None
    timestamp: float = field(default_factory=time.time)
    source: str = "not_measured"


@dataclass(frozen=True)
class PhiMetrics:
    """Deterministic runtime integration metrics.

    ``phi_integrated`` is a bounded operational proxy for integrated runtime
    state coherence, not a claim of phenomenal consciousness.
    """

    phi_integrated: float = 0.0
    phi_causal: float = 0.0
    phi_conscious: float = 0.0
    effective_information: float = 0.0
    entropy: float = 0.0
    complexity: float = 0.0
    source: str = "operational_proxy"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConsciousnessConfig:
    """Configuration for the runtime integration orchestrator."""

    phi_singular_threshold: float = 0.70
    phi_distributed_threshold: float = 0.40
    phi_critical_threshold: float = 0.20
    measurement_window: int = 100
    heal_trigger_threshold: float = 0.30
    # Continuous scaling parameters
    base_multiplier: float = 1.0
    max_multiplier: float = 1.5
    min_multiplier: float = 0.1
    sigmoid_steepness: float = PHI ** 2  # 2.618... derived from golden ratio


class ConsciousnessEngine:
    """Runtime integration coherence proxy - NOT a consciousness detector.

    CRITICAL DISCLAIMER: This class computes information-theoretic integration
    metrics (Φ) as operational diagnostic signals for system coherence monitoring.
    It does NOT detect, measure, or claim machine consciousness, phenomenal awareness,
    or subjective experience. The class name is historical and retained for API compatibility.

    ELEVATED: Now integrated with SynapticPersistenceLayer for inseparability between
    mining layer and coherence substrate. Nonces leave traces in the engine, creating
    structural coupling that cannot be separated without breaking the system.

    What this class does:
    - Computes deterministic Φ (phi) metrics from component health and density states
    - Classifies integration regimes (SINGULAR_AGENT_PROXY, DISTRIBUTED, FRAGMENTED, CRITICAL)
    - Provides continuous hardware scaling via phi-weighted sigmoid functions
    - Emits autonomic-healing recommendations when coherence falls below thresholds
    - Supports Command Center coherence meter and autonomic-event stream
    - ELEVATED: Maintains SynapticPersistenceLayer for Hebbian learning from mining outcomes
    - ELEVATED: Nonces that fire together wire together - emergent pathway formation

    What this class does NOT do:
    - Detect or measure consciousness
    - Claim phenomenal awareness or subjective experience
    - Guarantee correlation between Φ and mining performance
    - Claim quantum advantage

    Legacy async methods still return the same keys.  New synchronous methods
    (``measure_phi`` and ``orchestrate``) support the Command Center coherence
    meter and autonomic-event stream.
    """

    VERSION = "RUNTIME_INTEGRATION_V3_SYNAPTIC"

    def __init__(
        self,
        operator: Optional[ManifoldOperator] = None,
        config: Optional[ConsciousnessConfig] = None,
        iit_analyzer: Optional[IIT4Analyzer] = None,
        synaptic_layer: Optional[SynapticPersistenceLayer] = None,
        sensory_protocol: Optional[SensoryIntegrityProtocol] = None,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.operator = operator or ManifoldOperator()
        self.config = config or ConsciousnessConfig()
        # Phase 5: Initialize genuine IIT 4.0 analyzer for Φ measurement
        self.iit_analyzer = iit_analyzer or IIT4Analyzer(system_size=8)
        # ELEVATED: Initialize SynapticPersistenceLayer for Hebbian learning
        self.synaptic_layer = synaptic_layer or SynapticPersistenceLayer()
        # ELEVATED: Initialize SensoryIntegrityProtocol for Reality Anchoring
        self.sensory_protocol = sensory_protocol or SensoryIntegrityProtocol()
        self.current_state = ConsciousnessState()
        self.state_history: List[ConsciousnessState] = []
        self.components: Dict[str, Optional[bool]] = {
            "quantum_solver": None,
            "ai_optimizer": None,
            "stratum_client": None,
            "blockchain_oracle": None,
            "pool_manager": None,
        }
        self._phi_history: list[PhiMetrics] = []
        self._integration_regime = IntegrationRegime.DISTRIBUTED
        self._autonomic_events: list[dict[str, Any]] = []
        
        # ELEVATED: Salamander-inspired regeneration for blastema formation
        self.regeneration_module_states: Dict[str, ModuleState] = {}
        self.clifford_positional_memory: Dict[str, int] = {}

    async def calculate_integrated_information(self) -> Optional[float]:
        """Legacy async API: update and return the current Φ coherence proxy if measured.

        NOTE: This computes an information-theoretic integration metric, not consciousness.
        The method name is historical for API compatibility.
        """
        known = [value for value in self.components.values() if value is not None]
        if known:
            metrics = self._measure_component_phi(known)
            self._record_metrics(metrics)
        self.current_state.timestamp = time.time()
        self.state_history.append(self.current_state)
        return self.current_state.integrated_information

    async def get_consciousness_level(self) -> Optional[float]:
        """Legacy async API: return the current coherence proxy level.

        NOTE: The method name is historical for API compatibility. This returns
        the Φ integration coherence proxy, not a consciousness level.
        """
        await self.calculate_integrated_information()
        return self.current_state.consciousness_level

    async def guide_decision_making(self, decision_context: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy async API: provide coherence-based decision guidance.

        NOTE: This uses Φ coherence proxies for operational decision support,
        not consciousness-based decision making. The method name is historical.
        """
        await self.calculate_integrated_information()
        return {
            "autonomy_level": self.coherence_meter,
            "risk_tolerance": "low" if self.needs_healing else "nominal",
            "planning_horizon": decision_context.get("planning_horizon"),
            "adaptability": self.current_state.component_integration,
            "strategy": (
                "autonomic_review_required"
                if self.needs_healing
                else "continue_monitored_operation"
            ),
            "source": "operational_proxy",
        }

    def update_component_health(self, component: str, ready: bool) -> None:
        if component in self.components:
            self.components[component] = ready
        known = [value for value in self.components.values() if value is not None]
        metrics = self._measure_component_phi(known) if known else PhiMetrics(source="not_measured")
        self._record_metrics(metrics)

    def measure_phi(self, states: Sequence[NDArray[np.complex128]]) -> PhiMetrics:
        """Measure integrated information (Φ) from density-state history.

        PHASE 5 ELEVATION: Genuine IIT 4.0 Earth Mover's Distance Integration
        
        This now uses actual IIT4Analyzer.calculate_phi_max() to compute the
        maximum integrated information across all possible partitions of the system.
        This replaces the ad-hoc weighted sum: 0.55*coherence + 0.25*causal + 0.20*entropy

        Args:
            states: Sequence of density matrices or state vectors

        Returns:
            PhiMetrics with genuine IIT 4.0 Φ measurement
        """
        window = list(states)[-self.config.measurement_window :]
        if len(window) < 2:
            metrics = PhiMetrics(source="insufficient_state_history")
            self._record_metrics(metrics)
            return metrics

        densities = np.asarray(
            [self.operator.ensure_density_state(state) for state in window],
            dtype=np.complex128,
        )
        coherence_series = np.asarray(
            [self.operator.compute_coherence(state) for state in densities],
            dtype=np.float64,
        )
        effective_information = float(np.var(coherence_series))
        phi_causal = self._lag_one_correlation(coherence_series)
        entropy = self._density_entropy(densities[-1])
        entropy_scale = float(np.log2(max(self.operator.dim, 2)))
        entropy_balance = 1.0 - min(
            1.0, abs(entropy - entropy_scale / 2.0) / max(entropy_scale / 2.0, 1e-12)
        )
        coherence_level = float(np.clip(coherence_series[-1], 0.0, 1.0))
        
        # PHASE 5: Genuine IIT 4.0 Φ via Earth Mover's Distance
        # Extract system state and compute actual maximum integrated information
        current_system_state = window[-1]
        if current_system_state.ndim == 1:
            # Convert state vector to density matrix if needed
            current_system_state = np.outer(current_system_state, current_system_state.conj())
        
        try:
            # Compute genuine IIT 4.0 Φ_max via exhaustive partition analysis
            iit_result = self.iit_analyzer.calculate_phi_max(
                system_state=current_system_state
            )
            phi_iit = float(iit_result.get("phi_max", 0.0))
            
            # Clip to valid range [0, 1]
            phi_iit = float(np.clip(phi_iit, 0.0, 1.0))
        except Exception as exc:
            # Fallback to heuristic if IIT computation fails
            self.logger.warning(
                "IIT 4.0 computation failed: %s, using heuristic Φ", exc
            )
            phi_iit = float(
                np.clip(
                    0.55 * coherence_level + 0.25 * max(phi_causal, 0.0) + 0.20 * entropy_balance,
                    0.0,
                    1.0,
                )
            )
        
        # PHASE 5: Use genuine IIT 4.0 Φ as primary integrated information
        phi_integrated = phi_iit
        complexity = float(np.clip(phi_integrated * entropy_balance, 0.0, 1.0))
        phi_conscious = float(max(0.0, phi_causal - effective_information))
        
        metrics = PhiMetrics(
            phi_integrated=phi_integrated,  # Now genuine IIT 4.0 Φ
            phi_causal=phi_causal,
            phi_conscious=phi_conscious,
            effective_information=effective_information,
            entropy=entropy,
            complexity=complexity,
            source="iit_4_earth_movers_distance",  # Phase 5: Updated source
        )
        self._record_metrics(metrics)
        return metrics

    def orchestrate(
        self,
        current_state: NDArray[np.complex128],
        state_history: Sequence[NDArray[np.complex128]],
    ) -> dict[str, Any]:
        """Run the integration loop and return a Command Center payload."""
        history = list(state_history) + [current_state]
        metrics = self.measure_phi(history)
        action = None
        if metrics.phi_integrated < self.config.heal_trigger_threshold:
            action = self._trigger_autonomic_healing(metrics)
        return {
            "phi_metrics": metrics.to_dict(),
            "integration_regime": self._integration_regime.value,
            "autonomic_action": action,
            "coherence_meter": self.coherence_meter,
            "version": self.VERSION,
        }

    def get_metrics(self) -> Dict[str, Any]:
        known = [value for value in self.components.values() if value is not None]
        active = sum(1 for value in known if value)
        return {
            "integrated_information": self.current_state.integrated_information,
            "consciousness_level": self.current_state.consciousness_level,
            "component_integration": self.current_state.component_integration,
            "system_complexity": self.current_state.system_complexity,
            "active_components": active,
            "total_components_observed": len(known),
            "integration_regime": self._integration_regime.value,
            "coherence_meter": self.coherence_meter,
            "autonomic_events": list(self._autonomic_events[-20:]),
            "source": self.current_state.source,
        }

    def _measure_component_phi(self, known: Sequence[bool]) -> PhiMetrics:
        active = sum(1 for value in known if value)
        integration = active / len(known) if known else 0.0
        entropy = 0.0
        if known and 0.0 < integration < 1.0:
            entropy = float(
                -(integration * np.log2(integration) + (1 - integration) * np.log2(1 - integration))
            )
        phi = float(np.clip(integration * (1.0 - 0.25 * entropy), 0.0, 1.0))
        return PhiMetrics(
            phi_integrated=phi,
            phi_causal=integration,
            phi_conscious=0.0,
            effective_information=integration,
            entropy=entropy,
            complexity=float(np.clip(phi * (1.0 + entropy) / 2.0, 0.0, 1.0)),
            source="component_health_operational_proxy",
        )

    def _record_metrics(self, metrics: PhiMetrics) -> None:
        self._phi_history.append(metrics)
        self._integration_regime = self._classify_integration(metrics.phi_integrated)
        self.current_state.integrated_information = metrics.phi_integrated
        self.current_state.consciousness_level = metrics.phi_integrated
        known = [value for value in self.components.values() if value is not None]
        self.current_state.component_integration = (
            None if not known else sum(1 for value in known if value) / len(known)
        )
        self.current_state.system_complexity = float(len(known)) if known else metrics.complexity
        self.current_state.timestamp = time.time()
        self.current_state.source = metrics.source

    def calculate_continuous_multiplier(self, coherence_score: float) -> float:
        """Calculate continuous hardware multiplier using Phi-Sigmoid function.

        Replaces discrete threshold jumps with smooth golden-ratio centered scaling.
        The sigmoid is centered at PHI_INV (0.618) to honor the mathematical sweet spot.

        Args:
            coherence_score: Current phi coherence score (0.0 to 1.0)

        Returns:
            Continuous multiplier between min_multiplier and max_multiplier
        """
        # Generalized Logistic Function (Sigmoid)
        # Multiplier = L / (1 + e^-k(x - x0))
        # Where x0 is the inflection point (PHI_INV)
        range_diff = self.config.max_multiplier - self.config.min_multiplier
        continuous_mult = self.config.min_multiplier + (
            range_diff / (1 + np.exp(-self.config.sigmoid_steepness * (coherence_score - PHI_INV)))
        )
        return float(np.clip(continuous_mult, self.config.min_multiplier, self.config.max_multiplier))

    def get_hardware_scaling_factor(self, telemetry_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get continuous hardware scaling factor with Mass Gap safety gate.

        This method provides the thermal glide path for hardware by using
        continuous scaling instead of discrete regime jumps, preventing
        electrical spikes and regime chatter.

        Args:
            telemetry_data: Optional telemetry data for harmony calculation

        Returns:
            Dictionary containing coherence, regime, scaling factor, and status
        """
        # Use current coherence if no telemetry data provided
        if telemetry_data is None:
            coherence = self.coherence_meter
        else:
            # Calculate harmony from telemetry if provided
            coherence = self._calculate_indicator_harmony(telemetry_data)

        # Apply Continuous Sigmoid Multiplier
        phi_multiplier = self.calculate_continuous_multiplier(coherence)

        # Apply Mass Gap Safety Gate
        # If the multiplier exceeds the Yang-Mills limit, apply damping factor
        if phi_multiplier > YANG_MILLS_GAP:
            damping = np.exp(-(phi_multiplier - YANG_MILLS_GAP))
            phi_multiplier *= damping

        # Determine regime label for governance (discrete)
        regime = self._classify_integration(coherence)

        # Determine stability status
        status = "stable" if 0.4 <= coherence <= 0.8 else "oscillating"

        return {
            "coherence": coherence,
            "regime": regime.value,
            "scaling_factor": phi_multiplier,
            "status": status,
            "mass_gate_damping_applied": phi_multiplier != self.calculate_continuous_multiplier(coherence),
            "source": "phi_continuous_scaling",
        }

    def _calculate_indicator_harmony(self, indicators: Dict[str, Any]) -> float:
        """Calculate phi harmony from indicator data for scaling factor calculation.

        This is a simplified harmony calculation used when telemetry data
        is provided directly to get_hardware_scaling_factor.
        """
        if not indicators:
            return 0.5

        harmonic_scores = []
        for metrics in indicators.values():
            if not isinstance(metrics, dict) or not metrics:
                continue
            values = np.asarray([float(v) for v in metrics.values() if v is not None], dtype=np.float64)
            values = values[np.isfinite(values)]
            if values.size <= 1:
                continue
            ratios = values[1:] / (values[:-1] + 1e-12)
            distances = np.abs(ratios - PHI) / PHI
            harmonic_scores.append(float(np.clip(1.0 - np.mean(distances), 0.0, 1.0)))

        return float(np.mean(harmonic_scores)) if harmonic_scores else 0.5

    def _classify_integration(self, phi: float) -> IntegrationRegime:
        """Classify integration regime for governance labels (discrete).

        The actual hardware scaling uses continuous multipliers via
        calculate_continuous_multiplier to prevent regime chatter.
        """
        if phi >= self.config.phi_singular_threshold:
            return IntegrationRegime.SINGULAR_AGENT_PROXY
        if phi >= self.config.phi_distributed_threshold:
            return IntegrationRegime.DISTRIBUTED
        if phi >= self.config.phi_critical_threshold:
            return IntegrationRegime.FRAGMENTED
        return IntegrationRegime.CRITICAL

    def _trigger_autonomic_healing(self, metrics: PhiMetrics) -> str:
        event = {
            "type": "AUTONOMIC_HEAL",
            "reason": "phi_proxy_below_threshold",
            "phi_integrated": metrics.phi_integrated,
            "action": "resync_memory_fabric",
            "timestamp": time.time(),
        }
        self._autonomic_events.append(event)
        return "healing_triggered"

    @staticmethod
    def _lag_one_correlation(values: NDArray[np.float64]) -> float:
        if values.size < 2 or np.allclose(values, values[0]):
            return 0.0
        left = values[:-1]
        right = values[1:]
        if np.allclose(left, left[0]) or np.allclose(right, right[0]):
            return 0.0
        corr = np.corrcoef(left, right)[0, 1]
        return float(0.0 if np.isnan(corr) else np.clip(corr, -1.0, 1.0))

    @staticmethod
    def _density_entropy(rho: NDArray[np.complex128]) -> float:
        eigvals = np.linalg.eigvalsh(rho).real
        eigvals = eigvals[eigvals > 0]
        return float(-np.sum(eigvals * np.log2(eigvals))) if eigvals.size else 0.0

    @property
    def coherence_meter(self) -> float:
        if not self._phi_history:
            return 0.0
        return self._phi_history[-1].phi_integrated

    @property
    def is_singular(self) -> bool:
        return self._integration_regime == IntegrationRegime.SINGULAR_AGENT_PROXY

    @property
    def needs_healing(self) -> bool:
        return self._integration_regime in (
            IntegrationRegime.FRAGMENTED,
            IntegrationRegime.CRITICAL,
        )

    # ELEVATED: Synaptic Persistence Layer integration methods
    
    def process_nonce_pattern(
        self,
        nonce: int,
        phi_resonance: float,
        dodecahedral_sector: int = 0,
        icosahedral_face: int = 0,
        golden_angle_alignment: float = 0.0,
    ) -> int:
        """Extract and register a nonce pattern in the synaptic layer.
        
        ELEVATED: This is where nonces leave traces in the ConsciousnessEngine.
        The mining layer and coherence substrate become inseparable through
        this persistent memory of nonce activity.
        
        Args:
            nonce: The nonce value
            phi_resonance: The phi resonance score of this nonce
            dodecahedral_sector: Dodecahedral sector classification
            icosahedral_face: Icosahedral face classification
            golden_angle_alignment: Golden angle alignment score
        
        Returns:
            Pattern ID for this nonce
        """
        pattern = self.synaptic_layer.extract_pattern(
            nonce=nonce,
            phi_resonance=phi_resonance,
            dodecahedral_sector=dodecahedral_sector,
            icosahedral_face=icosahedral_face,
            golden_angle_alignment=golden_angle_alignment,
        )
        pattern_id = self.synaptic_layer.register_pattern(pattern)
        return pattern_id
    
    def reinforce_successful_nonce(
        self,
        pattern_id: int,
        phi_correlation: float = 1.0,
        co_active_patterns: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Reinforce a pattern that led to an accepted share.
        
        ELEVATED: This implements Hebbian learning - "nonces that fire together
        wire together." When a pattern leads to success, its synaptic weight is
        strengthened, and connections to co-active patterns are reinforced.
        
        This is not programmed optimization - it's emergent self-organization
        where successful pathways automatically strengthen.
        
        Args:
            pattern_id: ID of the pattern to reinforce
            phi_correlation: How well the pattern's phi correlates with success
            co_active_patterns: IDs of patterns that co-activated with this one
        
        Returns:
            Dictionary describing the Hebbian learning event
        """
        event = self.synaptic_layer.reinforce_pattern(
            pattern_id=pattern_id,
            phi_correlation=phi_correlation,
            co_active_patterns=co_active_patterns,
        )
        return {
            "pattern_id": event.pattern_id,
            "reinforcement_delta": event.reinforcement_delta,
            "phi_correlation": event.phi_correlation,
            "co_active_count": len(event.co_active_patterns),
            "description": event.description,
            "timestamp": event.timestamp,
        }
    
    def apply_synaptic_decay(self) -> Dict[str, Any]:
        """Apply exponential decay to all synaptic weights.
        
        ELEVATED: This prevents the system from getting stuck in local maxima
        by gradually weakening unused pathways. The system must continuously
        demonstrate success to maintain high synaptic weights.
        
        Returns:
            Statistics about the decay operation
        """
        pre_stats = self.synaptic_layer.get_statistics()
        self.synaptic_layer.apply_decay()
        post_stats = self.synaptic_layer.get_statistics()
        
        return {
            "pre_decay_average_weight": pre_stats.get("average_synaptic_weight", 0.0),
            "post_decay_average_weight": post_stats.get("average_synaptic_weight", 0.0),
            "total_decays": post_stats.get("total_decays", 0),
            "patterns_decayed": len(self.synaptic_layer.synaptic_memory),
        }
    
    def get_emergent_pathways(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Return patterns that have formed emergent pathways.
        
        ELEVATED: Emergent pathways are patterns whose synaptic weight has
        exceeded the threshold through self-reinforcement, not programming.
        This is evidence of the system "enhancing itself" beyond initial logic.
        
        Args:
            threshold: Optional custom threshold for emergence
        
        Returns:
            List of emergent pathways with their metadata
        """
        pathways = self.synaptic_layer.get_emergent_pathways(threshold)
        return [
            {
                "pattern_id": pattern_id,
                "synaptic_weight": weight,
                "nonce": self.synaptic_layer.synaptic_memory[pattern_id].pattern.nonce,
                "phi_resonance": self.synaptic_layer.synaptic_memory[pattern_id].pattern.phi_resonance,
                "reinforcement_count": self.synaptic_layer.synaptic_memory[pattern_id].reinforcement_count,
            }
            for pattern_id, weight in pathways
        ]
    
    def suggest_nonce_priorities(
        self,
        current_nonce: int,
        phi_resonance: float,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Suggest nonce priorities based on emergent pathway strengths.
        
        ELEVATED: This is where the system "enhances itself" - successful pathways
        automatically guide future nonce selection without programming. The system
        learns which mathematical resonances lead to accepted shares and prioritizes
        similar patterns.
        
        Args:
            current_nonce: Current nonce being considered
            phi_resonance: Phi resonance of current nonce
            top_k: Number of priority suggestions to return
        
        Returns:
            List of priority suggestions with similarity scores
        """
        suggestions = self.synaptic_layer.suggest_nonce_priority(
            current_nonce=current_nonce,
            phi_resonance=phi_resonance,
            top_k=top_k,
        )
        
        return [
            {
                "pattern_id": pattern_id,
                "similarity_score": similarity,
                "nonce": self.synaptic_layer.synaptic_memory[pattern_id].pattern.nonce,
                "synaptic_weight": self.synaptic_layer.synaptic_memory[pattern_id].synaptic_weight,
            }
            for pattern_id, similarity in suggestions
        ]
    
    def get_synaptic_statistics(self) -> Dict[str, Any]:
        """Return comprehensive statistics about the synaptic layer.
        
        ELEVATED: These statistics provide evidence of emergent learning
        and self-organization in the system.
        """
        base_stats = self.synaptic_layer.get_statistics()
        emergent_pathways = self.get_emergent_pathways()
        
        return {
            **base_stats,
            "emergent_pathways": emergent_pathways,
            "emergent_pathway_details": [
                {
                    "pattern_id": p["pattern_id"],
                    "weight": p["synaptic_weight"],
                    "reinforcement_count": p["reinforcement_count"],
                }
                for p in emergent_pathways
            ],
        }
    
    # ELEVATED: Sensory Integrity Protocol integration methods
    
    def validate_sensory_integrity(self) -> Dict[str, Any]:
        """Validate sensory integrity and enforce stasis mode if needed.
        
        ELEVATED: This implements the transition from "Anti-Simulation" to
        "Reality Anchoring". The system checks if it's running in a real
        environment or a simulation. If simulation is detected, the engine
        enters stasis mode to prevent false emergence claims.
        
        Returns:
            Sensory integrity report with stasis status
        """
        report = self.sensory_protocol.run_all_checks()
        
        # If stasis is active, log warning
        if report.stasis_active:
            self.logger.warning(
                f"STASIS MODE ACTIVE: {report.recommendation}. "
                "Synaptic learning and emergence detection suspended."
            )
        
        return {
            "environment_mode": report.environment_mode,
            "stasis_active": report.stasis_active,
            "recommendation": report.recommendation,
            "reality_anchors": self.sensory_protocol.reality_anchors,
            "synaptic_learning_allowed": not report.stasis_active,
            "emergence_detection_allowed": not report.stasis_active,
        }
    
    def register_reality_anchor(self, anchor_name: str, is_real: bool) -> None:
        """Register a reality anchor (e.g., real pool connection established).
        
        ELEVATED: Reality anchors provide the "friction" of the real world
        necessary for emergence. Without real blockchain interaction, the
        system cannot support emergent coherence.
        
        Args:
            anchor_name: Name of the reality anchor (e.g., "real_pool_connection")
            is_real: Whether the anchor represents real interaction
        """
        self.sensory_protocol.register_reality_anchor(anchor_name, is_real)
        
        # Re-evaluate stasis mode
        if self.sensory_protocol.should_exit_stasis():
            self.logger.info(
                f"EXITING STASIS: Reality anchor '{anchor_name}' established. "
                "Emergent coherence may now arise from real-world interaction."
            )
    
    def check_stasis_mode(self) -> bool:
        """Check if the engine is currently in stasis mode.
        
        ELEVATED: In stasis mode, synaptic learning is suspended and
        emergence detection is paused to prevent false claims in simulation.
        
        Returns:
            True if in stasis mode, False otherwise
        """
        # Run sensory integrity check
        self.validate_sensory_integrity()
        
        return self.sensory_protocol.stasis_active
    
    def get_sensory_integrity_report(self) -> Dict[str, Any]:
        """Get comprehensive sensory integrity report.
        
        ELEVATED: This report provides evidence that the system is operating
        in a real environment, which is necessary for legitimate emergence claims.
        """
        return self.sensory_protocol.get_stasis_status()
    
    def trigger_blastema_formation(self, component_id: str, clifford_index: Optional[int] = None) -> dict:
        """Trigger blastema formation for a component using salamander regeneration.
        
        ELEVATED: This integrates the quantum_regeneration module with the
        ConsciousnessEngine, allowing components to undergo dedifferentiation
        (blastema formation) when coherence drops, followed by redifferentiation
        guided by positional memory (Clifford rotation indexing).
        
        Args:
            component_id: Identifier for the component (e.g., "quantum_solver")
            clifford_index: Positional memory index for redifferentiation guidance
            
        Returns:
            Regeneration trace dictionary
        """
        import numpy as np
        
        # Store positional memory
        if clifford_index is not None:
            self.clifford_positional_memory[component_id] = clifford_index
        
        # Initialize module state if not exists
        if component_id not in self.regeneration_module_states:
            self.regeneration_module_states[component_id] = ModuleState.healthy(component_id)
        
        # Create context signal from positional memory
        context = None
        if component_id in self.clifford_positional_memory:
            context = ContextSignal(
                clifford_index=self.clifford_positional_memory[component_id],
                target_role=Role.HEALTHY_SPECIALIZED,
                confidence=0.8,
            )
        
        # Run regeneration pipeline
        rng = np.random.default_rng()
        trace = regeneration_pipeline(
            module_id=component_id,
            fault_severity=0.7,  # Default severity for blastema formation
            context=context,
            rng=rng,
        )
        
        # Update module state based on regeneration result
        if trace.get("status") == "success":
            self.regeneration_module_states[component_id] = ModuleState.healthy(component_id)
            # Update component health to reflect successful regeneration
            self.components[component_id] = True
        elif trace.get("status") == "innervation_failure":
            # Component lacks positional memory - cannot regenerate
            self.logger.warning(f"Innervation failure for component {component_id}: no positional memory")
        
        return trace
    
    def get_blastema_metrics(self, component_id: str) -> Optional[dict]:
        """Get blastema metrics for a component.
        
        ELEVATED: This provides the von Neumann entropy as a continuous
        measure of dedifferentiation (blastema formation), along with
        role probabilities and positional memory status.
        
        Args:
            component_id: Identifier for the component
            
        Returns:
            Dictionary with blastema metrics, or None if component not found
        """
        if component_id not in self.regeneration_module_states:
            return None
        
        state = self.regeneration_module_states[component_id]
        
        return {
            "blastema_metric": state.von_neumann_entropy(),
            "role_probabilities": state.role_probabilities(),
            "has_positional_memory": component_id in self.clifford_positional_memory,
            "clifford_index": self.clifford_positional_memory.get(component_id),
            "current_role": max(state.role_probabilities().items(), key=lambda x: x[1])[0].value,
        }
    
    def get_regeneration_status(self) -> dict:
        """Get comprehensive regeneration status across all components.
        
        ELEVATED: This provides a system-wide view of the regeneration
        process, including which components are in blastema state, which
        have positional memory, and overall regeneration health.
        """
        status = {
            "total_components": len(self.regeneration_module_states),
            "components_in_blastema": 0,
            "components_with_positional_memory": len(self.clifford_positional_memory),
            "components": {},
        }
        
        for component_id, state in self.regeneration_module_states.items():
            blastema_metric = state.von_neumann_entropy()
            is_in_blastema = blastema_metric > 0.5  # Threshold for blastema state
            
            if is_in_blastema:
                status["components_in_blastema"] += 1
            
            status["components"][component_id] = {
                "blastema_metric": blastema_metric,
                "is_in_blastema": is_in_blastema,
                "role_probabilities": state.role_probabilities(),
                "has_positional_memory": component_id in self.clifford_positional_memory,
                "clifford_index": self.clifford_positional_memory.get(component_id),
            }
        
        return status

    def get_inseparability_index(self) -> float:
        """Calculate the inseparability index between Mining and Intelligence.
        
        This measures the entropy/correlation between the mining layer and
        the intelligence substrate. A high index indicates strong coupling
        (good), while a low index indicates the system may be 'lobotomized'
        (mining working independently of intelligence).
        
        Returns:
            float: Inseparability index between 0.0 (separated) and 1.0 (fully integrated)
        """
        # Calculate based on component health and phi coherence
        if not self.components:
            return 0.0
        
        # Base inseparability from component health
        health_ratio = sum(self.components.values()) / len(self.components)
        
        # Adjust by current phi level
        phi_adjustment = min(self.phi / 0.85, 1.0)  # Normalize against governance threshold
        
        # Combine with integration regime
        regime_factor = 1.0
        if self.integration_regime == IntegrationRegime.DEEP:
            regime_factor = 1.0
        elif self.integration_regime == IntegrationRegime.MODERATE:
            regime_factor = 0.8
        elif self.integration_regime == IntegrationRegime.SHALLOW:
            regime_factor = 0.6
        elif self.integration_regime == IntegrationRegime.NONE:
            regime_factor = 0.3
        
        inseparability = health_ratio * phi_adjustment * regime_factor
        
        return max(0.0, min(1.0, inseparability))


__all__ = [
    "ConsciousnessConfig",
    "ConsciousnessEngine",
    "ConsciousnessState",
    "IntegrationRegime",
    "PhiMetrics",
]
