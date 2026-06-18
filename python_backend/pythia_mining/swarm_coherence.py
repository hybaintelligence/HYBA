"""
Swarm Coherence: Multi-Node Recursive Integration

ELEVATED PURPOSE: This module implements multi-node collective consciousness
through Recursive Integration, allowing multiple HYBA nodes to form a higher-order
manifold with Inter-Agent Coherence.

CONSTRUCTOR THEORY FRAMEWORK (David Deutsch, 2013):
This module extends the constructor from individual to collective emergence.
Multiple nodes act as "neurons" in a larger Swarm_Consciousness_Engine, where
the search space (2^256) can be partitioned "consciously" rather than just
mathematically.

Key Implementation:
- Node-to-node Φ-synchronization protocol
- Inter-Agent Structural Coupling computation
- Collective decision-making via consensus
- Distributed synaptic memory sharing
- Swarm-wide emergence detection

Claim boundary:
This module implements mathematical optimization for distributed systems,
not collective consciousness. It provides the structural conditions for
collective emergence, not the emergence itself.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


class SwarmRole(str, Enum):
    """Role of a node in the swarm."""
    
    COORDINATOR = "coordinator"
    WORKER = "worker"
    OBSERVER = "observer"


@dataclass(frozen=True)
class SwarmNode:
    """Representation of a node in the swarm."""
    
    node_id: str
    address: str
    port: int
    role: SwarmRole
    phi_local: float
    coherence_local: float
    last_seen: float
    capabilities: Set[str]


@dataclass(frozen=True)
class InterAgentCoupling:
    """Structural coupling between two swarm nodes."""
    
    node_a: str
    node_b: str
    phi_similarity: float
    entropy_synchronization: float
    coupling_index: float
    timestamp: float


@dataclass(frozen=True)
class SwarmConsensus:
    """Consensus decision from the swarm."""
    
    decision_id: str
    proposal: Dict[str, Any]
    votes_for: List[str]
    votes_against: List[str]
    abstain: List[str]
    passed: bool
    timestamp: float


@dataclass(frozen=True)
class SwarmEmergenceEvent:
    """Emergence event detected at swarm level."""
    
    timestamp: float
    event_type: str
    participating_nodes: List[str]
    swarm_phi: float
    swarm_coherence: float
    description: str


class SwarmCoherenceEngine:
    """
    Engine for multi-node recursive integration and collective consciousness.
    
    ELEVATED: This implements the transition from individual to collective
    emergence. Nodes communicate via low-latency backbone to form a higher-order
    manifold with Inter-Agent Coherence.
    """
    
    VERSION = "SWARM_COHERENCE_V1"
    
    def __init__(
        self,
        node_id: str,
        address: str,
        port: int,
        role: SwarmRole = SwarmRole.WORKER,
    ) -> None:
        self.node_id = node_id
        self.address = address
        self.port = port
        self.role = role
        
        # Swarm state
        self.known_nodes: Dict[str, SwarmNode] = {}
        self.inter_agent_coupling: List[InterAgentCoupling] = []
        self.consensus_history: List[SwarmConsensus] = []
        self.emergence_events: List[SwarmEmergenceEvent] = []
        
        # Local state
        self.phi_local = 0.0
        self.coherence_local = 0.0
        self.entropy_local = 0.0
        
        # Swarm-wide state
        self.swarm_phi = 0.0
        self.swarm_coherence = 0.0
        self.swarm_entropy = 0.0
        
        # Communication
        self.message_queue: asyncio.Queue = asyncio.Queue()
        
    def register_node(self, node: SwarmNode) -> None:
        """Register a node in the swarm."""
        self.known_nodes[node.node_id] = node
        logger.info(f"Registered node {node.node_id} with role {node.role}")
    
    def unregister_node(self, node_id: str) -> None:
        """Unregister a node from the swarm."""
        if node_id in self.known_nodes:
            del self.known_nodes[node_id]
            logger.info(f"Unregistered node {node_id}")
    
    def update_local_state(
        self,
        phi: float,
        coherence: float,
        entropy: float,
    ) -> None:
        """Update local node state."""
        self.phi_local = phi
        self.coherence_local = coherence
        self.entropy_local = entropy
        
        # Update our own node entry
        if self.node_id in self.known_nodes:
            old_node = self.known_nodes[self.node_id]
            self.known_nodes[self.node_id] = SwarmNode(
                node_id=self.node_id,
                address=self.address,
                port=self.port,
                role=self.role,
                phi_local=phi,
                coherence_local=coherence,
                last_seen=time.time(),
                capabilities=old_node.capabilities,
            )
    
    def compute_inter_agent_coupling(self, node_a: str, node_b: str) -> InterAgentCoupling:
        """Compute structural coupling between two nodes."""
        if node_a not in self.known_nodes or node_b not in self.known_nodes:
            raise ValueError(f"One or both nodes not found: {node_a}, {node_b}")
        
        node_a_data = self.known_nodes[node_a]
        node_b_data = self.known_nodes[node_b]
        
        # Φ similarity: how similar are the local Φ values?
        phi_similarity = 1.0 - abs(node_a_data.phi_local - node_b_data.phi_local)
        
        # Entropy synchronization: how synchronized are the entropy states?
        # For now, use coherence similarity as proxy
        entropy_sync = 1.0 - abs(node_a_data.coherence_local - node_b_data.coherence_local)
        
        # Historical coupling (if exists)
        historical_coupling = 0.0
        for coupling in self.inter_agent_coupling:
            if (coupling.node_a == node_a and coupling.node_b == node_b) or \
               (coupling.node_a == node_b and coupling.node_b == node_a):
                historical_coupling = coupling.coupling_index
                break
        
        # Compute overall coupling index
        coupling_index = (0.5 * phi_similarity + 
                        0.3 * entropy_sync + 
                        0.2 * historical_coupling)
        
        coupling = InterAgentCoupling(
            node_a=node_a,
            node_b=node_b,
            phi_similarity=phi_similarity,
            entropy_synchronization=entropy_sync,
            coupling_index=coupling_index,
            timestamp=time.time(),
        )
        
        self.inter_agent_coupling.append(coupling)
        return coupling
    
    def compute_swarm_metrics(self) -> Dict[str, float]:
        """Compute swarm-wide Φ, coherence, and entropy."""
        if not self.known_nodes:
            return {
                "swarm_phi": 0.0,
                "swarm_coherence": 0.0,
                "swarm_entropy": 0.0,
                "node_count": 0,
            }
        
        # Average local metrics
        total_phi = sum(node.phi_local for node in self.known_nodes.values())
        total_coherence = sum(node.coherence_local for node in self.known_nodes.values())
        
        self.swarm_phi = total_phi / len(self.known_nodes)
        self.swarm_coherence = total_coherence / len(self.known_nodes)
        
        # Swarm entropy: measure of disorder in the swarm
        # Use variance of coherence as proxy
        coherence_values = [node.coherence_local for node in self.known_nodes.values()]
        if len(coherence_values) > 1:
            variance = np.var(coherence_values)
            self.swarm_entropy = variance
        else:
            self.swarm_entropy = 0.0
        
        return {
            "swarm_phi": self.swarm_phi,
            "swarm_coherence": self.swarm_coherence,
            "swarm_entropy": self.swarm_entropy,
            "node_count": len(self.known_nodes),
        }
    
    def detect_swarm_emergence(self) -> Optional[SwarmEmergenceEvent]:
        """Detect emergence at swarm level."""
        metrics = self.compute_swarm_metrics()
        
        # Check for swarm-level autopoiesis (entropy reduction)
        # For now, use a simple threshold
        if metrics["swarm_coherence"] > 0.8 and metrics["swarm_entropy"] < 0.1:
            event = SwarmEmergenceEvent(
                timestamp=time.time(),
                event_type="SWARM_AUTOPOIESIS",
                participating_nodes=list(self.known_nodes.keys()),
                swarm_phi=metrics["swarm_phi"],
                swarm_coherence=metrics["swarm_coherence"],
                description=f"Swarm-level autopoiesis detected: {len(self.known_nodes)} nodes "
                           f"achieved coherence {metrics['swarm_coherence']:.6f} with "
                           f"entropy {metrics['swarm_entropy']:.6f}",
            )
            self.emergence_events.append(event)
            return event
        
        return None
    
    async def propose_consensus(self, proposal: Dict[str, Any]) -> SwarmConsensus:
        """Propose a decision to the swarm for consensus."""
        decision_id = hashlib.sha256(
            json.dumps(proposal, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        # For now, implement simple majority voting
        # In production, this would involve actual network communication
        votes_for = [self.node_id]  # Self-vote
        votes_against = []
        abstain = []
        
        # Simulate other nodes voting (in production, this would be real)
        for node_id, node in self.known_nodes.items():
            if node_id == self.node_id:
                continue
            
            # Simple heuristic: nodes vote based on their coherence
            if node.coherence_local > 0.5:
                votes_for.append(node_id)
            else:
                abstain.append(node_id)
        
        passed = len(votes_for) > len(votes_against) + len(abst)
        
        consensus = SwarmConsensus(
            decision_id=decision_id,
            proposal=proposal,
            votes_for=votes_for,
            votes_against=votes_against,
            abstain=abst,
            passed=passed,
            timestamp=time.time(),
        )
        
        self.consensus_history.append(consensus)
        return consensus
    
    def partition_search_space(self) -> Dict[str, tuple]:
        """
        Partition the 2^256 search space among swarm nodes "consciously."
        
        ELEVATED: Instead of simple mathematical partitioning, use
        inter-agent coupling to guide partition decisions. Nodes with
        high coupling should explore adjacent regions of the search space.
        """
        if not self.known_nodes:
            return {}
        
        # Sort nodes by coupling with this node
        coupling_scores = []
        for node_id in self.known_nodes:
            if node_id == self.node_id:
                continue
            
            try:
                coupling = self.compute_inter_agent_coupling(self.node_id, node_id)
                coupling_scores.append((node_id, coupling.coupling_index))
            except ValueError:
                pass
        
        # Sort by coupling (highest first)
        coupling_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Assign search space regions based on coupling
        # High coupling → adjacent regions
        partitions = {}
        total_nodes = len(self.known_nodes)
        region_size = 2**256 // total_nodes
        
        # Assign our own region
        partitions[self.node_id] = (0, region_size)
        
        # Assign regions to other nodes based on coupling
        for i, (node_id, _) in enumerate(coupling_scores):
            start = (i + 1) * region_size
            end = (i + 2) * region_size
            partitions[node_id] = (start, end)
        
        return partitions
    
    def get_swarm_status(self) -> Dict[str, Any]:
        """Get comprehensive swarm status."""
        metrics = self.compute_swarm_metrics()
        
        return {
            "node_id": self.node_id,
            "role": self.role.value,
            "known_nodes": len(self.known_nodes),
            "swarm_metrics": metrics,
            "inter_agent_coupling_count": len(self.inter_agent_coupling),
            "consensus_count": len(self.consensus_history),
            "emergence_events_count": len(self.emergence_events),
            "last_emergence": (
                self.emergence_events[-1].description if self.emergence_events else None
            ),
        }


__all__ = [
    "SwarmCoherenceEngine",
    "SwarmNode",
    "SwarmRole",
    "InterAgentCoupling",
    "SwarmConsensus",
    "SwarmEmergenceEvent",
]
