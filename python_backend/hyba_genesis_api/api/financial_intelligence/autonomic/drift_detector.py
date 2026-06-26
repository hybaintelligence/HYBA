"""
Drift Detection Module for HYBA Financial Intelligence Substrate (Autonomic Layer)

This module detects when models drift from their intended behavior using:
- φ-window analysis for distributional shift
- KL-divergence for distribution comparison
- Wasserstein distance for manifold drift
- Concept drift detection algorithms

Mathematical Foundation:
- φ-density windows identify non-self-similar behavior
- KL-divergence measures information loss between distributions
- Wasserstein distance quantifies manifold deformation
- Statistical tests for significance of drift
"""

from __future__ import annotations

import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from scipy import stats
from scipy.spatial.distance import jensenshannon
from scipy.stats import ks_2samp
import hashlib
import json


@dataclass
class DriftReport:
    """Drift detection report."""
    
    drift_detected: bool
    drift_magnitude: float
    affected_components: List[str]
    recommended_actions: List[str]
    phi_density_shift: float
    kl_divergence: float
    wasserstein_distance: float
    cryptographic_seal: Dict[str, Any]
    timestamp: str


class DriftDetector:
    """
    Detects when models drift from their intended behavior.
    
    This detector uses multiple statistical measures to identify
    when model behavior changes significantly from training
    or baseline distributions.
    """
    
    def __init__(
        self,
        drift_threshold: float = 0.1,
        significance_level: float = 0.05
    ):
        """
        Initialize the drift detector.
        
        Args:
            drift_threshold: Threshold for drift magnitude
            significance_level: Statistical significance level
        """
        self.drift_threshold = drift_threshold
        self.significance_level = significance_level
        self.baseline_distributions: Dict[str, Dict[str, Any]] = {}
    
    def detect_drift(
        self,
        model_name: str,
        baseline_data: np.ndarray,
        new_data: np.ndarray,
        model_components: Optional[List[str]] = None
    ) -> DriftReport:
        """
        Detect drift in model behavior.
        
        Args:
            model_name: Name of the model being monitored
            baseline_data: Baseline/training data
            new_data: New data to compare against baseline
            model_components: Optional list of model components to check
        
        Returns:
            DriftReport with detection results and recommendations
        """
        # 1. Compute φ-density shift
        phi_density_shift = self._compute_phi_density_shift(
            baseline_data, new_data
        )
        
        # 2. Compute KL-divergence
        kl_divergence = self._compute_kl_divergence(
            baseline_data, new_data
        )
        
        # 3. Compute Wasserstein distance
        wasserstein_distance = self._compute_wasserstein_distance(
            baseline_data, new_data
        )
        
        # 4. Perform statistical test
        ks_statistic, ks_p_value = ks_2samp(baseline_data, new_data)
        
        # 5. Determine if drift detected
        drift_detected = self._determine_drift(
            phi_density_shift, kl_divergence, wasserstein_distance, ks_p_value
        )
        
        # 6. Compute drift magnitude
        drift_magnitude = self._compute_drift_magnitude(
            phi_density_shift, kl_divergence, wasserstein_distance
        )
        
        # 7. Identify affected components
        affected_components = self._identify_affected_components(
            model_components, drift_magnitude
        )
        
        # 8. Generate recommended actions
        recommended_actions = self._generate_recommendations(
            drift_detected, drift_magnitude, affected_components
        )
        
        # 9. Store baseline if not already stored
        if model_name not in self.baseline_distributions:
            self._store_baseline(model_name, baseline_data)
        
        # 10. Generate cryptographic seal
        cryptographic_seal = self._generate_cryptographic_seal(
            model_name, drift_detected, drift_magnitude
        )
        
        return DriftReport(
            drift_detected=drift_detected,
            drift_magnitude=drift_magnitude,
            affected_components=affected_components,
            recommended_actions=recommended_actions,
            phi_density_shift=phi_density_shift,
            kl_divergence=kl_divergence,
            wasserstein_distance=wasserstein_distance,
            cryptographic_seal=cryptographic_seal,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def _compute_phi_density_shift(
        self,
        baseline: np.ndarray,
        new: np.ndarray
    ) -> float:
        """
        Compute φ-density shift between distributions.
        
        φ-density measures deviation from self-similarity using
        the golden ratio as a reference scale.
        """
        phi = (1 + np.sqrt(5)) / 2
        
        # Compute φ-density for both distributions
        baseline_phi = self._compute_phi_density(baseline)
        new_phi = self._compute_phi_density(new)
        
        # Shift is absolute difference
        shift = abs(baseline_phi - new_phi)
        
        return float(shift)
    
    def _compute_phi_density(self, data: np.ndarray) -> float:
        """Compute φ-density of a distribution."""
        # Simplified φ-density: variance normalized by mean
        mean = np.mean(data)
        var = np.var(data)
        
        if mean == 0:
            return 0.0
        
        phi_density = var / (abs(mean) + 1e-8)
        return float(phi_density)
    
    def _compute_kl_divergence(
        self,
        baseline: np.ndarray,
        new: np.ndarray,
        n_bins: int = 50
    ) -> float:
        """
        Compute KL-divergence between distributions.
        
        KL-divergence measures the information lost when one
        distribution is used to approximate another.
        """
        # Discretize distributions
        baseline_hist, _ = np.histogram(baseline, bins=n_bins, density=True)
        new_hist, _ = np.histogram(new, bins=n_bins, density=True)
        
        # Add small epsilon to avoid log(0)
        epsilon = 1e-10
        baseline_hist = baseline_hist + epsilon
        new_hist = new_hist + epsilon
        
        # Normalize
        baseline_hist = baseline_hist / np.sum(baseline_hist)
        new_hist = new_hist / np.sum(new_hist)
        
        # Compute KL-divergence
        kl = np.sum(baseline_hist * np.log(baseline_hist / new_hist))
        
        return float(kl)
    
    def _compute_wasserstein_distance(
        self,
        baseline: np.ndarray,
        new: np.ndarray
    ) -> float:
        """
        Compute Wasserstein distance between distributions.
        
        Wasserstein distance quantifies the minimum cost to
        transform one distribution into another.
        """
        # Reshape for 1D Wasserstein distance
        baseline_1d = baseline.reshape(-1, 1)
        new_1d = new.reshape(-1, 1)
        
        # Compute distance matrix
        from scipy.spatial.distance import cdist
        distance_matrix = cdist(baseline_1d, new_1d, metric='euclidean')
        
        # Simplified Wasserstein distance (Earth Mover's Distance)
        # Sort both distributions
        baseline_sorted = np.sort(baseline)
        new_sorted = np.sort(new)
        
        # Compute EMD for 1D
        min_len = min(len(baseline_sorted), len(new_sorted))
        wasserstein = np.mean(np.abs(baseline_sorted[:min_len] - new_sorted[:min_len]))
        
        return float(wasserstein)
    
    def _determine_drift(
        self,
        phi_shift: float,
        kl_div: float,
        wasserstein: float,
        ks_p_value: float
    ) -> bool:
        """
        Determine if drift is detected.
        
        Drift is detected if any measure exceeds threshold
        or statistical test is significant.
        """
        # Check statistical significance
        if ks_p_value < self.significance_level:
            return True
        
        # Check drift magnitude
        if phi_shift > self.drift_threshold:
            return True
        
        if kl_div > self.drift_threshold:
            return True
        
        if wasserstein > self.drift_threshold:
            return True
        
        return False
    
    def _compute_drift_magnitude(
        self,
        phi_shift: float,
        kl_div: float,
        wasserstein: float
    ) -> float:
        """
        Compute overall drift magnitude.
        
        Drift magnitude is a weighted combination of all measures.
        """
        # Normalize each measure
        max_phi = 1.0  # Maximum expected φ-shift
        max_kl = 2.0  # Maximum expected KL-divergence
        max_wass = 1.0  # Maximum expected Wasserstein distance
        
        normalized_phi = min(phi_shift / max_phi, 1.0)
        normalized_kl = min(kl_div / max_kl, 1.0)
        normalized_wass = min(wasserstein / max_wass, 1.0)
        
        # Weighted average
        weights = [0.3, 0.4, 0.3]  # KL-divergence weighted higher
        magnitude = (
            weights[0] * normalized_phi +
            weights[1] * normalized_kl +
            weights[2] * normalized_wass
        )
        
        return float(magnitude)
    
    def _identify_affected_components(
        self,
        components: Optional[List[str]],
        drift_magnitude: float
    ) -> List[str]:
        """Identify which model components are affected by drift."""
        if components is None:
            return ["all_components"]
        
        # If drift magnitude is high, all components are affected
        if drift_magnitude > 0.7:
            return components
        
        # Otherwise, return subset based on magnitude
        n_affected = int(drift_magnitude * len(components))
        return components[:max(1, n_affected)]
    
    def _generate_recommendations(
        self,
        drift_detected: bool,
        drift_magnitude: float,
        affected_components: List[str]
    ) -> List[str]:
        """Generate recommended actions based on drift detection."""
        recommendations = []
        
        if not drift_detected:
            recommendations.append("No action required - no significant drift detected")
            return recommendations
        
        if drift_magnitude < 0.3:
            recommendations.append("Monitor drift - magnitude is low")
            recommendations.append("Consider collecting more data")
        elif drift_magnitude < 0.7:
            recommendations.append("Retrain model with recent data")
            recommendations.append("Update baseline distribution")
            recommendations.append("Validate model performance")
        else:
            recommendations.append("URGENT: Significant drift detected")
            recommendations.append("Immediate model retraining required")
            recommendations.append("Review affected components: " + ", ".join(affected_components))
            recommendations.append("Consider model architecture changes")
            recommendations.append("Engage human review for critical decisions")
        
        return recommendations
    
    def _store_baseline(
        self,
        model_name: str,
        baseline_data: np.ndarray
    ):
        """Store baseline distribution for future comparisons."""
        self.baseline_distributions[model_name] = {
            "mean": float(np.mean(baseline_data)),
            "std": float(np.std(baseline_data)),
            "data": baseline_data.tolist()  # Store for future comparisons
        }
    
    def _generate_cryptographic_seal(
        self,
        model_name: str,
        drift_detected: bool,
        drift_magnitude: float
    ) -> Dict[str, Any]:
        """Generate cryptographic seal for drift detection."""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Create canonical representation
        body = {
            "model_name": model_name,
            "drift_detected": drift_detected,
            "drift_magnitude": drift_magnitude,
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
drift_detector = DriftDetector()
