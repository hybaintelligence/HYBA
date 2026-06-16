"""Reflexive structural learning controller for the HYBA codebase.

This module treats the local Python codebase as the controller's deterministic
"umwelt".  It parses AST structure into a lightweight dependency graph,
computes a bounded IIT-style integration proxy, identifies counterfactual
knowledge gaps, and emits governance-gated learning proposals.

Production discipline: the controller never rewrites source files.  It returns
auditable proposals that can be reviewed or consumed by a separate, explicitly
authorized actuator.
"""

from __future__ import annotations

import ast
import math
import zlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Set, Tuple

from hyba_genesis_api.core.intelligence_fabric import PHI, PhiResonanceFabric, explain
from hyba_genesis_api.core.intelligence_manifold import IntelligenceManifold
from hyba_genesis_api.core.predictive_controller import PredictiveActiveInference
from hyba_genesis_api.core.thermal_intelligence import ThermalEnvelope

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


class IITSystemHealth:
    """Evaluate integration growth or fragmentation without external labels."""

    def __init__(self) -> None:
        self.phi_history: List[float] = []

    def compute_current_phi(self, graph: CausalGraph) -> float:
        summary = graph.summary()
        node_count = max(int(summary["node_count"]), 1)
        edge_density = float(summary["edge_density"])
        imbalance = abs(int(summary["source_count"]) - int(summary["sink_count"])) / node_count
        source_sink_balance = max(0.0, 1.0 - imbalance)
        phi_node_ratio = float(summary["phi_node_ratio"])
        raw_phi = (0.55 * edge_density * PHI) + (0.30 * source_sink_balance) + (0.15 * phi_node_ratio)
        return round(max(0.0, min(1.0, raw_phi)), 6)

    def evaluate_growth(self, graph: CausalGraph) -> PhiHealth:
        current_phi = self.compute_current_phi(graph)
        previous_phi = self.phi_history[-1] if self.phi_history else current_phi
        delta = round(current_phi - previous_phi, 6)
        self.phi_history.append(current_phi)
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
    """Observe -> evaluate -> compress -> propose loop over the local codebase."""

    def __init__(self, root_dir: Path | str):
        self.umwelt = CodebaseUmwelt(root_dir)
        self.health = IITSystemHealth()
        self.engine = CounterfactualEngine()
        self.memory = PulviniCompressionFeedback()
        self.fabric = PhiResonanceFabric()
        self.manifold = IntelligenceManifold()
        self.predictive_engine = PredictiveActiveInference(self.manifold)
        self.thermal = ThermalEnvelope()
        self.knowledge_substrate: Dict[str, Any] = {}

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

    def step(self) -> Dict[str, Any]:
        self.thermal.start_cognition()
        graph = self.umwelt.parse_structure()
        self.manifold.update_causal_graph(graph.edges)
        health = self.health.evaluate_growth(graph)
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
        }


def default_reflexive_root() -> Path:
    """Return the scoped pythia_mining root used by the production API."""

    return Path(__file__).resolve().parents[2] / "pythia_mining"
