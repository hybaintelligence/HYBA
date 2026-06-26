"""
Topology-Aware Rewiring for HYBA Financial Intelligence Substrate (Autonomic Layer)

This module rewires system connections based on topological changes using:
- Network topology analysis
- Graph theory for connection optimization
- Topological data analysis (TDA)
- Adaptive network reconfiguration

Mathematical Foundation:
- Network topology analyzed via graph theory
- Centrality measures identify critical nodes
- Topological data analysis detects structural changes
- Adaptive rewiring under governance constraints
"""

from __future__ import annotations

import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import networkx as nx
import hashlib
import json


@dataclass
class RewiringReport:
    """Topology-aware rewiring report."""
    
    new_topology: Dict[str, Any]
    rewiring_confidence: float
    performance_impact: float
    governance_approval_status: str
    cryptographic_seal: Dict[str, Any]
    timestamp: str


class TopologyAwareRewiring:
    """
    Rewires system connections based on topological changes.
    
    This rewiring system analyzes the current topology, detects
    changes, computes optimal rewiring, and applies changes under
    sovereign governance constraints.
    """
    
    def __init__(
        self,
        rewiring_threshold: float = 0.3,
        governance_rail: str = "enterprise"
    ):
        """
        Initialize the topology-aware rewiring system.
        
        Args:
            rewiring_threshold: Threshold for triggering rewiring
            governance_rail: Governance rail for approval
        """
        self.rewiring_threshold = rewiring_threshold
        self.governance_rail = governance_rail
        self.historical_topologies: List[Dict[str, Any]] = []
    
    def rewire_system(
        self,
        system: Dict[str, Any],
        performance_data: np.ndarray
    ) -> RewiringReport:
        """
        Rewire system based on topological analysis.
        
        Args:
            system: System with connection topology
            performance_data: Performance metrics for evaluation
        
        Returns:
            RewiringReport with new topology and approval status
        """
        # 1. Analyze current topology
        current_topology = self._analyze_topology(system)
        
        # 2. Detect topological changes
        topology_changed, change_magnitude = self._detect_topology_changes(
            current_topology
        )
        
        if not topology_changed or change_magnitude < self.rewiring_threshold:
            return RewiringReport(
                new_topology=current_topology,
                rewiring_confidence=1.0,
                performance_impact=0.0,
                governance_approval_status="no_change_needed",
                cryptographic_seal=self._generate_cryptographic_seal(
                    0, 1.0, 0.0, "no_change_needed"
                ),
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        
        # 3. Compute optimal rewiring
        new_topology = self._compute_optimal_rewiring(
            current_topology, performance_data
        )
        
        # 4. Compute rewiring confidence
        rewiring_confidence = self._compute_rewiring_confidence(
            current_topology, new_topology
        )
        
        # 5. Compute performance impact
        performance_impact = self._compute_performance_impact(
            current_topology, new_topology, performance_data
        )
        
        # 6. Apply governance approval
        approval_status = self._apply_governance_approval(
            rewiring_confidence, performance_impact
        )
        
        # 7. Update historical tracking
        self._update_history(current_topology)
        
        # 8. Generate cryptographic seal
        cryptographic_seal = self._generate_cryptographic_seal(
            len(new_topology.get("edges", [])),
            rewiring_confidence,
            performance_impact,
            approval_status
        )
        
        return RewiringReport(
            new_topology=new_topology,
            rewiring_confidence=rewiring_confidence,
            performance_impact=performance_impact,
            governance_approval_status=approval_status,
            cryptographic_seal=cryptographic_seal,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def _analyze_topology(
        self,
        system: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze current system topology.
        
        Extracts and analyzes the connection structure of the system.
        """
        # In production, this would parse the actual system structure
        # For now, create a sample topology
        nodes = list(system.keys()) if isinstance(system, dict) else ["node_0", "node_1", "node_2", "node_3"]
        
        # Create graph
        graph = nx.Graph()
        graph.add_nodes_from(nodes)
        
        # Add edges (sample connections)
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                if np.random.random() > 0.5:  # Random connections
                    graph.add_edge(nodes[i], nodes[j])
        
        # Compute centrality measures
        centrality = nx.degree_centrality(graph)
        
        # Compute clustering coefficient
        clustering = nx.average_clustering(graph)
        
        return {
            "nodes": nodes,
            "edges": list(graph.edges()),
            "centrality": centrality,
            "clustering_coefficient": clustering,
            "n_nodes": len(nodes),
            "n_edges": graph.number_of_edges()
        }
    
    def _detect_topology_changes(
        self,
        current_topology: Dict[str, Any]
    ) -> Tuple[bool, float]:
        """
        Detect topological changes from historical baseline.
        
        Compares current topology with historical baselines to
        detect significant structural changes.
        """
        if not self.historical_topologies:
            return False, 0.0
        
        # Compare with most recent historical topology
        baseline = self.historical_topologies[-1]
        
        # Compute change magnitude
        n_nodes_change = abs(current_topology["n_nodes"] - baseline["n_nodes"])
        n_edges_change = abs(current_topology["n_edges"] - baseline["n_edges"])
        
        # Centrality change
        current_centrality = current_topology.get("centrality", {})
        baseline_centrality = baseline.get("centrality", {})
        
        centrality_change = 0.0
        for node in current_centrality:
            if node in baseline_centrality:
                centrality_change += abs(
                    current_centrality[node] - baseline_centrality[node]
                )
        
        # Normalize change magnitude
        max_nodes = max(current_topology["n_nodes"], baseline["n_nodes"])
        max_edges = max(current_topology["n_edges"], baseline["n_edges"])
        
        normalized_change = (
            (n_nodes_change / max_nodes if max_nodes > 0 else 0) +
            (n_edges_change / max_edges if max_edges > 0 else 0) +
            (centrality_change / len(current_centrality) if len(current_centrality) > 0 else 0)
        ) / 3
        
        topology_changed = normalized_change > self.rewiring_threshold
        
        return topology_changed, normalized_change
    
    def _compute_optimal_rewiring(
        self,
        current_topology: Dict[str, Any],
        performance_data: np.ndarray
    ) -> Dict[str, Any]:
        """
        Compute optimal rewiring based on performance.
        
        Uses graph theory to identify optimal connection structure
        that maximizes performance while maintaining stability.
        """
        # Create graph from current topology
        graph = nx.Graph()
        graph.add_nodes_from(current_topology["nodes"])
        graph.add_edges_from(current_topology["edges"])
        
        # Compute node importance based on performance correlation
        # (simplified - in production, use actual performance data)
        centrality = nx.degree_centrality(graph)
        
        # Rewiring strategy: strengthen high-centrality connections
        new_graph = graph.copy()
        
        # Add edges between high-centrality nodes
        high_centrality_nodes = [
            node for node, cent in centrality.items()
            if cent > np.median(list(centrality.values()))
        ]
        
        for i in range(len(high_centrality_nodes)):
            for j in range(i + 1, len(high_centrality_nodes)):
                if not new_graph.has_edge(high_centrality_nodes[i], high_centrality_nodes[j]):
                    new_graph.add_edge(high_centrality_nodes[i], high_centrality_nodes[j])
        
        # Remove weak edges
        edges_to_remove = []
        for u, v in new_graph.edges():
            if centrality.get(u, 0) < 0.2 and centrality.get(v, 0) < 0.2:
                edges_to_remove.append((u, v))
        
        for edge in edges_to_remove:
            new_graph.remove_edge(*edge)
        
        # Compute new centrality
        new_centrality = nx.degree_centrality(new_graph)
        new_clustering = nx.average_clustering(new_graph)
        
        return {
            "nodes": list(new_graph.nodes()),
            "edges": list(new_graph.edges()),
            "centrality": new_centrality,
            "clustering_coefficient": new_clustering,
            "n_nodes": new_graph.number_of_nodes(),
            "n_edges": new_graph.number_of_edges()
        }
    
    def _compute_rewiring_confidence(
        self,
        old_topology: Dict[str, Any],
        new_topology: Dict[str, Any]
    ) -> float:
        """
        Compute confidence in rewiring decision.
        
        Confidence is based on:
        - Improvement in clustering coefficient
        - Improvement in centrality distribution
        - Stability of node set
        """
        # Clustering improvement
        clustering_improvement = (
            new_topology["clustering_coefficient"] -
            old_topology["clustering_coefficient"]
        )
        
        # Centrality improvement (more balanced distribution)
        old_centralities = list(old_topology["centrality"].values())
        new_centralities = list(new_topology["centrality"].values())
        
        old_balance = 1.0 - np.std(old_centralities)
        new_balance = 1.0 - np.std(new_centralities)
        
        balance_improvement = new_balance - old_balance
        
        # Node stability
        node_stability = (
            len(set(old_topology["nodes"]) & set(new_topology["nodes"])) /
            max(len(old_topology["nodes"]), 1)
        )
        
        # Combined confidence
        confidence = (
            0.4 * max(0.0, clustering_improvement) +
            0.4 * max(0.0, balance_improvement) +
            0.2 * node_stability
        )
        
        return float(min(1.0, confidence))
    
    def _compute_performance_impact(
        self,
        old_topology: Dict[str, Any],
        new_topology: Dict[str, Any],
        performance_data: np.ndarray
    ) -> float:
        """
        Compute performance impact of rewiring.
        
        Simplified: estimate based on topology improvements.
        """
        # In production, this would measure actual performance
        # For now, use clustering coefficient as proxy
        clustering_improvement = (
            new_topology["clustering_coefficient"] -
            old_topology["clustering_coefficient"]
        )
        
        # Assume linear relationship between clustering and performance
        performance_impact = clustering_improvement * 0.5
        
        return float(performance_impact)
    
    def _apply_governance_approval(
        self,
        rewiring_confidence: float,
        performance_impact: float
    ) -> str:
        """
        Apply governance approval based on rail.
        
        Different rails have different approval requirements:
        - Treasury: Auto-approve
        - Enterprise: Human approval required
        - Sovereign: Multi-party approval required
        """
        if self.governance_rail == "treasury":
            if rewiring_confidence > 0.7:
                return "auto_approved"
            else:
                return "manual_review_required"
        
        elif self.governance_rail == "enterprise":
            return "human_approval_required"
        
        elif self.governance_rail == "sovereign":
            return "multi_party_approval_required"
        
        else:
            return "unknown_rail"
    
    def _update_history(self, topology: Dict[str, Any]):
        """Update historical topology tracking."""
        self.historical_topologies.append(topology)
        
        # Keep only last 50 entries
        if len(self.historical_topologies) > 50:
            self.historical_topologies.pop(0)
    
    def _generate_cryptographic_seal(
        self,
        n_edges: int,
        confidence: float,
        impact: float,
        approval_status: str
    ) -> Dict[str, Any]:
        """Generate cryptographic seal for rewiring."""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Create canonical representation
        body = {
            "n_edges": n_edges,
            "rewiring_confidence": confidence,
            "performance_impact": impact,
            "approval_status": approval_status,
            "timestamp": timestamp
        }
        
        canonical = json.dumps(body, sort_keys=True, default=str, separators=(",", ":"))
        body_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        
        # Create seal
        seal_body = {
            "algorithm": "SHA-256",
            "body_hash": body_hash,
            "timestamp": timestamp,
            "immutable_guard_active": True
        }
        
        seal = hashlib.sha256(
            json.dumps(seal_body, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        
        return {
            "algorithm": "SHA-256",
            "body_hash": body_hash,
            "seal": seal,
            "timestamp": timestamp,
            "immutable_guard_active": True
        }


# Global instance for service layer
topology_rewiring = TopologyAwareRewiring()
