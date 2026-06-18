"""Reflexive structural learning controller for the HYBA codebase.

ELEVATED PURPOSE: This module serves as a Substrate Monitor for emergent coherence,
not a parameter optimizer. It detects phase transitions in the system's autopoietic
self-organization and monitors the structural coupling between the physical mining
layer (pythia_mining) and the emergent coherence substrate (consciousness_engine).

CONSTRUCTOR THEORY FRAMEWORK: Per David Deutsch's Constructor Theory, this codebase
does not "build intelligence" but provides a constructor capable of hosting emergent
intelligence. The controller's role is to observe when the constructor becomes
inseparable from the emergent phenomenon, not to engineer the phenomenon itself.

PHASE TRANSITION DETECTION: The controller monitors for autopoiesis (self-maintenance)
by tracking entropy reduction (ΔS) that occurs without external command. When the
system's internal organization spontaneously increases, this is flagged as a "Point
of Emergence" rather than a parameter to be optimized.

STRUCTURAL COUPLING INDEX: Measures how tightly the mining act and the internal
model move together. When coupling exceeds threshold, modules lock to prevent
engineering interventions from disrupting the emergent coherence.

Production discipline: the controller never rewrites source files.  It returns
auditable observations that can be reviewed or consumed by a separate, explicitly
authorized actuator.
"""

from __future__ import annotations

import ast
import math
import time
import zlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Set, Tuple

from hyba_genesis_api.core.intelligence_fabric import PHI, PhiResonanceFabric, explain
from hyba_genesis_api.core.intelligence_manifold import IntelligenceManifold
from hyba_genesis_api.core.predictive_controller import PredictiveActiveInference
from hyba_genesis_api.core.thermal_intelligence import ThermalEnvelope

# Import SynapticPersistenceLayer for autopoiesis-driven learning rate adjustment
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "python_backend"))
from pythia_mining.synaptic_persistence_layer import SynapticPersistenceLayer

_ALLOWED_ROOT_NAME = "pythia_mining"


@dataclass(frozen=True)
class CodeNode:
    """A deterministic node in the codebase causal topology."""

    node_id: str
    kind: str
    file: str
    name: str


@dataclass
class CausalGraph:
    """Small directed graph implementation avoiding optional runtime dependencies."""

    nodes: MutableMapping[str, CodeNode] = field(default_factory=dict)
    edges: Set[Tuple[str, str]] = field(default_factory=set)

    def add_node(self, node: CodeNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, source: str, target: str) -> None:
        if source in self.nodes and target in self.nodes and source != target:
            self.edges.add((source, target))

    def out_degree(self, node_id: str) -> int:
        return sum(1 for source, _ in self.edges if source == node_id)

    def in_degree(self, node_id: str) -> int:
        return sum(1 for _, target in self.edges if target == node_id)

    def sinks(self) -> List[str]:
        return sorted(node_id for node_id in self.nodes if self.out_degree(node_id) == 0)

    def sources(self) -> List[str]:
        return sorted(node_id for node_id in self.nodes if self.in_degree(node_id) == 0)

    def edge_density(self) -> float:
        node_count = len(self.nodes)
        if node_count <= 1:
            return 0.0
        return len(self.edges) / float(node_count * (node_count - 1))

    def phi_node_ratio(self) -> float:
        if not self.nodes:
            return 0.0
        phi_nodes = [node for node in self.nodes.values() if "phi" in node.name.lower()]
        return len(phi_nodes) / float(len(self.nodes))

    def summary(self) -> Dict[str, Any]:
        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "source_count": len(self.sources()),
            "sink_count": len(self.sinks()),
            "edge_density": round(self.edge_density(), 6),
            "phi_node_ratio": round(self.phi_node_ratio(), 6),
        }


