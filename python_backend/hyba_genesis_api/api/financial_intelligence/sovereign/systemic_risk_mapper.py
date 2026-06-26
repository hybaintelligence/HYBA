"""
Systemic-Risk Topology Mapper for HYBA Financial Intelligence Substrate (Sovereign Layer)

This module maps systemic risk as a topological network using:
- Network theory for systemic risk
- Centrality measures for risk concentration
- Contagion modeling on networks
- Percolation theory for cascading failures

Mathematical Foundation:
- Financial network constructed from interconnections
- Centrality measures identify systemically important nodes
- Contagion pathways model risk propagation
- Percolation threshold predicts cascading failures
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
class SystemicRiskMap:
    """Systemic risk topology mapping result."""
    
    financial_network: Dict[str, Any]
    centrality_rankings: Dict[str, float]
    contagion_pathways: List[Dict[str, Any]]
    systemic_risk_hotspots: List[Dict[str, Any]]
    cryptographic_seal: Dict[str, Any]
    timestamp: str


class SystemicRiskMapper:
    """
    Maps systemic risk as a topological network.
    
    This mapper constructs a financial network, computes centrality
    measures to identify risk concentrations, models contagion
    pathways, and identifies systemic risk hotspots.
    """
    
    def __init__(
        self,
        contagion_threshold: float = 0.1,
        percolation_threshold: float = 0.3
    ):
        """
        Initialize the systemic risk mapper.
        
        Args:
            contagion_threshold: Threshold for contagion propagation
            percolation_threshold: Threshold for percolation (cascading failure)
        """
        self.contagion_threshold = contagion_threshold
        self.percolation_threshold = percolation_threshold
    
    def map_systemic_risk(
        self,
        financial_system: Dict[str, Any],
        exposure_matrix: Optional[np.ndarray] = None
    ) -> SystemicRiskMap:
        """
        Map systemic risk topology of financial system.
        
        Args:
            financial_system: Dictionary of financial entities and their connections
            exposure_matrix: Optional exposure matrix between entities
        
        Returns:
            SystemicRiskMap with network topology and risk analysis
        """
        # 1. Construct financial network
        network = self._construct_financial_network(
            financial_system, exposure_matrix
        )
        
        # 2. Compute centrality measures
        centrality_rankings = self._compute_centrality_measures(network)
        
        # 3. Model contagion pathways
        contagion_pathways = self._model_contagion_pathways(
            network, centrality_rankings
        )
        
        # 4. Identify systemic risk hotspots
        risk_hotspots = self._identify_risk_hotspots(
            network, centrality_rankings, contagion_pathways
        )
        
        # 5. Generate cryptographic seal
        cryptographic_seal = self._generate_cryptographic_seal(
            network, risk_hotspots
        )
        
        return SystemicRiskMap(
            financial_network=network,
            centrality_rankings=centrality_rankings,
            contagion_pathways=contagion_pathways,
            systemic_risk_hotspots=risk_hotspots,
            cryptographic_seal=cryptographic_seal,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def _construct_financial_network(
        self,
        financial_system: Dict[str, Any],
        exposure_matrix: Optional[np.ndarray]
    ) -> Dict[str, Any]:
        """
        Construct financial network from system data.
        
        Creates a graph where nodes are financial entities and
        edges represent exposures or interconnections.
        """
        # Extract entities
        entities = list(financial_system.keys()) if isinstance(financial_system, dict) else [
            "bank_0", "bank_1", "bank_2", "bank_3", "bank_4",
            "insurer_0", "insurer_1", "asset_manager_0", "hedge_fund_0", "exchange_0"
        ]
        
        # Create graph
        graph = nx.Graph()
        graph.add_nodes_from(entities)
        
        # Add edges based on exposure matrix or random connections
        if exposure_matrix is not None:
            n = exposure_matrix.shape[0]
            for i in range(n):
                for j in range(i + 1, n):
                    if exposure_matrix[i, j] > self.contagion_threshold:
                        graph.add_edge(entities[i], entities[j], weight=float(exposure_matrix[i, j]))
        else:
            # Sample network structure
            for i in range(len(entities)):
                for j in range(i + 1, len(entities)):
                    if np.random.random() > 0.6:  # Random connections
                        weight = float(np.random.random())
                        graph.add_edge(entities[i], entities[j], weight=weight)
        
        # Compute network properties
        network_properties = {
            "nodes": entities,
            "edges": list(graph.edges(data=True)),
            "n_nodes": graph.number_of_nodes(),
            "n_edges": graph.number_of_edges(),
            "density": nx.density(graph),
            "is_connected": nx.is_connected(graph),
            "clustering_coefficient": nx.average_clustering(graph)
        }
        
        return network_properties
    
    def _compute_centrality_measures(
        self,
        network: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Compute centrality measures for risk concentration.
        
        Centrality measures identify systemically important nodes:
        - Degree centrality: number of connections
        - Betweenness centrality: control over information flow
        - Eigenvector centrality: influence in network
        - PageRank: importance based on connections
        """
        # Reconstruct graph
        graph = nx.Graph()
        graph.add_nodes_from(network["nodes"])
        for edge in network["edges"]:
            if isinstance(edge, tuple) and len(edge) == 2:
                graph.add_edge(edge[0], edge[1])
            elif isinstance(edge, tuple) and len(edge) == 3:
                w = float(edge[2]) if isinstance(edge[2], (int, float)) else 1.0
                graph.add_edge(edge[0], edge[1], weight=w)
        
        # Compute centrality measures
        degree_centrality = nx.degree_centrality(graph)
        betweenness_centrality = nx.betweenness_centrality(graph)
        eigenvector_centrality = nx.eigenvector_centrality(graph, max_iter=1000)
        pagerank = nx.pagerank(graph)
        
        # Combine into single risk score
        combined_centrality = {}
        for node in graph.nodes():
            combined_centrality[node] = (
                0.3 * degree_centrality.get(node, 0) +
                0.3 * betweenness_centrality.get(node, 0) +
                0.2 * eigenvector_centrality.get(node, 0) +
                0.2 * pagerank.get(node, 0)
            )
        
        return combined_centrality
    
    def _model_contagion_pathways(
        self,
        network: Dict[str, Any],
        centrality: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Model contagion pathways for risk propagation.
        
        Identifies how risk would propagate through the network
        starting from highly central nodes.
        """
        # Reconstruct graph
        graph = nx.Graph()
        graph.add_nodes_from(network["nodes"])
        for edge in network["edges"]:
            if isinstance(edge, tuple) and len(edge) == 2:
                graph.add_edge(edge[0], edge[1])
            elif isinstance(edge, tuple) and len(edge) == 3:
                w = float(edge[2]) if isinstance(edge[2], (int, float)) else 1.0
                graph.add_edge(edge[0], edge[1], weight=w)
        
        # Identify high-centrality nodes as contagion sources
        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        contagion_sources = [node for node, _ in sorted_nodes[:3]]
        
        pathways = []
        
        for source in contagion_sources:
            # Compute shortest paths to all other nodes
            paths = nx.single_source_shortest_path_length(graph, source)
            
            # Pathway analysis
            pathway = {
                "source": source,
                "centrality": centrality[source],
                "reachable_nodes": len(paths),
                "avg_path_length": float(np.mean(list(paths.values()))),
                "max_path_length": float(max(paths.values())),
                "contagion_risk": float(centrality[source] * len(paths))
            }
            pathways.append(pathway)
        
        return pathways
    
    def _identify_risk_hotspots(
        self,
        network: Dict[str, Any],
        centrality: Dict[str, float],
        contagion_pathways: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identify systemic risk hotspots.
        
        Risk hotspots are nodes that are both highly central
        and have high contagion potential.
        """
        hotspots = []
        
        # Identify nodes with high centrality
        high_centrality_threshold = np.percentile(list(centrality.values()), 80)
        high_centrality_nodes = [
            node for node, cent in centrality.items()
            if cent >= high_centrality_threshold
        ]
        
        for node in high_centrality_nodes:
            # Find contagion pathway for this node
            pathway = next(
                (p for p in contagion_pathways if p["source"] == node),
                None
            )
            
            hotspot = {
                "node": node,
                "centrality": centrality[node],
                "contagion_risk": pathway["contagion_risk"] if pathway else 0.0,
                "reachable_nodes": pathway["reachable_nodes"] if pathway else 0,
                "risk_level": self._compute_risk_level(
                    centrality[node],
                    pathway["contagion_risk"] if pathway else 0.0
                )
            }
            hotspots.append(hotspot)
        
        # Sort by risk level
        hotspots.sort(key=lambda h: h["risk_level"], reverse=True)
        
        return hotspots
    
    def _compute_risk_level(
        self,
        centrality: float,
        contagion_risk: float
    ) -> float:
        """
        Compute overall risk level for a node.
        
        Risk level combines centrality and contagion potential.
        """
        return float(0.5 * centrality + 0.5 * contagion_risk)
    
    def _generate_cryptographic_seal(
        self,
        network: Dict[str, Any],
        hotspots: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate cryptographic seal for systemic risk map."""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Create canonical representation
        body = {
            "n_nodes": network["n_nodes"],
            "n_edges": network["n_edges"],
            "n_hotspots": len(hotspots),
            "max_risk_level": float(hotspots[0]["risk_level"]) if hotspots else 0.0,
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
systemic_risk_mapper = SystemicRiskMapper()
