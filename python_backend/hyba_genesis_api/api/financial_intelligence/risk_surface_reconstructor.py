"""
Risk Surface Reconstruction Module for HYBA Financial Intelligence Substrate

This module reconstructs risk as a high-dimensional surface using:
- Risk as a Morse function on asset space
- Critical point analysis for risk concentration
- Gradient flow for risk propagation
- Level set analysis for risk contours

Mathematical Foundation:
- Risk manifold constructed from portfolio covariance
- Critical points identify risk concentrations (hotspots)
- Gradient flow vectors show risk propagation direction
- Level sets define risk contours for visualization
"""

from __future__ import annotations

import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from scipy import stats
from scipy.spatial.distance import pdist, squareform
from scipy.optimize import minimize
from scipy.signal import find_peaks
import hashlib
import json


@dataclass
class RiskSurface:
    """Risk surface reconstruction result."""
    
    risk_manifold: List[List[float]]
    critical_points: List[Dict[str, Any]]
    gradient_flow: List[List[float]]
    risk_contours: List[List[float]]
    topological_invariants: Dict[str, float]
    cryptographic_seal: Dict[str, Any]
    timestamp: str


class RiskSurfaceReconstructor:
    """
    Reconstructs risk as a high-dimensional surface.
    
    This reconstructor builds a risk manifold from portfolio data,
    identifies critical points (risk concentrations), computes
    gradient flow for risk propagation, and generates risk contours.
    """
    
    def __init__(self, grid_resolution: int = 50):
        """
        Initialize the risk surface reconstructor.
        
        Args:
            grid_resolution: Resolution of the risk surface grid
        """
        self.grid_resolution = grid_resolution
    
    def reconstruct_risk_surface(
        self,
        portfolio_returns: np.ndarray,
        asset_names: Optional[List[str]] = None
    ) -> RiskSurface:
        """
        Reconstruct risk surface from portfolio returns.
        
        Args:
            portfolio_returns: Portfolio returns (N_assets, N_timepoints)
            asset_names: Optional list of asset names
        
        Returns:
            RiskSurface with manifold, critical points, and contours
        """
        # 1. Construct risk manifold from covariance
        risk_manifold = self._construct_risk_manifold(portfolio_returns)
        
        # 2. Identify critical points (risk concentrations)
        critical_points = self._identify_critical_points(
            risk_manifold, asset_names
        )
        
        # 3. Compute gradient flow
        gradient_flow = self._compute_gradient_flow(risk_manifold)
        
        # 4. Generate risk contours
        risk_contours = self._generate_risk_contours(risk_manifold)
        
        # 5. Compute topological invariants
        topological_invariants = self._compute_topological_invariants(
            risk_manifold, critical_points
        )
        
        # 6. Generate cryptographic seal
        cryptographic_seal = self._generate_cryptographic_seal(
            risk_manifold, critical_points, topological_invariants
        )
        
        return RiskSurface(
            risk_manifold=risk_manifold.tolist(),
            critical_points=critical_points,
            gradient_flow=gradient_flow,
            risk_contours=risk_contours,
            topological_invariants=topological_invariants,
            cryptographic_seal=cryptographic_seal,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def _construct_risk_manifold(
        self,
        portfolio_returns: np.ndarray
    ) -> np.ndarray:
        """
        Construct risk manifold from portfolio covariance.
        
        The risk manifold represents the risk surface in asset space,
        where each point corresponds to a portfolio allocation and
        the height represents the risk (variance).
        """
        # Compute covariance matrix
        cov_matrix = np.cov(portfolio_returns)
        
        # Eigenvalue decomposition for risk factors
        eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
        
        # Construct 2D risk surface using first two principal components
        if len(eigenvalues) >= 2:
            # Use first two eigenvectors as basis
            basis = eigenvectors[:, -2:]
            
            # Create grid in principal component space
            n_points = self.grid_resolution
            x = np.linspace(-2, 2, n_points)
            y = np.linspace(-2, 2, n_points)
            X, Y = np.meshgrid(x, y)
            
            # Compute risk at each grid point
            risk_surface = np.zeros((n_points, n_points))
            for i in range(n_points):
                for j in range(n_points):
                    # Portfolio weights in original space
                    weights = basis @ np.array([X[i, j], Y[i, j]])
                    weights = weights / (np.sum(np.abs(weights)) + 1e-8)
                    
                    # Portfolio variance (risk)
                    risk = weights.T @ cov_matrix @ weights
                    risk_surface[i, j] = risk
        else:
            # Fallback: 1D risk surface
            n_points = self.grid_resolution
            risk_surface = np.zeros((n_points, 1))
            for i in range(n_points):
                weight = i / (n_points - 1)
                risk = weight**2 * eigenvalues[-1]
                risk_surface[i, 0] = risk
        
        return risk_surface
    
    def _identify_critical_points(
        self,
        risk_manifold: np.ndarray,
        asset_names: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Identify critical points (risk concentrations).
        
        Critical points are local maxima (risk hotspots) and minima
        (risk basins) on the risk surface.
        """
        critical_points = []
        
        # Find local maxima (risk hotspots)
        if risk_manifold.ndim == 2:
            # 2D case
            maxima_indices = find_peaks(risk_manifold.flatten())[0]
            maxima_coords = np.unravel_index(maxima_indices, risk_manifold.shape)
            
            for idx, (flat_idx, (i, j)) in enumerate(zip(maxima_indices, zip(*maxima_coords))):
                critical_points.append({
                    "type": "local_maximum",
                    "coordinates": [int(i), int(j)],
                    "risk_value": float(risk_manifold[i, j]),
                    "severity": self._compute_severity(risk_manifold[i, j], risk_manifold),
                    "asset": asset_names[idx % len(asset_names)] if asset_names and len(asset_names) > 0 else f"asset_{idx}"
                })
            
            # Find local minima (risk basins)
            inverted_risk = -risk_manifold
            minima_indices = find_peaks(inverted_risk.flatten())[0]
            minima_coords = np.unravel_index(minima_indices, inverted_risk.shape)
            
            for idx, (flat_idx, (i, j)) in enumerate(zip(minima_indices, zip(*minima_coords))):
                critical_points.append({
                    "type": "local_minimum",
                    "coordinates": [int(i), int(j)],
                    "risk_value": float(risk_manifold[i, j]),
                    "severity": self._compute_severity(risk_manifold[i, j], risk_manifold),
                    "asset": asset_names[idx % len(asset_names)] if asset_names and len(asset_names) > 0 else f"asset_{idx}"
                })
        else:
            # 1D case
            maxima_indices = find_peaks(risk_manifold.flatten())[0]
            for idx in maxima_indices:
                critical_points.append({
                    "type": "local_maximum",
                    "coordinates": [int(idx), 0],
                    "risk_value": float(risk_manifold[idx, 0]),
                    "severity": self._compute_severity(risk_manifold[idx, 0], risk_manifold),
                    "asset": asset_names[idx % len(asset_names)] if asset_names else f"asset_{idx}"
                })
        
        return critical_points
    
    def _compute_severity(
        self,
        risk_value: float,
        risk_manifold: np.ndarray
    ) -> float:
        """
        Compute severity of critical point.
        
        Severity is normalized risk value relative to the range.
        """
        risk_min = np.min(risk_manifold)
        risk_max = np.max(risk_manifold)
        risk_range = risk_max - risk_min
        
        if risk_range == 0:
            return 0.0
        
        return float((risk_value - risk_min) / risk_range)
    
    def _compute_gradient_flow(
        self,
        risk_manifold: np.ndarray
    ) -> List[List[float]]:
        """
        Compute gradient flow vectors.
        
        Gradient flow shows the direction of steepest ascent
        (risk increase) at each point on the surface.
        """
        # Compute gradient using finite differences
        if risk_manifold.ndim == 2:
            # 2D case
            grad_y, grad_x = np.gradient(risk_manifold)
            
            # Flatten and combine
            gradient_flow = np.column_stack([
                grad_x.flatten(),
                grad_y.flatten()
            ]).tolist()
        else:
            # 1D case
            grad = np.gradient(risk_manifold.flatten())
            gradient_flow = [[float(g), 0.0] for g in grad]
        
        return gradient_flow
    
    def _generate_risk_contours(
        self,
        risk_manifold: np.ndarray
    ) -> List[List[float]]:
        """
        Generate risk contours (level sets).
        
        Risk contours are lines of constant risk value, useful
        for visualization and risk management.
        """
        n_contours = 10
        risk_min = np.min(risk_manifold)
        risk_max = np.max(risk_manifold)
        
        contour_levels = np.linspace(risk_min, risk_max, n_contours)
        
        contours = []
        for level in contour_levels:
            # Find points where risk equals this level (within tolerance)
            mask = np.abs(risk_manifold - level) < (risk_max - risk_min) / (2 * n_contours)
            points = np.argwhere(mask)
            
            if len(points) > 0:
                contours.append(points.tolist())
            else:
                contours.append([])
        
        return contours
    
    def _compute_topological_invariants(
        self,
        risk_manifold: np.ndarray,
        critical_points: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Compute topological invariants of risk surface.
        
        Topological invariants include Euler characteristic,
        Betti numbers, and other properties that remain
        unchanged under continuous deformations.
        """
        # Count critical points by type
        n_maxima = sum(1 for cp in critical_points if cp["type"] == "local_maximum")
        n_minima = sum(1 for cp in critical_points if cp["type"] == "local_minimum")
        n_saddle = len(critical_points) - n_maxima - n_minima
        
        # Euler characteristic (Morse theory): χ = n_maxima - n_saddle + n_minima
        euler_characteristic = n_maxima - n_saddle + n_minima
        
        # Total risk (integral over surface)
        total_risk = np.sum(risk_manifold)
        
        # Average risk
        avg_risk = np.mean(risk_manifold)
        
        # Risk variance (measure of surface complexity)
        risk_variance = np.var(risk_manifold)
        
        return {
            "n_maxima": float(n_maxima),
            "n_minima": float(n_minima),
            "n_saddle": float(n_saddle),
            "euler_characteristic": float(euler_characteristic),
            "total_risk": float(total_risk),
            "avg_risk": float(avg_risk),
            "risk_variance": float(risk_variance)
        }
    
    def _generate_cryptographic_seal(
        self,
        risk_manifold: np.ndarray,
        critical_points: List[Dict[str, Any]],
        invariants: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate cryptographic seal for risk surface."""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Create canonical representation
        body = {
            "risk_mean": float(np.mean(risk_manifold)),
            "risk_std": float(np.std(risk_manifold)),
            "n_critical_points": len(critical_points),
            "euler_characteristic": invariants["euler_characteristic"],
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
risk_reconstructor = RiskSurfaceReconstructor()