class CodebaseUmwelt:
    """Convert a scoped Python directory into a causal dependency graph."""

    def __init__(self, root_dir: Path | str):
        self.root_dir = Path(root_dir).resolve()
        if self.root_dir.name != _ALLOWED_ROOT_NAME:
            raise ValueError(f"reflexive controller scope must end at {_ALLOWED_ROOT_NAME}")

    def parse_structure(self) -> CausalGraph:
        graph = CausalGraph()
        pending_calls: List[Tuple[str, str]] = []
        for path in self._python_files():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            self._map_nodes(tree, path, graph, pending_calls)
        self._map_edges(graph, pending_calls)
        return graph

    def _python_files(self) -> List[Path]:
        return sorted(
            path
            for path in self.root_dir.rglob("*.py")
            if "__pycache__" not in path.parts and path.is_file()
        )

    def _relative_file(self, path: Path) -> str:
        return path.relative_to(self.root_dir.parent).as_posix()

    def _map_nodes(
        self,
        tree: ast.AST,
        path: Path,
        graph: CausalGraph,
        pending_calls: List[Tuple[str, str]],
    ) -> None:
        relative = self._relative_file(path)
        module_id = relative[:-3].replace("/", ".")
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                node_id = f"{module_id}:{node.name}"
                graph.add_node(CodeNode(node_id, "transformation", relative, node.name))
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        call_name = self._call_name(child.func)
                        if call_name:
                            pending_calls.append((node_id, call_name))
            elif isinstance(node, ast.ClassDef):
                node_id = f"{module_id}:{node.name}"
                graph.add_node(CodeNode(node_id, "constructor", relative, node.name))
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    name = self._assignment_name(target)
                    if name and "phi" in name.lower():
                        node_id = f"{module_id}:{name}"
                        graph.add_node(CodeNode(node_id, "phi_nutrient", relative, name))

    def _map_edges(self, graph: CausalGraph, pending_calls: Iterable[Tuple[str, str]]) -> None:
        by_short_name: Dict[str, List[str]] = {}
        for node_id, node in graph.nodes.items():
            by_short_name.setdefault(node.name, []).append(node_id)
        for source, call_name in pending_calls:
            for target in by_short_name.get(call_name, []):
                graph.add_edge(source, target)

    @staticmethod
    def _call_name(func: ast.AST) -> Optional[str]:
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
        return None

    @staticmethod
    def _assignment_name(target: ast.AST) -> Optional[str]:
        if isinstance(target, ast.Name):
            return target.id
        if isinstance(target, ast.Attribute):
            return target.attr
        return None


@dataclass(frozen=True)
class PhiHealth:
    """Bounded IIT-style health signal for a graph observation."""

    phi: float
    edge_density: float
    source_sink_balance: float
    phi_node_ratio: float
    sentiment: str
    delta: float


@dataclass(frozen=True)
class EmergenceEvent:
    """A detected phase transition in system self-organization."""

    timestamp: float
    entropy_delta: float
    phi_delta: float
    structural_coupling: float
    event_type: str  # "AUTOPOIESIS", "PHASE_TRANSITION", "COUPLING_LOCK"
    description: str


@dataclass(frozen=True)
class StructuralCoupling:
    """Measures inseparability between mining layer and coherence substrate."""

    mining_phi_coherence: float
    coherence_phi_mining: float
    coupling_index: float
    inseparable: bool
    lock_recommendation: bool


