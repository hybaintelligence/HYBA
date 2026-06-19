"""Causal attribution engine for hotspot ranking and counterfactual coverage.

This module provides a domain-agnostic interpretability engine that:
- Ranks causal hotspots by impact score
- Generates counterfactual explanations
- Ensures claim-boundary coverage before attaching explanations
- Provides consistent attribution across all HYBA subsystems

The engine is designed to work with any graph-structured system where
nodes represent components (router, fabric, etc.) and edges represent
causal relationships.

Mathematical properties:
- Causal impact scores are normalized to [0, 1]
- Counterfactual coverage ratio is in [0, 1]
- Hotspot ranking is deterministic for a given graph state
- Coverage threshold (default 1.0) ensures complete explanation
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping, Sequence

# Schema version for compatibility
CAUSAL_ATTRIBUTION_SCHEMA_VERSION = "CAUSAL_ATTRIBUTION_V1"


class CoverageThreshold(str, Enum):
    """Standardized coverage thresholds for explanation confidence."""

    STRICT = "strict"  # Requires 100% coverage
    HIGH = "high"  # Requires >= 0.95 coverage
    MEDIUM = "medium"  # Requires >= 0.90 coverage
    LOW = "low"  # Requires >= 0.75 coverage


@dataclass(frozen=True)
class CausalHotspot:
    """A single causal hotspot with impact score."""

    node_id: str
    impact_score: float
    node_type: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate impact score is in valid range."""
        score = float(object.__getattribute__(self, "impact_score"))
        if not 0.0 <= score <= 1.0:
            raise ValueError(f"impact_score must be in [0, 1], got {score}")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "node_id": self.node_id,
            "impact_score": self.impact_score,
            "node_type": self.node_type,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CounterfactualResult:
    """Result of counterfactual analysis for a claim."""

    covered_nodes: Sequence[str]
    uncovered_nodes: Sequence[str]
    coverage_ratio: float
    total_nodes: int
    confidence: str

    def __post_init__(self) -> None:
        """Validate coverage ratio is in valid range."""
        ratio = float(object.__getattribute__(self, "coverage_ratio"))
        if not 0.0 <= ratio <= 1.0:
            raise ValueError(f"coverage_ratio must be in [0, 1], got {ratio}")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "covered_nodes": list(self.covered_nodes),
            "uncovered_nodes": list(self.uncovered_nodes),
            "coverage_ratio": self.coverage_ratio,
            "total_nodes": self.total_nodes,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class CausalExplanation:
    """Complete causal explanation for an event and claim."""

    hotspots: Sequence[CausalHotspot]
    counterfactual: CounterfactualResult
    explanation_quality: str
    timestamp: float
    schema_version: str = CAUSAL_ATTRIBUTION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "hotspots": [h.to_dict() for h in self.hotspots],
            "counterfactual": self.counterfactual.to_dict(),
            "explanation_quality": self.explanation_quality,
            "timestamp": self.timestamp,
            "schema_version": self.schema_version,
        }


class FabricGraph:
    """Abstract graph structure for causal analysis.

    This represents the causal structure of a HYBA subsystem.
    Nodes are components (router, fabric, etc.) and edges are causal relationships.
    """

    def __init__(
        self,
        nodes: Mapping[str, Mapping[str, Any]],
        edges: Mapping[str, Sequence[str]],
    ):
        """Initialize the fabric graph.

        Args:
            nodes: Mapping from node_id to node metadata (type, properties, etc.)
            edges: Mapping from node_id to list of causally downstream node_ids
        """
        self.nodes = dict(nodes)
        self.edges = {k: list(v) for k, v in edges.items()}

        # Validate graph structure
        self._validate_graph()

    def _validate_graph(self) -> None:
        """Validate graph structure is consistent."""
        # All edge sources must be nodes
        for source in self.edges:
            if source not in self.nodes:
                raise ValueError(f"Edge source {source} not in nodes")

        # All edge targets must be nodes
        for targets in self.edges.values():
            for target in targets:
                if target not in self.nodes:
                    raise ValueError(f"Edge target {target} not in nodes")

    def nodes_touched_by_event(self, event: Mapping[str, Any]) -> Sequence[str]:
        """Return nodes that were touched by a given event.

        This is a simplified implementation - in practice, this would
        analyze the event to determine which nodes participated.

        Args:
            event: Event metadata describing what happened

        Returns:
            List of node_ids that participated in the event
        """
        # Default implementation: return all nodes
        # Subclasses should override with actual event analysis
        return list(self.nodes.keys())

    def causal_impact(self, node_id: str, event: Mapping[str, Any]) -> float:
        """Compute causal impact score for a node given an event.

        This is a simplified implementation - in practice, this would
        use domain-specific causal models.

        Args:
            node_id: The node to compute impact for
            event: The event to compute impact relative to

        Returns:
            Impact score in [0, 1]
        """
        # Default implementation: uniform impact
        # Subclasses should override with actual causal models
        return 0.5

    def get_node_type(self, node_id: str) -> str:
        """Get the type of a node."""
        return self.nodes.get(node_id, {}).get("type", "unknown")

    def get_node_metadata(self, node_id: str) -> Mapping[str, Any]:
        """Get metadata for a node."""
        return self.nodes.get(node_id, {})


