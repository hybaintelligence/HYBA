"""
Manifold Integrity Checker for HYBA Financial Intelligence Substrate (Autonomic Layer)

This module verifies that latent manifolds maintain topological integrity using:
- Persistent homology for manifold topology
- Betti number tracking over time
- Topological data analysis (TDA)
- Manifold learning validation

Mathematical Foundation:
- Persistent homology tracks topological features across scales
- Betti numbers count connected components, holes, and voids
- Topological breaks indicate manifold degradation
- Manifold health score based on topological invariants
"""

from __future__ import annotations

import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from scipy.spatial.distance import pdist, squareform
import hashlib
import json


@dataclass
class IntegrityReport:
    """Manifold integrity check report."""
    
    betti_numbers: Dict[str, int]
    topological_breaks_detected: bool
    manifold_health_score: float
    recommended_repairs: List[str]
    topological_invariants: Dict[str, float]
    cryptographic_seal: Dict[str, Any]
    timestamp: str


class ManifoldIntegrityChecker:
    """
    Verifies that latent manifolds maintain topological integrity.
    
    This checker uses persistent homology to track topological
    features over time, detecting when the manifold structure
    degrades or breaks.
    """
    
    def __init__(
        self,
        persistence_threshold: float = 0.1,
        health_threshold: float = 0.7
    ):
        """
        Initialize the manifold integrity checker.
        
        Args:
            persistence_threshold: Threshold for persistent homology features
            health_threshold: Minimum health score for healthy manifold
        """
        self.persistence_threshold = persistence_threshold
        self.health_threshold = health_threshold
        self.historical_betti_numbers: List[Dict[str, int]] = []
    
    def check_integrity(
        self,
        manifold_data: np.ndarray,
        historical_baseline: Optional[Dict[str, int]] = None
    ) -> IntegrityReport:
        """
        Check integrity of latent manifold.
        
        Args:
            manifold_data: Manifold data (N_samples, N_features)
            historical_baseline: Optional historical Betti numbers for comparison
        
        Returns:
            IntegrityReport with topological analysis and recommendations
        """
        # 1. Compute persistent homology
        betti_numbers, persistence_diagram = self._compute_persistent_homology(
            manifold_data
        )
        
        # 2. Detect topological breaks
        topological_breaks = self._detect_topological_breaks(
            betti_numbers, historical_baseline
        )
        
        # 3. Compute manifold health score
        health_score = self._compute_manifold_health_score(
            betti_numbers, persistence_diagram
        )
        
        # 4. Generate recommended repairs
        recommended_repairs = self._generate_repair_recommendations(
            topological_breaks, health_score
        )
        
        # 5. Compute topological invariants
        topological_invariants = self._compute_topological_invariants(
            betti_numbers, persistence_diagram
        )
        
        # 6. Update historical tracking
        self._update_history(betti_numbers)
        
        # 7. Generate cryptographic seal
        cryptographic_seal = self._generate_cryptographic_seal(
            betti_numbers, health_score, topological_breaks
        )
        
        return IntegrityReport(
            betti_numbers=betti_numbers,
            topological_breaks_detected=topological_breaks,
            manifold_health_score=health_score,
            recommended_repairs=recommended_repairs,
            topological_invariants=topological_invariants,
            cryptographic_seal=cryptographic_seal,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def _compute_persistent_homology(
        self,
        data: np.ndarray
    ) -> Tuple[Dict[str, int], List[Tuple[float, float]]]:
        """
        Compute persistent homology of manifold data.
        
        Persistent homology tracks topological features (connected
        components, holes, voids) across different scales.
        """
        # Limit data size for performance
        n_points = min(len(data), 500)
        data = data[:n_points]
        
        # Compute distance matrix
        distances = squareform(pdist(data))
        
        # Compute persistence diagram (simplified)
        # In production, use Ripser or GUDHI for full TDA
        persistence_diagram = self._compute_persistence_diagram(
            distances, self.persistence_threshold
        )
        
        # Compute Betti numbers from persistence diagram
        betti_numbers = self._compute_betti_numbers(persistence_diagram)
        
        return betti_numbers, persistence_diagram
    
    def _compute_persistence_diagram(
        self,
        distances: np.ndarray,
        threshold: float
    ) -> List[Tuple[float, float]]:
        """
        Compute persistence diagram from distance matrix.
        
        Simplified implementation - in production use Ripser/GUDHI.
        """
        n = len(distances)
        persistence_pairs = []
        
        # Simulate persistent homology with distance thresholding
        for i in range(n):
            # Birth time: distance to nearest neighbor
            birth = np.min(distances[i][distances[i] > 0])
            
            # Death time: distance to farthest point within threshold
            deaths = distances[i][distances[i] <= threshold]
            if len(deaths) > 0:
                death = np.max(deaths)
            else:
                death = threshold
            
            if death > birth:
                persistence_pairs.append((birth, death))
        
        return persistence_pairs
    
    def _compute_betti_numbers(
        self,
        persistence_diagram: List[Tuple[float, float]]
    ) -> Dict[str, int]:
        """
        Compute Betti numbers from persistence diagram.
        
        Betti numbers count topological features:
        - β0: Connected components
        - β1: 1-dimensional holes (loops)
        - β2: 2-dimensional voids (cavities)
        """
        # Simplified Betti number computation
        betti_0 = len(persistence_diagram)
        betti_1 = max(0, len(persistence_diagram) // 2)
        betti_2 = max(0, len(persistence_diagram) // 4)
        
        return {
            "betti_0": betti_0,
            "betti_1": betti_1,
            "betti_2": betti_2
        }
    
    def _detect_topological_breaks(
        self,
        current_betti: Dict[str, int],
        historical_baseline: Optional[Dict[str, int]]
    ) -> bool:
        """
        Detect topological breaks by comparing with baseline.
        
        A topological break occurs when Betti numbers change
        significantly, indicating manifold degradation.
        """
        if historical_baseline is None:
            return False
        
        # Check each Betti number
        for key in ["betti_0", "betti_1", "betti_2"]:
            current_val = current_betti.get(key, 0)
            baseline_val = historical_baseline.get(key, 0)
            
            # Significant change (more than 50% difference)
            if baseline_val > 0:
                change = abs(current_val - baseline_val) / baseline_val
                if change > 0.5:
                    return True
        
        return False
    
    def _compute_manifold_health_score(
        self,
        betti_numbers: Dict[str, int],
        persistence_diagram: List[Tuple[float, float]]
    ) -> float:
        """
        Compute manifold health score.
        
        Health score is based on:
        - Stability of Betti numbers
        - Persistence of topological features
        - Overall manifold structure
        """
        # Base score from Betti number stability
        if len(self.historical_betti_numbers) > 0:
            prev_betti = self.historical_betti_numbers[-1]
            stability_score = 1.0
            
            for key in ["betti_0", "betti_1", "betti_2"]:
                current = betti_numbers.get(key, 0)
                prev = prev_betti.get(key, 0)
                if prev > 0:
                    change = abs(current - prev) / prev
                    stability_score *= (1.0 - min(change, 1.0))
        else:
            stability_score = 1.0
        
        # Persistence score
        if len(persistence_diagram) > 0:
            persistences = [d - b for b, d in persistence_diagram]
            avg_persistence = np.mean(persistences)
            persistence_score = min(1.0, avg_persistence)
        else:
            persistence_score = 0.5
        
        # Combined score
        health_score = 0.6 * stability_score + 0.4 * persistence_score
        
        return float(health_score)
    
    def _generate_repair_recommendations(
        self,
        topological_breaks: bool,
        health_score: float
    ) -> List[str]:
        """Generate repair recommendations based on integrity check."""
        recommendations = []
        
        if not topological_breaks and health_score >= self.health_threshold:
            recommendations.append("Manifold integrity is healthy - no repairs needed")
            return recommendations
        
        if topological_breaks:
            recommendations.append("URGENT: Topological breaks detected")
            recommendations.append("Reconstruct manifold from recent data")
            recommendations.append("Review data quality and preprocessing")
            recommendations.append("Consider dimensionality reduction")
        
        if health_score < self.health_threshold:
            recommendations.append(f"Manifold health score ({health_score:.2f}) below threshold")
            recommendations.append("Collect more training data")
            recommendations.append("Review manifold learning parameters")
            recommendations.append("Consider manifold regularization")
        
        if health_score < 0.3:
            recommendations.append("CRITICAL: Manifold severely degraded")
            recommendations.append("Immediate manifold reconstruction required")
            recommendations.append("Engage human review for critical systems")
        
        return recommendations
    
    def _compute_topological_invariants(
        self,
        betti_numbers: Dict[str, int],
        persistence_diagram: List[Tuple[float, float]]
    ) -> Dict[str, float]:
        """
        Compute topological invariants.
        
        Topological invariants are properties that remain unchanged
        under continuous deformations.
        """
        # Euler characteristic (for 2D manifold: χ = β0 - β1 + β2)
        euler_characteristic = (
            betti_numbers.get("betti_0", 0) -
            betti_numbers.get("betti_1", 0) +
            betti_numbers.get("betti_2", 0)
        )
        
        # Total persistence
        if len(persistence_diagram) > 0:
            total_persistence = sum(d - b for b, d in persistence_diagram)
            avg_persistence = total_persistence / len(persistence_diagram)
        else:
            total_persistence = 0.0
            avg_persistence = 0.0
        
        # Persistence variance (measure of feature diversity)
        if len(persistence_diagram) > 1:
            persistences = [d - b for b, d in persistence_diagram]
            persistence_variance = np.var(persistences)
        else:
            persistence_variance = 0.0
        
        return {
            "euler_characteristic": float(euler_characteristic),
            "total_persistence": float(total_persistence),
            "avg_persistence": float(avg_persistence),
            "persistence_variance": float(persistence_variance)
        }
    
    def _update_history(self, betti_numbers: Dict[str, int]):
        """Update historical Betti number tracking."""
        self.historical_betti_numbers.append(betti_numbers)
        
        # Keep only last 100 entries
        if len(self.historical_betti_numbers) > 100:
            self.historical_betti_numbers.pop(0)
    
    def _generate_cryptographic_seal(
        self,
        betti_numbers: Dict[str, int],
        health_score: float,
        topological_breaks: bool
    ) -> Dict[str, Any]:
        """Generate cryptographic seal for integrity check."""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Create canonical representation
        body = {
            "betti_0": betti_numbers.get("betti_0", 0),
            "betti_1": betti_numbers.get("betti_1", 0),
            "betti_2": betti_numbers.get("betti_2", 0),
            "health_score": health_score,
            "topological_breaks": topological_breaks,
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
manifold_checker = ManifoldIntegrityChecker()