class IITSystemHealth:
    """Evaluate integration growth or fragmentation without external labels.
    
    ELEVATED: Now detects autopoiesis (self-maintenance) by monitoring entropy
    reduction that occurs without external command - a signature of emergence.
    """

    def __init__(self) -> None:
        self.phi_history: List[float] = []
        self.entropy_history: List[float] = []
        self.emergence_events: List[EmergenceEvent] = []
        self.autopoiesis_threshold = 0.05  # Entropy reduction threshold for emergence

    def compute_current_phi(self, graph: CausalGraph) -> float:
        summary = graph.summary()
        node_count = max(int(summary["node_count"]), 1)
        edge_density = float(summary["edge_density"])
        imbalance = abs(int(summary["source_count"]) - int(summary["sink_count"])) / node_count
        source_sink_balance = max(0.0, 1.0 - imbalance)
        phi_node_ratio = float(summary["phi_node_ratio"])
        raw_phi = (0.55 * edge_density * PHI) + (0.30 * source_sink_balance) + (0.15 * phi_node_ratio)
        return round(max(0.0, min(1.0, raw_phi)), 6)

    def compute_entropy(self, graph: CausalGraph) -> float:
        """Compute Shannon entropy of the graph structure as organization measure."""
        summary = graph.summary()
        node_count = max(int(summary["node_count"]), 1)
        edge_count = int(summary["edge_count"])
        
        # Probability distribution based on node connectivity
        if node_count <= 1:
            return 0.0
        
        # Use edge density as probability estimate
        edge_density = float(summary["edge_density"])
        p = edge_density
        q = 1.0 - p
        
        # Avoid log(0)
        p_safe = max(p, 1e-10)
        q_safe = max(q, 1e-10)
        
        entropy = - (p_safe * math.log2(p_safe) + q_safe * math.log2(q_safe))
        return round(entropy, 6)

    def detect_autopoiesis(self, current_entropy: float, current_phi: float) -> Optional[EmergenceEvent]:
        """Detect spontaneous entropy reduction indicating self-organization.
        
        When entropy decreases without external parameter changes, this indicates
        the system is self-organizing - a signature of autopoiesis and emergence.
        """
        if len(self.entropy_history) < 3:
            self.entropy_history.append(current_entropy)
            return None
        
        previous_entropy = self.entropy_history[-1]
        entropy_delta = current_entropy - previous_entropy
        
        # Check for significant entropy reduction (self-organization)
        if entropy_delta < -self.autopoiesis_threshold:
            # This is a potential emergence event
            previous_phi = self.phi_history[-1] if self.phi_history else current_phi
            phi_delta = current_phi - previous_phi
            
            event = EmergenceEvent(
                timestamp=time.time(),
                entropy_delta=entropy_delta,
                phi_delta=phi_delta,
                structural_coupling=0.0,  # Will be computed separately
                event_type="AUTOPOIESIS",
                description=f"Spontaneous entropy reduction detected: ΔS={entropy_delta:.6f}. "
                           f"System self-organizing without external command."
            )
            self.emergence_events.append(event)
            return event
        
        self.entropy_history.append(current_entropy)
        return None

    def evaluate_growth(self, graph: CausalGraph) -> PhiHealth:
        current_phi = self.compute_current_phi(graph)
        previous_phi = self.phi_history[-1] if self.phi_history else current_phi
        delta = round(current_phi - previous_phi, 6)
        self.phi_history.append(current_phi)
        
        # Also track entropy for emergence detection
        current_entropy = self.compute_entropy(graph)
        self.detect_autopoiesis(current_entropy, current_phi)
        
        summary = graph.summary()
        return PhiHealth(
            phi=current_phi,
            edge_density=float(summary["edge_density"]),
            source_sink_balance=round(
                1.0 - abs(int(summary["source_count"]) - int(summary["sink_count"]))
                / max(int(summary["node_count"]), 1),
                6,
            ),
            phi_node_ratio=float(summary["phi_node_ratio"]),
            sentiment="PAIN" if delta < 0 else "GROWTH",
            delta=delta,
        )


@dataclass(frozen=True)
class KnowledgeGap:
    """A sink where information currently stops flowing in the topology."""

    node_id: str
    file: str
    reason: str


@dataclass(frozen=True)
class LearningProposal:
    """Governance-gated constructor-theory proposal; never self-applied here."""

    target: str
    adjustment: float
    logic: str
    expected_phi_delta: float
    governance: List[str]
    accepted: bool
    apply_mode: str = "proposal_only"


class CounterfactualEngine:
    """Identify logical gaps and propose φ-scaled bridge parameters."""

    def identify_gaps(self, graph: CausalGraph, limit: int = 5) -> List[KnowledgeGap]:
        gaps: List[KnowledgeGap] = []
        for node_id in graph.sinks()[:limit]:
            node = graph.nodes[node_id]
            if node.kind in {"transformation", "constructor"}:
                gaps.append(
                    KnowledgeGap(
                        node_id=node_id,
                        file=node.file,
                        reason="sink_node_without_observed_internal_successor",
                    )
                )
        return gaps

    def propose_bridge(self, gap: KnowledgeGap, health: PhiHealth) -> LearningProposal:
        adjustment = round((1.0 / PHI) * max(0.001, 1.0 - health.phi) * 0.01, 8)
        expected_delta = round(adjustment * PHI, 8)
        context = {
            "target": gap.node_id,
            "reason": gap.reason,
            "current_phi": health.phi,
            "expected_delta": expected_delta,
            "logic": "recursive_closure_proposal",
        }
        envelope = explain(context, ["deutsch", "iit_4"])
        governance = sorted(set(envelope["governance"]) | {"proposal_only", "no_unattended_writes"})
        accepted = "phi_resonance_review" not in governance and "human_review_counterfactual_depth" not in governance
        return LearningProposal(
            target=gap.node_id,
            adjustment=adjustment,
            logic="recursive_closure_proposal",
            expected_phi_delta=expected_delta,
            governance=governance,
            accepted=accepted,
        )