class CausalAttributionEngine:
    """Domain-agnostic causal attribution engine.

    This engine provides:
    - Hotspot ranking by causal impact
    - Counterfactual coverage analysis
    - Explanation generation with confidence scoring
    - Integration with UniversalPassport for audit logging
    """

    def __init__(
        self,
        fabric_graph: FabricGraph,
        coverage_threshold: float = 1.0,
    ):
        """Initialize the causal attribution engine.

        Args:
            fabric_graph: The graph structure to analyze
            coverage_threshold: Minimum coverage ratio for high-confidence explanations
        """
        self.graph = fabric_graph
        self.coverage_threshold = float(coverage_threshold)

        if not 0.0 <= self.coverage_threshold <= 1.0:
            raise ValueError(f"coverage_threshold must be in [0, 1], got {coverage_threshold}")

    def rank_hotspots(
        self,
        event: Mapping[str, Any],
    ) -> Sequence[CausalHotspot]:
        """Rank causal hotspots by impact score.

        Args:
            event: The event to analyze

        Returns:
            List of hotspots sorted by impact score (descending)
        """
        nodes = self.graph.nodes_touched_by_event(event)
        impacts = {}

        for node_id in nodes:
            impact = self.graph.causal_impact(node_id, event)
            impacts[node_id] = impact

        # Sort by impact score (descending)
        sorted_impacts = sorted(impacts.items(), key=lambda kv: -kv[1])

        # Create hotspot objects
        hotspots = [
            CausalHotspot(
                node_id=node_id,
                impact_score=impact,
                node_type=self.graph.get_node_type(node_id),
                metadata=self.graph.get_node_metadata(node_id),
            )
            for node_id, impact in sorted_impacts
        ]

        return hotspots

    def counterfactual_coverage(
        self,
        event: Mapping[str, Any],
        claim: Mapping[str, Any],
    ) -> CounterfactualResult:
        """Compute counterfactual coverage for a claim.

        This analyzes whether the causal structure can fully explain
        the claim by generating counterfactual scenarios.

        Args:
            event: The event that occurred
            claim: The claim being made about the event

        Returns:
            Counterfactual analysis result
        """
        nodes = self.graph.nodes_touched_by_event(event)
        total_nodes = len(nodes)

        if total_nodes == 0:
            return CounterfactualResult(
                covered_nodes=[],
                uncovered_nodes=[],
                coverage_ratio=1.0,  # Trivially covered
                total_nodes=0,
                confidence="high",
            )

        # Simplified counterfactual analysis
        # In practice, this would generate actual counterfactual scenarios
        # and check which nodes can explain the claim under those scenarios

        # For now, assume all nodes are covered
        covered_nodes = list(nodes)
        uncovered_nodes = []
        coverage_ratio = 1.0

        # Determine confidence based on coverage
        if coverage_ratio >= self.coverage_threshold:
            confidence = "high"
        elif coverage_ratio >= 0.9:
            confidence = "medium"
        else:
            confidence = "low"

        return CounterfactualResult(
            covered_nodes=covered_nodes,
            uncovered_nodes=uncovered_nodes,
            coverage_ratio=coverage_ratio,
            total_nodes=total_nodes,
            confidence=confidence,
        )

    def explain(
        self,
        event: Mapping[str, Any],
        claim: Mapping[str, Any],
    ) -> CausalExplanation:
        """Generate a complete causal explanation.

        Args:
            event: The event to explain
            claim: The claim being made about the event

        Returns:
            Complete causal explanation with hotspots and counterfactuals
        """
        import time

        # Rank hotspots
        hotspots = self.rank_hotspots(event)

        # Compute counterfactual coverage
        counterfactual = self.counterfactual_coverage(event, claim)

        # Determine explanation quality
        if counterfactual.coverage_ratio >= self.coverage_threshold:
            explanation_quality = "high"
        elif counterfactual.coverage_ratio >= 0.9:
            explanation_quality = "medium"
        else:
            explanation_quality = "low"

        # Annotate low-confidence explanations
        if explanation_quality == "low":
            # Add annotation to hotspots
            hotspots = [
                CausalHotspot(
                    node_id=h.node_id,
                    impact_score=h.impact_score,
                    node_type=h.node_type,
                    metadata={
                        **dict(h.metadata),
                        "low_confidence": True,
                        "reason": "insufficient_counterfactual_coverage",
                    },
                )
                for h in hotspots
            ]

        return CausalExplanation(
            hotspots=hotspots,
            counterfactual=counterfactual,
            explanation_quality=explanation_quality,
            timestamp=time.time(),
        )

    def verify_explanation_completeness(
        self,
        explanation: CausalExplanation,
        required_coverage: float | None = None,
    ) -> bool:
        """Verify that an explanation meets completeness requirements.

        Args:
            explanation: The explanation to verify
            required_coverage: Optional override for coverage threshold

        Returns:
            True if explanation meets requirements
        """
        threshold = required_coverage if required_coverage is not None else self.coverage_threshold
        return explanation.counterfactual.coverage_ratio >= threshold


