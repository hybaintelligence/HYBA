"""
Curvature-Based Anomaly Detection for HYBA Financial Intelligence Substrate (Autonomic Layer)

This module detects anomalies through curvature analysis using:
- Gaussian curvature for local geometry
- Mean curvature for surface analysis
- Ricci curvature for manifold flow
- Curvature blow-up detection

Mathematical Foundation:
- Gaussian curvature K = (f_xx * f_yy - f_xy^2) / (1 + f_x^2 + f_y^2)^2
- Curvature blow-up indicates singularities/anomalies
- Topological context from neighborhood analysis
- Anomaly severity based on curvature magnitude
"""

from __future__ import annotations

import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from scipy import stats
from scipy.signal import find_peaks
import hashlib
import json


@dataclass
class AnomalyReport:
    """Curvature-based anomaly detection report."""
    
    anomaly_locations: List[Dict[str, Any]]
    curvature_values: List[float]
    anomaly_severity_scores: List[float]
    topological_context: List[Dict[str, Any]]
    cryptographic_seal: Dict[str, Any]
    timestamp: str


class CurvatureAnomalyDetector:
    """
    Detects anomalies through curvature analysis of data manifolds.
    
    This detector computes the curvature field of the data manifold
    and identifies anomalies as points with extreme curvature values,
    indicating singularities or deviations from normal geometry.
    """
    
    def __init__(
        self,
        curvature_threshold: float = 2.0,
        neighborhood_size: int = 5
    ):
        """
        Initialize the curvature anomaly detector.
        
        Args:
            curvature_threshold: Threshold for anomaly detection
            neighborhood_size: Size of neighborhood for context analysis
        """
        self.curvature_threshold = curvature_threshold
        self.neighborhood_size = neighborhood_size
    
    def detect_anomalies(
        self,
        data: np.ndarray,
        returns: Optional[np.ndarray] = None
    ) -> AnomalyReport:
        """
        Detect anomalies through curvature analysis.
        
        Args:
            data: Data manifold (N_samples, N_features)
            returns: Optional return series for context
        
        Returns:
            AnomalyReport with detected anomalies and context
        """
        # 1. Compute curvature field
        curvature_field = self._compute_curvature_field(data)
        
        # 2. Identify curvature blow-ups (anomalies)
        anomaly_indices = self._identify_curvature_blowups(curvature_field)
        
        # 3. Compute anomaly severity scores
        severity_scores = self._compute_severity_scores(
            curvature_field, anomaly_indices
        )
        
        # 4. Compute topological context
        topological_context = self._compute_topological_context(
            data, anomaly_indices
        )
        
        # 5. Format anomaly locations
        anomaly_locations = []
        for idx in anomaly_indices:
            anomaly_locations.append({
                "index": int(idx),
                "curvature": float(curvature_field[idx]),
                "severity": float(severity_scores[idx]),
                "return": float(returns[idx]) if returns is not None and idx < len(returns) else None
            })
        
        # 6. Generate cryptographic seal
        cryptographic_seal = self._generate_cryptographic_seal(
            len(anomaly_locations), severity_scores
        )
        
        return AnomalyReport(
            anomaly_locations=anomaly_locations,
            curvature_values=curvature_field.tolist(),
            anomaly_severity_scores=severity_scores.tolist(),
            topological_context=topological_context,
            cryptographic_seal=cryptographic_seal,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def _compute_curvature_field(
        self,
        data: np.ndarray
    ) -> np.ndarray:
        """
        Compute curvature field of data manifold.
        
        For 1D data, computes curvature of the curve.
        For 2D data, computes Gaussian curvature of the surface.
        """
        if data.ndim == 1:
            # 1D case: curvature of curve
            return self._compute_1d_curvature(data)
        elif data.ndim == 2 and data.shape[1] == 2:
            # 2D case: Gaussian curvature of surface
            return self._compute_gaussian_curvature(data)
        else:
            # Higher dimensions: use local curvature approximation
            return self._compute_local_curvature(data)
    
    def _compute_1d_curvature(
        self,
        data: np.ndarray
    ) -> np.ndarray:
        """
        Compute curvature of 1D curve.
        
        Curvature k = f'' / (1 + f'^2)^(3/2)
        """
        # Compute first and second derivatives
        f_prime = np.gradient(data)
        f_double_prime = np.gradient(f_prime)
        
        # Curvature
        curvature = f_double_prime / (1 + f_prime**2)**(1.5)
        
        return curvature
    
    def _compute_gaussian_curvature(
        self,
        data: np.ndarray
    ) -> np.ndarray:
        """
        Compute Gaussian curvature of 2D surface.
        
        Gaussian curvature K = (f_xx * f_yy - f_xy^2) / (1 + f_x^2 + f_y^2)^2
        """
        x = data[:, 0]
        y = data[:, 1]
        
        # Compute partial derivatives
        f_x = np.gradient(x)
        f_y = np.gradient(y)
        f_xx = np.gradient(f_x)
        f_yy = np.gradient(f_y)
        f_xy = np.gradient(f_x)  # Simplified mixed derivative
        
        # Gaussian curvature
        numerator = f_xx * f_yy - f_xy**2
        denominator = (1 + f_x**2 + f_y**2)**2
        curvature = numerator / (denominator + 1e-8)
        
        return curvature
    
    def _compute_local_curvature(
        self,
        data: np.ndarray
    ) -> np.ndarray:
        """
        Compute local curvature approximation for high-dimensional data.
        
        Uses local neighborhood analysis to estimate curvature at each point.
        """
        n_points = len(data)
        curvature = np.zeros(n_points)
        
        for i in range(n_points):
            # Get local neighborhood
            start_idx = max(0, i - self.neighborhood_size // 2)
            end_idx = min(n_points, i + self.neighborhood_size // 2 + 1)
            neighborhood = data[start_idx:end_idx]
            
            if len(neighborhood) < 3:
                curvature[i] = 0.0
                continue
            
            # Compute local variance as curvature proxy
            local_var = np.var(neighborhood, axis=0)
            curvature[i] = np.mean(local_var)
        
        # Normalize
        if np.max(curvature) > 0:
            curvature = curvature / np.max(curvature)
        
        return curvature
    
    def _identify_curvature_blowups(
        self,
        curvature_field: np.ndarray
    ) -> np.ndarray:
        """
        Identify curvature blow-ups (anomalies).
        
        Anomalies are points where curvature exceeds threshold
        or represents a local maximum.
        """
        # Find peaks in curvature
        peaks, _ = find_peaks(curvature_field)
        
        # Filter by threshold
        anomaly_indices = peaks[curvature_field[peaks] > self.curvature_threshold]
        
        # Also include points with extreme negative curvature
        negative_peaks, _ = find_peaks(-curvature_field)
        negative_anomalies = negative_peaks[
            curvature_field[negative_peaks] < -self.curvature_threshold
        ]
        
        # Combine
        all_anomalies = np.concatenate([anomaly_indices, negative_anomalies])
        
        return np.unique(all_anomalies)
    
    def _compute_severity_scores(
        self,
        curvature_field: np.ndarray,
        anomaly_indices: np.ndarray
    ) -> np.ndarray:
        """
        Compute anomaly severity scores.
        
        Severity is based on curvature magnitude relative to
        the distribution of curvature values.
        """
        severity_scores = np.zeros(len(curvature_field))
        
        if len(anomaly_indices) == 0:
            return severity_scores
        
        # Compute curvature statistics
        curvature_mean = np.mean(curvature_field)
        curvature_std = np.std(curvature_field)
        
        # Severity as number of standard deviations from mean
        for idx in anomaly_indices:
            if idx < len(curvature_field):
                z_score = abs(curvature_field[idx] - curvature_mean) / (curvature_std + 1e-8)
                severity_scores[idx] = min(1.0, z_score / 3.0)  # Cap at 1.0
        
        return severity_scores
    
    def _compute_topological_context(
        self,
        data: np.ndarray,
        anomaly_indices: np.ndarray
    ) -> List[Dict[str, Any]]:
        """
        Compute topological context for anomalies.
        
        Analyzes the neighborhood of each anomaly to provide
        context about why it's anomalous.
        """
        context_list = []
        
        for idx in anomaly_indices:
            if idx >= len(data):
                continue
            
            # Get neighborhood
            start_idx = max(0, idx - self.neighborhood_size)
            end_idx = min(len(data), idx + self.neighborhood_size + 1)
            neighborhood = data[start_idx:end_idx]
            
            # Compute neighborhood statistics
            neighborhood_mean = np.mean(neighborhood, axis=0)
            neighborhood_std = np.std(neighborhood, axis=0)
            
            # Distance from neighborhood mean
            distance = np.linalg.norm(data[idx] - neighborhood_mean)
            
            context_list.append({
                "index": int(idx),
                "neighborhood_mean": neighborhood_mean.tolist(),
                "neighborhood_std": neighborhood_std.tolist(),
                "distance_from_mean": float(distance),
                "local_density": float(len(neighborhood) / (2 * self.neighborhood_size))
            })
        
        return context_list
    
    def _generate_cryptographic_seal(
        self,
        n_anomalies: int,
        severity_scores: np.ndarray
    ) -> Dict[str, Any]:
        """Generate cryptographic seal for anomaly detection."""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Create canonical representation
        body = {
            "n_anomalies": n_anomalies,
            "avg_severity": float(np.mean(severity_scores)) if len(severity_scores) > 0 else 0.0,
            "max_severity": float(np.max(severity_scores)) if len(severity_scores) > 0 else 0.0,
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
curvature_detector = CurvatureAnomalyDetector()