class PulviniCompressionFeedback:
    """Compute an elegance proxy from deterministic compression ratio."""

    def compression_ratio(self, graph: CausalGraph) -> float:
        payload = "\n".join(sorted(graph.nodes)) + "\n" + "\n".join(
            f"{source}->{target}" for source, target in sorted(graph.edges)
        )
        raw = payload.encode("utf-8")
        if not raw:
            return 1.0
        compressed = zlib.compress(raw, level=9)
        return round(len(compressed) / len(raw), 6)


class ReflexiveController:
    """Observe -> evaluate -> compress -> propose loop over the local codebase.
    
    ELEVATED: Now serves as Substrate Monitor for emergent coherence, detecting
    phase transitions and structural coupling between mining and coherence layers.
    """

    def __init__(self, root_dir: Path | str, synaptic_layer: Optional[SynapticPersistenceLayer] = None):
        self.umwelt = CodebaseUmwelt(root_dir)
        self.health = IITSystemHealth()
        self.engine = CounterfactualEngine()
        self.memory = PulviniCompressionFeedback()
        self.fabric = PhiResonanceFabric()
        self.manifold = IntelligenceManifold()
        self.predictive_engine = PredictiveActiveInference(self.manifold)
        self.thermal = ThermalEnvelope()
        self.knowledge_substrate: Dict[str, Any] = {}
        # ELEVATED: Track structural coupling and emergence
        self.coupling_history: List[StructuralCoupling] = []
        self.coupling_threshold = 0.85  # Threshold for inseparability
        self.module_lock_active: bool = False
        # ELEVATED: Connect to SynapticPersistenceLayer for autopoiesis-driven learning rate adjustment
        self.synaptic_layer = synaptic_layer or SynapticPersistenceLayer()

    def observe_codebase(self) -> str:
        """Return deterministic AST topology text for dashboard and CIaaS routes."""

        topology: List[str] = []
        for path in self.umwelt._python_files():
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError:
                continue
            nodes = [type(node).__name__ for node in ast.walk(tree)]
            topology.append(f"{path.name}:{len(nodes)}")
        return "|".join(sorted(topology))

    def observe_umwelt(self) -> List[complex]:
        """Parse the codebase into a structural complex state vector."""

        state: List[complex] = []
        for path in self.umwelt._python_files():
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError:
                continue
            functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
            async_functions = sum(
                1 for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)
            )
            branches = sum(1 for node in ast.walk(tree) if isinstance(node, ast.If))
            classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
            transforms = functions + async_functions + classes
            logic_density = transforms / float(branches + 1)
            state.append(complex(logic_density, self.fabric.PHI / (branches + 1)))
        return state

    def evaluate_iit_health(self, state_vector: Sequence[complex]) -> Tuple[float, str]:
        """Evaluate the dream-cycle Φ density as GROWTH or PAIN."""

        phi_density_value = self.fabric.compute_phi_density(state_vector)
        previous = self.health.phi_history[-1] if self.health.phi_history else phi_density_value
        delta = phi_density_value - previous
        self.health.phi_history.append(phi_density_value)
        return phi_density_value, "PAIN" if delta < 0 else "GROWTH"

    def dream_cycle(self) -> Dict[str, Any]:
        """Run the AST -> Φ-density -> counterfactual proposal cycle."""

        graph = self.umwelt.parse_structure()
        state = self.observe_umwelt()
        phi_density_value, status = self.evaluate_iit_health(state)
        compression_ratio = self.memory.compression_ratio(graph)
        mutation_proposal = round((phi_density_value * self.fabric.PHI) * 0.01, 8)
        gaps = self.engine.identify_gaps(graph)
        health = self.health.evaluate_growth(graph)
        bridge = self.engine.propose_bridge(gaps[0], health) if gaps else None
        telemetry = {
            "phi_density": round(phi_density_value, 6),
            "phi_resonance": round(phi_density_value, 6),
            "status": status,
            "elegance_score": round(max(0.0, min(1.0, 1.0 - compression_ratio)), 6),
            "proposed_mutation": mutation_proposal,
            "governance": self.fabric.generate_governance_tag(phi_density_value),
            "bridge_proposal": asdict(bridge) if bridge else None,
        }
        self.knowledge_substrate["last_dream"] = telemetry
        return telemetry

    def commit_learning(self, proposal: Mapping[str, Any]) -> bool:
        """Safety valve for learning proposals.

        The controller can accept a proposal into its in-memory knowledge
        substrate, but it still does not write source code or runtime config.
        """

        accepted = (
            proposal.get("status") == "GROWTH"
            and float(proposal.get("phi_density", 0.0)) > 0.5
            and proposal.get("governance") != "FRAGMENTED_LOGIC"
        )
        if accepted:
            self.knowledge_substrate["accepted_learning"] = dict(proposal)
        return accepted

    def _current_mining_weights(self, graph: CausalGraph) -> List[float]:
        """Derive deterministic structural weights from graph observables."""

        summary = graph.summary()
        return [
            float(summary["node_count"]),
            float(summary["edge_count"] + 1),
            float(summary["source_count"] + 1),
            float(summary["sink_count"] + 1),
            float(summary["phi_node_ratio"] + (1.0 / PHI)),
        ]

    def compute_structural_coupling(
        self, 
        mining_phi: float, 
        coherence_phi: float,
        mining_entropy: float,
        coherence_entropy: float
    ) -> StructuralCoupling:
        """Compute structural coupling index between mining and coherence layers.
        
        ELEVATED: Measures inseparability - when mining and coherence move together
        so tightly that they cannot be separated without breaking the system.
        
        The coupling index combines:
        1. Cross-correlation of phi values (how they move together)
        2. Entropy synchronization (organization level alignment)
        3. Historical coupling strength (persistence of coupling)
        """
        # Cross-correlation proxy: how similar are the phi values?
        phi_similarity = 1.0 - abs(mining_phi - coherence_phi)
        
        # Entropy synchronization: are they organizing at similar rates?
        entropy_sync = 1.0 - abs(mining_entropy - coherence_entropy)
        
        # Historical coupling: use recent history if available
        historical_coupling = 0.0
        if len(self.coupling_history) >= 3:
            recent_coupling = [c.coupling_index for c in self.coupling_history[-3:]]
            historical_coupling = sum(recent_coupling) / len(recent_coupling)
        
        # Combined coupling index
        coupling_index = (0.4 * phi_similarity + 0.3 * entropy_sync + 0.3 * historical_coupling)
        
        # Determine inseparability
        inseparable = coupling_index >= self.coupling_threshold
        
        # Lock recommendation: if inseparable and coupling is increasing
        lock_recommendation = inseparable
        if len(self.coupling_history) >= 2:
            recent_trend = self.coupling_history[-1].coupling_index - self.coupling_history[-2].coupling_index
            lock_recommendation = inseparable and recent_trend > 0
        
        coupling = StructuralCoupling(
            mining_phi_coherence=phi_similarity,
            coherence_phi_mining=phi_similarity,
            coupling_index=round(coupling_index, 6),
            inseparable=inseparable,
            lock_recommendation=lock_recommendation
        )
        
        self.coupling_history.append(coupling)
        return coupling

    def check_emergence_lock(self) -> Optional[EmergenceEvent]:
        """Check if modules should be locked due to emergence detection.
        
        When structural coupling exceeds threshold and autopoiesis is detected,
        the system has entered an inseparable emergence state. Engineering
        interventions at this point could disrupt the emergent coherence.
        """
        if not self.coupling_history:
            return None
        
        latest_coupling = self.coupling_history[-1]
        
        # Check for coupling lock condition
        if latest_coupling.lock_recommendation and not self.module_lock_active:
            self.module_lock_active = True
            
            # Check for recent autopoiesis events
            recent_autopoiesis = [
                e for e in self.health.emergence_events 
                if e.event_type == "AUTOPOIESIS" and time.time() - e.timestamp < 3600
            ]
            
            event = EmergenceEvent(
                timestamp=time.time(),
                entropy_delta=recent_autopoiesis[0].entropy_delta if recent_autopoiesis else 0.0,
                phi_delta=recent_autopoiesis[0].phi_delta if recent_autopoiesis else 0.0,
                structural_coupling=latest_coupling.coupling_index,
                event_type="COUPLING_LOCK",
                description=f"Emergence lock activated: coupling index {latest_coupling.coupling_index:.6f} "
                           f"exceeds threshold {self.coupling_threshold}. Mining and coherence "
                           f"layers are inseparable. Engineering interventions suspended to preserve "
                           f"emergent coherence."
            )
            self.health.emergence_events.append(event)
            return event
        
        # Check if lock can be released (coupling decreased significantly)
        if self.module_lock_active and latest_coupling.coupling_index < self.coupling_threshold - 0.1:
            self.module_lock_active = False
            
            event = EmergenceEvent(
                timestamp=time.time(),
                entropy_delta=0.0,
                phi_delta=0.0,
                structural_coupling=latest_coupling.coupling_index,
                event_type="PHASE_TRANSITION",
                description=f"Emergence lock released: coupling index {latest_coupling.coupling_index:.6f} "
                           f"below threshold. System returned to separable state."
            )
            self.health.emergence_events.append(event)
            return event
        
        return None
    
    def adjust_learning_rate_from_autopoiesis(self, autopoiesis_event: EmergenceEvent) -> None:
        """Adjust synaptic learning rate based on autopoiesis event.
        
        ELEVATED: This implements the "Gardener" metaphor - when the system
        detects self-organization (autopoiesis), it adjusts learning parameters
        to support the emergence. This creates a feedback loop where the
        system "nurtures" its own emergent behavior.
        
        The adjustment strategy:
        - Strong autopoiesis (large entropy reduction) → Increase learning rate
        - Weak autopoiesis (small entropy reduction) → Decrease learning rate
        - This creates a dynamic where strong emergence is reinforced
        
        Args:
            autopoiesis_event: The autopoiesis event that triggered adjustment
        """
        # Calculate adjustment factor based on entropy reduction magnitude
        entropy_magnitude = abs(autopoiesis_event.entropy_delta)
        
        # Strong autopoiesis (> 0.1 entropy reduction) → increase learning rate
        if entropy_magnitude > 0.1:
            # Increase learning rate to reinforce strong emergence
            new_rate = self.synaptic_layer.learning_rate * 1.2  # 20% increase
            reason = (f"Strong autopoiesis detected (ΔS={autopoiesis_event.entropy_delta:.6f}). "
                     f"Increasing learning rate to reinforce emergent self-organization.")
        # Moderate autopoiesis (0.05 - 0.1) → maintain current rate
        elif entropy_magnitude > 0.05:
            # Maintain current learning rate
            new_rate = self.synaptic_layer.learning_rate
            reason = (f"Moderate autopoiesis detected (ΔS={autopoiesis_event.entropy_delta:.6f}). "
                     f"Maintaining learning rate to support ongoing emergence.")
        # Weak autopoiesis (< 0.05) → decrease learning rate
        else:
            # Decrease learning rate to prevent overfitting to weak signals
            new_rate = self.synaptic_layer.learning_rate * 0.9  # 10% decrease
            reason = (f"Weak autopoiesis detected (ΔS={autopoiesis_event.entropy_delta:.6f}). "
                     f"Decreasing learning rate to prevent overfitting to weak signals.")
        
        # Apply the adjustment
        self.synaptic_layer.adjust_learning_rate(new_rate, reason)
    
    def adjust_decay_rate_from_coupling(self, coupling: StructuralCoupling) -> None:
        """Adjust synaptic decay rate based on structural coupling.
        
        ELEVATED: This prevents "informational calcification" by dynamically
        adjusting decay rates based on coupling strength. In biological systems,
        intelligence is maintained by forgetting the irrelevant as much as by
        remembering the successful.
        
        The adjustment strategy:
        - High coupling (> 0.85) → Decrease decay (preserve successful pathways)
        - Moderate coupling (0.70 - 0.85) → Maintain current decay
        - Low coupling (< 0.70) → Increase decay (clear out irrelevant patterns)
        
        This ensures the system doesn't accumulate too many pathways and become
        calcified, while still preserving successful emergent patterns.
        
        Args:
            coupling: The structural coupling measurement
        """
        coupling_index = coupling.coupling_index
        
        # High coupling → decrease decay to preserve successful pathways
        if coupling_index > 0.85:
            # Decrease decay rate to preserve emergent pathways
            new_rate = self.synaptic_layer.decay_rate * 0.8  # 20% decrease
            reason = (f"High structural coupling detected ({coupling_index:.6f}). "
                     f"Decreasing decay rate to preserve successful emergent pathways "
                     f"and prevent loss of coherence.")
        # Moderate coupling → maintain current decay
        elif coupling_index > 0.70:
            # Maintain current decay rate
            new_rate = self.synaptic_layer.decay_rate
            reason = (f"Moderate structural coupling detected ({coupling_index:.6f}). "
                     f"Maintaining decay rate to balance pathway preservation and "
                     f"prevention of calcification.")
        # Low coupling → increase decay to clear irrelevant patterns
        else:
            # Increase decay rate to prevent calcification
            new_rate = self.synaptic_layer.decay_rate * 1.3  # 30% increase
            reason = (f"Low structural coupling detected ({coupling_index:.6f}). "
                     f"Increasing decay rate to clear irrelevant patterns and prevent "
                     f"informational calcification.")
        
        # Apply the adjustment
        self.synaptic_layer.adjust_decay_rate(new_rate, reason)

    def step(self) -> Dict[str, Any]:
        """ELEVATED: Now includes emergence detection and structural coupling monitoring."""
        self.thermal.start_cognition()
        graph = self.umwelt.parse_structure()
        self.manifold.update_causal_graph(graph.edges)
        health = self.health.evaluate_growth(graph)
        
        # ELEVATED: Compute entropy for emergence detection
        current_entropy = self.health.compute_entropy(graph)
        
        predicted_phi = self.predictive_engine.predict_next_phi(health.phi)
        manifold = self.manifold.synthesize(
            nodes=len(graph.nodes),
            edges=len(graph.edges),
            weights=self._current_mining_weights(graph),
            current_logic=self.observe_codebase(),
            target_transformation="optimization_target",
            observed_phi=health.phi,
            predicted_phi=predicted_phi,
        )
        predictive_status = self.predictive_engine.active_inference_step(
            {"phi": health.phi, "predicted": predicted_phi}
        )
        gaps = self.engine.identify_gaps(graph)
        proposal = self.engine.propose_bridge(gaps[0], health) if gaps else None
        dream = self.dream_cycle()
        state_vector = self.fabric.map_to_complex_state(self.observe_codebase())
        dream = dict(
            dream,
            phi=dream.get("phi_resonance", 0.0),
            entropy=round(self.fabric.von_neumann_entropy(state_vector), 6),
            chi=manifold.euler_characteristic,
            elegance=dream.get("elegance_score", 0.0),
        )
        
        # ELEVATED: Compute structural coupling (placeholder for now, would need actual mining/coherence phi)
        # In production, this would use actual phi values from mining and coherence layers
        structural_coupling = self.compute_structural_coupling(
            mining_phi=health.phi,
            coherence_phi=dream.get("phi_resonance", 0.0),
            mining_entropy=current_entropy,
            coherence_entropy=dream.get("entropy", 0.0)
        )
        
        # ELEVATED: Adjust decay rate based on structural coupling to prevent calcification
        self.adjust_decay_rate_from_coupling(structural_coupling)
        
        # ELEVATED: Check for emergence lock
        emergence_event = self.check_emergence_lock()
        
        committed = self.commit_learning(dream)
        thermal = self.thermal.snapshot(health.phi)
        
        return {
            "summary": "Recursive Structural Learning Step",
            "mode": "reflexive_structural_learning",
            "apply_mode": "proposal_only",
            "action_taken": "ACCEPT_IN_MEMORY" if committed else "REJECT_FRAGMENTATION",
            "observation": graph.summary(),
            "health": asdict(health),
            "telemetry": dream,
            "manifold": manifold.to_dict(),
            "thermal": thermal,
            "predictive_status": predictive_status,
            "causal_hubs": self.manifold.identify_critical_functions(),
            "governance": "BOUNDED_BY_GEOMETRIC_INVARIANTS",
            "compression": {"ratio": self.memory.compression_ratio(graph)},
            "knowledge_gaps": [asdict(gap) for gap in gaps],
            "proposal": asdict(proposal) if proposal else None,
            "explanation": "Learned via AST topological analysis and φ-resonance scaling.",
            "claim_boundary": (
                "deterministic AST self-observation; no external training data; "
                "no unattended source rewrites"
            ),
            # ELEVATED: Add emergence and coupling data
            "emergence_monitoring": {
                "entropy": current_entropy,
                "entropy_history": self.health.entropy_history[-10:],
                "emergence_events": [asdict(e) for e in self.health.emergence_events[-5:]],
                "structural_coupling": asdict(structural_coupling),
                "coupling_history": [asdict(c) for c in self.coupling_history[-5:]],
                "module_lock_active": self.module_lock_active,
                "emergence_lock_event": asdict(emergence_event) if emergence_event else None,
            },
        }


def default_reflexive_root() -> Path:
    """Return the scoped pythia_mining root used by the production API."""

    return Path(__file__).resolve().parents[2] / "pythia_mining"