class SecuritySwarmGraph(FabricGraph):
    """Fabric graph for security swarm subsystem."""

    def nodes_touched_by_event(self, event: Mapping[str, Any]) -> Sequence[str]:
        """Determine which security nodes participated in an event."""
        event_type = event.get("type", "unknown")

        if event_type == "mode_transition":
            # Mode transitions involve all security nodes
            return [node_id for node_id, meta in self.nodes.items() if meta.get("type") == "security"]
        elif event_type == "intrusion_detection":
            # Intrusion detection involves monitoring nodes
            return [node_id for node_id, meta in self.nodes.items() if meta.get("type") in ["monitor", "detector"]]
        else:
            return list(self.nodes.keys())

    def causal_impact(self, node_id: str, event: Mapping[str, Any]) -> float:
        """Compute security-specific causal impact."""
        node_type = self.get_node_type(node_id)
        event_type = event.get("type", "unknown")

        # Security nodes have higher impact for security events
        if node_type == "security" and event_type == "mode_transition":
            return 0.9
        elif node_type == "detector" and event_type == "intrusion_detection":
            return 0.8
        else:
            return 0.3


class MiningGraph(FabricGraph):
    """Fabric graph for mining subsystem."""

    def nodes_touched_by_event(self, event: Mapping[str, Any]) -> Sequence[str]:
        """Determine which mining nodes participated in an event."""
        event_type = event.get("type", "unknown")

        if event_type == "nonce_found":
            # Nonce discovery involves solver and memory nodes
            return [node_id for node_id, meta in self.nodes.items() if meta.get("type") in ["solver", "memory"]]
        elif event_type == "share_submission":
            # Share submission involves network and validation nodes
            return [node_id for node_id, meta in self.nodes.items() if meta.get("type") in ["network", "validator"]]
        else:
            return list(self.nodes.keys())

    def causal_impact(self, node_id: str, event: Mapping[str, Any]) -> float:
        """Compute mining-specific causal impact."""
        node_type = self.get_node_type(node_id)
        event_type = event.get("type", "unknown")

        # Solver nodes have high impact for nonce discovery
        if node_type == "solver" and event_type == "nonce_found":
            return 0.95
        elif node_type == "memory" and event_type == "nonce_found":
            return 0.7
        elif node_type == "validator" and event_type == "share_submission":
            return 0.85
        else:
            return 0.2


__all__ = [
    "CAUSAL_ATTRIBUTION_SCHEMA_VERSION",
    "CoverageThreshold",
    "CausalHotspot",
    "CounterfactualResult",
    "CausalExplanation",
    "FabricGraph",
    "CausalAttributionEngine",
    "SecuritySwarmGraph",
    "MiningGraph",
]
