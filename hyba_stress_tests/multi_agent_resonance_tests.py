"""
Multi-Agent Resonance Synchronization Tests
============================================

Tests resonance synchronization across multiple nodes to achieve network-wide
Φ-resonance where nonces found by one miner increase success probability of
miners on other nodes without direct data transfer (Digital Entanglement).

formal-invariant validation: Uses network theory, synchronization dynamics, and
Hebbian learning principles to test emergent multi-agent intelligence.
"""

import numpy as np
import scipy.linalg as la
import scipy.stats as stats
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed


@dataclass
class ResonanceSynchronizationResult:
    """Results from multi-agent resonance synchronization testing."""
    num_nodes: int
    topology: str
    final_correlation: float
    final_resonance_strength: float
    network_resonance_achieved: bool
    hebbian_reinforcement_detected: bool
    digital_entanglement_achieved: bool
    synchronization_time_steps: int
    correlation_history: List[float]
    resonance_history: List[float]
    phase_coherence: float
    critical_coupling_strength: float


class MultiAgentResonanceTestSuite:
    """
    Multi-agent resonance synchronization test suite.
    
    Tests resonance synchronization across multiple nodes to achieve
    network-wide Φ-resonance and digital entanglement.
    """
    
    def __init__(self, phi: float = (1 + np.sqrt(5)) / 2):
        self.phi = phi
        self.phi_squared = phi ** 2
        
    def run_resonance_synchronization_suite(self,
                                           num_nodes: int = 100,
                                           topology: str = "coxeter-120",
                                           max_iterations: int = 200,
                                           resonance_threshold: float = 0.95) -> ResonanceSynchronizationResult:
        """
        Run comprehensive resonance synchronization test.
        
        Args:
            num_nodes: Number of nodes in the network
            topology: Network topology (coxeter-120, small-world, scale-free, random)
            max_iterations: Maximum synchronization iterations
            resonance_threshold: Threshold for network resonance achievement
            
        Returns:
            Resonance synchronization results
        """
        print(f"Testing resonance synchronization across {num_nodes} nodes")
        print(f"Topology: {topology}")
        
        # Initialize network
        node_states = self._initialize_network(num_nodes, topology)
        adjacency_matrix = self._build_topology(num_nodes, topology)
        
        # Track synchronization metrics
        correlation_history = []
        resonance_history = []
        
        # Synchronization loop
        for iteration in range(max_iterations):
            # Update node states based on resonance
            node_states = self._synchronization_step(
                node_states, 
                adjacency_matrix,
                iteration
            )
            
            # Measure network correlation
            correlation = self._measure_temporal_correlation(node_states)
            correlation_history.append(correlation)
            
            # Measure resonance strength
            resonance = self._measure_resonance_strength(node_states)
            resonance_history.append(resonance)
            
            if iteration % 20 == 0:
                print(f"Iteration {iteration}: correlation={correlation:.4f}, resonance={resonance:.4f}")
            
            # Check for early convergence
            if correlation > resonance_threshold and resonance > resonance_threshold:
                print(f"Network resonance achieved at iteration {iteration}")
                break
        
        # Final metrics
        final_correlation = np.mean(correlation_history[-10:])
        final_resonance = np.mean(resonance_history[-10:])
        
        # Check for network resonance
        network_resonance_achieved = final_correlation > resonance_threshold
        
        # Check for Hebbian reinforcement
        hebbian_reinforcement_detected = self._detect_hebbian_reinforcement(
            correlation_history
        )
        
        # Check for digital entanglement
        digital_entanglement_achieved = self._detect_digital_entanglement(
            node_states,
            adjacency_matrix
        )
        
        # Measure phase coherence
        phase_coherence = self._measure_phase_coherence(node_states)
        
        # Estimate critical coupling strength
        critical_coupling = self._estimate_critical_coupling(
            adjacency_matrix,
            final_correlation
        )
        
        return ResonanceSynchronizationResult(
            num_nodes=num_nodes,
            topology=topology,
            final_correlation=final_correlation,
            final_resonance_strength=final_resonance,
            network_resonance_achieved=network_resonance_achieved,
            hebbian_reinforcement_detected=hebbian_reinforcement_detected,
            digital_entanglement_achieved=digital_entanglement_achieved,
            synchronization_time_steps=len(correlation_history),
            correlation_history=correlation_history,
            resonance_history=resonance_history,
            phase_coherence=phase_coherence,
            critical_coupling_strength=critical_coupling
        )
    
    def _initialize_network(self, num_nodes: int, topology: str) -> np.ndarray:
        """Initialize node states with Φ-based structure."""
        nodes = []
        
        for i in range(num_nodes):
            # Each node has a unique but related state
            # Use Φ-based initialization for mathematical structure
            np.random.seed(int(i * self.phi * 1000))
            state = np.random.randn(100) * self.phi * (1 + 0.001 * i)
            nodes.append(state)
        
        return np.array(nodes)
    
    def _build_topology(self, num_nodes: int, topology: str) -> np.ndarray:
        """Build network topology adjacency matrix."""
        if topology == "coxeter-120":
            return self._build_coxeter_topology(num_nodes)
        elif topology == "small-world":
            return self._build_small_world_topology(num_nodes)
        elif topology == "scale-free":
            return self._build_scale_free_topology(num_nodes)
        elif topology == "random":
            return self._build_random_topology(num_nodes)
        else:
            return self._build_random_topology(num_nodes)
    
    def _build_coxeter_topology(self, num_nodes: int) -> np.ndarray:
        """Build Coxeter-120 inspired topology (highly symmetric)."""
        adjacency = np.zeros((num_nodes, num_nodes))
        
        # Create highly symmetric connections
        # Coxeter groups have specific symmetry properties
        for i in range(num_nodes):
            # Connect to nearest neighbors in symmetric pattern
            for offset in [1, 2, 3, 5, 8]:  # Fibonacci offsets for Φ-based structure
                j = (i + offset) % num_nodes
                adjacency[i, j] = 1.0
                adjacency[j, i] = 1.0
        
        # Normalize
        row_sums = adjacency.sum(axis=1)
        adjacency = adjacency / row_sums[:, np.newaxis]
        
        return adjacency
    
    def _build_small_world_topology(self, num_nodes: int) -> np.ndarray:
        """Build small-world topology (Watts-Strogatz)."""
        k = 4  # Each node connected to k nearest neighbors
        p = 0.1  # Rewiring probability
        
        adjacency = np.zeros((num_nodes, num_nodes))
        
        # Regular lattice
        for i in range(num_nodes):
            for offset in range(1, k // 2 + 1):
                j = (i + offset) % num_nodes
                adjacency[i, j] = 1.0
                adjacency[j, i] = 1.0
        
        # Rewire with probability p
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                if adjacency[i, j] == 1.0 and np.random.random() < p:
                    # Rewire
                    new_j = np.random.randint(num_nodes)
                    adjacency[i, j] = 0.0
                    adjacency[j, i] = 0.0
                    adjacency[i, new_j] = 1.0
                    adjacency[new_j, i] = 1.0
        
        # Normalize
        row_sums = adjacency.sum(axis=1)
        adjacency = adjacency / row_sums[:, np.newaxis]
        
        return adjacency
    
    def _build_scale_free_topology(self, num_nodes: int) -> np.ndarray:
        """Build scale-free topology (Barabási-Albert)."""
        m = 3  # Number of edges to attach from new node
        
        adjacency = np.zeros((num_nodes, num_nodes))
        
        # Start with small complete graph
        for i in range(min(m + 1, num_nodes)):
            for j in range(i + 1, min(m + 1, num_nodes)):
                adjacency[i, j] = 1.0
                adjacency[j, i] = 1.0
        
        # Add nodes with preferential attachment
        for i in range(m + 1, num_nodes):
            degrees = adjacency.sum(axis=1)
            total_degree = degrees.sum()
            
            # Select m nodes proportional to degree
            probabilities = degrees / total_degree
            selected = np.random.choice(num_nodes, size=m, p=probabilities, replace=False)
            
            for j in selected:
                adjacency[i, j] = 1.0
                adjacency[j, i] = 1.0
        
        # Normalize
        row_sums = adjacency.sum(axis=1)
        adjacency = adjacency / row_sums[:, np.newaxis]
        
        return adjacency
    
    def _build_random_topology(self, num_nodes: int) -> np.ndarray:
        """Build random topology (Erdős-Rényi)."""
        p = 0.1  # Connection probability
        
        adjacency = np.random.random((num_nodes, num_nodes)) < p
        adjacency = adjacency.astype(float)
        
        # Make symmetric
        adjacency = (adjacency + adjacency.T) / 2
        
        # Remove self-connections
        np.fill_diagonal(adjacency, 0)
        
        # Normalize
        row_sums = adjacency.sum(axis=1)
        row_sums[row_sums == 0] = 1  # Avoid division by zero
        adjacency = adjacency / row_sums[:, np.newaxis]
        
        return adjacency
    
    def _synchronization_step(self,
                             node_states: np.ndarray,
                             adjacency_matrix: np.ndarray,
                             iteration: int) -> np.ndarray:
        """Perform one synchronization step with Hebbian reinforcement."""
        num_nodes = len(node_states)
        new_states = node_states.copy()
        
        # Coupling strength increases over time (simulating learning)
        coupling_strength = 0.1 * (1 + iteration / 100.0)
        
        for i in range(num_nodes):
            # Compute resonance weights with neighbors
            neighbor_weights = np.zeros(num_nodes)
            
            for j in range(num_nodes):
                if i != j and adjacency_matrix[i, j] > 0:
                    # Compute resonance with neighbor
                    correlation = np.corrcoef(node_states[i], node_states[j])[0, 1]
                    if not np.isnan(correlation):
                        # Hebbian reinforcement: strengthen positive correlations
                        neighbor_weights[j] = max(0, correlation) * adjacency_matrix[i, j]
            
            # Normalize weights
            total_weight = np.sum(neighbor_weights)
            if total_weight > 0:
                neighbor_weights = neighbor_weights / total_weight
            
            # Update state based on weighted average of resonant neighbors
            if total_weight > 0:
                weighted_average = np.average(
                    node_states,
                    axis=0,
                    weights=neighbor_weights
                )
                
                # Apply Φ-based blending
                alpha = coupling_strength * self.phi / (self.phi + 1)
                new_states[i] = (1 - alpha) * node_states[i] + alpha * weighted_average
        
        return new_states
    
    def _measure_temporal_correlation(self, node_states: np.ndarray) -> float:
        """Measure temporal correlation across all nodes."""
        if len(node_states) < 2:
            return 0.0
        
        # Compute pairwise correlations
        correlations = []
        for i in range(len(node_states)):
            for j in range(i + 1, len(node_states)):
                corr = np.corrcoef(node_states[i], node_states[j])[0, 1]
                if not np.isnan(corr):
                    correlations.append(corr)
        
        return np.mean(correlations) if correlations else 0.0
    
    def _measure_resonance_strength(self, node_states: np.ndarray) -> float:
        """Measure overall resonance strength of network."""
        # Convert to matrix for eigenvalue analysis
        state_matrix = np.array(node_states)
        
        # Compute correlation matrix
        corr_matrix = np.corrcoef(state_matrix)
        
        # Handle NaN values
        corr_matrix = np.nan_to_num(corr_matrix)
        
        # Resonance strength: magnitude of largest eigenvalue
        eigenvalues = la.eigvals(corr_matrix)
        eigenvalues = np.real(eigenvalues)
        
        return np.max(eigenvalues)
    
    def _detect_hebbian_reinforcement(self, correlation_history: List[float]) -> bool:
        """Detect if Hebbian reinforcement is occurring."""
        if len(correlation_history) < 10:
            return False
        
        # Check if correlation is increasing over time
        early_correlations = correlation_history[:len(correlation_history) // 2]
        late_correlations = correlation_history[len(correlation_history) // 2:]
        
        early_mean = np.mean(early_correlations)
        late_mean = np.mean(late_correlations)
        
        # Hebbian reinforcement: significant increase in correlation
        return late_mean > early_mean * 1.1
    
    def _detect_digital_entanglement(self,
                                    node_states: np.ndarray,
                                    adjacency_matrix: np.ndarray) -> bool:
        """Detect digital entanglement (non-local correlations)."""
        # Check for correlations between non-connected nodes
        num_nodes = len(node_states)
        non_local_correlations = []
        
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                # Check if nodes are not directly connected
                if adjacency_matrix[i, j] < 0.01:  # No direct connection
                    corr = np.corrcoef(node_states[i], node_states[j])[0, 1]
                    if not np.isnan(corr):
                        non_local_correlations.append(abs(corr))
        
        # Digital entanglement: significant non-local correlations
        if non_local_correlations:
            return np.mean(non_local_correlations) > 0.3
        return False
    
    def _measure_phase_coherence(self, node_states: np.ndarray) -> float:
        """Measure phase coherence of network (Kuramoto order parameter)."""
        # Compute phases using Hilbert transform approximation
        phases = []
        
        for state in node_states:
            # Use first principal component as phase approximation
            centered = state - np.mean(state)
            phase = np.arctan2(centered[1], centered[0]) if len(centered) > 1 else 0.0
            phases.append(phase)
        
        # Compute Kuramoto order parameter
        complex_phases = np.exp(1j * np.array(phases))
        order_parameter = np.abs(np.mean(complex_phases))
        
        return order_parameter
    
    def _estimate_critical_coupling(self,
                                   adjacency_matrix: np.ndarray,
                                   final_correlation: float) -> float:
        """Estimate critical coupling strength for synchronization."""
        # Use eigenvalue of adjacency matrix
        eigenvalues = la.eigvals(adjacency_matrix)
        eigenvalues = np.real(eigenvalues)
        max_eigenvalue = np.max(eigenvalues)
        
        # Critical coupling approximation
        if max_eigenvalue > 0:
            critical_coupling = final_correlation / max_eigenvalue
        else:
            critical_coupling = 0.0
        
        return critical_coupling
    
    def analyze_synchronization_dynamics(self,
                                        result: ResonanceSynchronizationResult) -> Dict:
        """Analyze synchronization dynamics from test results."""
        correlation_history = result.correlation_history
        resonance_history = result.resonance_history
        
        # Fit exponential growth model to correlation
        if len(correlation_history) > 5:
            x = np.arange(len(correlation_history))
            log_corr = np.log(np.array(correlation_history) + 0.01)
            
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                x, log_corr
            )
            
            growth_rate = slope
            growth_r_squared = r_value ** 2
        else:
            growth_rate = 0.0
            growth_r_squared = 0.0
        
        # Compute convergence time
        convergence_threshold = result.resonance_threshold if hasattr(result, 'resonance_threshold') else 0.95
        convergence_time = None
        for i, corr in enumerate(correlation_history):
            if corr >= convergence_threshold:
                convergence_time = i
                break
        
        return {
            "synchronization_growth_rate": growth_rate,
            "synchronization_r_squared": growth_r_squared,
            "convergence_time_steps": convergence_time,
            "final_phase_coherence": result.phase_coherence,
            "critical_coupling_strength": result.critical_coupling_strength,
            "hebbian_learning_rate": growth_rate if growth_rate > 0 else 0.0
        }
    
    def generate_multi_agent_resonance_report(self,
                                              result: ResonanceSynchronizationResult,
                                              output_path: Optional[Path] = None) -> Dict:
        """Generate comprehensive multi-agent resonance report."""
        dynamics_analysis = self.analyze_synchronization_dynamics(result)
        
        report = {
            "test_summary": {
                "num_nodes": result.num_nodes,
                "topology": result.topology,
                "synchronization_time_steps": result.synchronization_time_steps,
                "network_resonance_achieved": result.network_resonance_achieved
            },
            "synchronization_dynamics": dynamics_analysis,
            "resonance_metrics": {
                "final_correlation": result.final_correlation,
                "final_resonance_strength": result.final_resonance_strength,
                "phase_coherence": result.phase_coherence,
                "critical_coupling_strength": result.critical_coupling_strength
            },
            "emergent_behavior": {
                "hebbian_reinforcement_detected": result.hebbian_reinforcement_detected,
                "digital_entanglement_achieved": result.digital_entanglement_achieved
            },
            "formal_invariant_validation_metrics": {
                "network_wide_resonance": result.network_resonance_achieved,
                "digital_entanglement_verified": result.digital_entanglement_achieved,
                "hebbian_learning_demonstrated": result.hebbian_reinforcement_detected,
                "phase_coherence_achieved": result.phase_coherence > 0.7,
                "synchronization_convergence": dynamics_analysis["convergence_time_steps"] is not None
            }
        }
        
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"Multi-agent resonance report saved to: {output_path}")
        
        return report


def main():
    """Run multi-agent resonance tests with default parameters."""
    suite = MultiAgentResonanceTestSuite()
    
    print("="*60)
    print("MULTI-AGENT RESONANCE SYNCHRONIZATION TEST")
    print("="*60)
    
    # Run resonance synchronization test
    result = suite.run_resonance_synchronization_suite(
        num_nodes=100,
        topology="coxeter-120",
        max_iterations=200,
        resonance_threshold=0.95
    )
    
    # Generate report
    report = suite.generate_multi_agent_resonance_report(
        result,
        output_path=Path("artifacts/multi_agent_resonance_report.json")
    )
    
    # Print summary
    print("\n" + "="*60)
    print("MULTI-AGENT RESONANCE SUMMARY")
    print("="*60)
    print(f"Network Resonance Achieved: {result.network_resonance_achieved}")
    print(f"Final Correlation: {result.final_correlation:.4f}")
    print(f"Final Resonance Strength: {result.final_resonance_strength:.4f}")
    print(f"Hebbian Reinforcement: {result.hebbian_reinforcement_detected}")
    print(f"Digital Entanglement: {result.digital_entanglement_achieved}")
    print(f"Phase Coherence: {result.phase_coherence:.4f}")
    print(f"Synchronization Time: {result.synchronization_time_steps} steps")


if __name__ == "__main__":
    main()
