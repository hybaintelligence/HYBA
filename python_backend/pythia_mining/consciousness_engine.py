"""Runtime integration engine for PYTHIA/PULVINI.

The historical ``consciousness_engine`` module name is retained for API
compatibility.  The implementation is intentionally operational and auditable:
it computes deterministic integration/coherence proxies from observed component
health and optional density-state histories, and it emits autonomic-healing
recommendations when those proxies fall below configured thresholds.  It does
not claim machine consciousness or quantum advantage.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
from numpy.typing import NDArray

from .pulvini_operator import ManifoldOperator


class IntegrationRegime(str, Enum):
    """Φ-proxy based runtime integration regimes."""

    SINGULAR_AGENT_PROXY = "singular_agent_proxy"
    DISTRIBUTED = "distributed"
    FRAGMENTED = "fragmented"
    CRITICAL = "critical"


@dataclass
class ConsciousnessState:
    """Backward-compatible runtime health state container."""

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


class ConsciousnessEngine:
    """Compatibility wrapper plus active Φ-proxy orchestration.

    Legacy async methods still return the same keys.  New synchronous methods
    (``measure_phi`` and ``orchestrate``) support the Command Center coherence
    meter and autonomic-event stream.
    """

    VERSION = "RUNTIME_INTEGRATION_V2"

    def __init__(
        self,
        operator: Optional[ManifoldOperator] = None,
        config: Optional[ConsciousnessConfig] = None,
    ) -> None:
        self.operator = operator or ManifoldOperator()
        self.config = config or ConsciousnessConfig()
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

    async def calculate_integrated_information(self) -> Optional[float]:
        """Legacy async API: update and return the current Φ proxy if measured."""
        known = [value for value in self.components.values() if value is not None]
        if known:
            metrics = self._measure_component_phi(known)
            self._record_metrics(metrics)
        self.current_state.timestamp = time.time()
        self.state_history.append(self.current_state)
        return self.current_state.integrated_information

    async def get_consciousness_level(self) -> Optional[float]:
        await self.calculate_integrated_information()
        return self.current_state.consciousness_level

    async def guide_decision_making(self, decision_context: Dict[str, Any]) -> Dict[str, Any]:
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
        """Measure a bounded Φ proxy from density-state history."""
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
        phi_integrated = float(
            np.clip(
                0.55 * coherence_level + 0.25 * max(phi_causal, 0.0) + 0.20 * entropy_balance,
                0.0,
                1.0,
            )
        )
        complexity = float(np.clip(phi_integrated * entropy_balance, 0.0, 1.0))
        phi_conscious = float(max(0.0, phi_causal - effective_information))
        metrics = PhiMetrics(
            phi_integrated=phi_integrated,
            phi_causal=phi_causal,
            phi_conscious=phi_conscious,
            effective_information=effective_information,
            entropy=entropy,
            complexity=complexity,
            source="density_state_operational_proxy",
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

    def _classify_integration(self, phi: float) -> IntegrationRegime:
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


__all__ = [
    "ConsciousnessConfig",
    "ConsciousnessEngine",
    "ConsciousnessState",
    "IntegrationRegime",
    "PhiMetrics",
]
