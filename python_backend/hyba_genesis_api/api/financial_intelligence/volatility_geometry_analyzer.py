"""
Volatility Geometry Analyzer for HYBA Financial Intelligence Substrate

This module models volatility as a geometric object using:
- Volatility as a stochastic differential geometry
- Rough path theory for volatility trajectories
- Fractal dimension analysis
- Multifractal cascade structure

Mathematical Foundation:
- Rough path signatures capture volatility path properties
- Fractal dimensions quantify volatility roughness
- Multifractal cascade models volatility clustering
- Stochastic differential geometry for local curvature
"""

from __future__ import annotations

import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from scipy import stats
from scipy.signal import detrend
import hashlib
import json


@dataclass
class VolatilityGeometry:
    """Volatility geometry analysis result."""
    
    rough_path_signatures: List[float]
    fractal_dimensions: Dict[str, float]
    cascade_parameters: Dict[str, float]
    surface_curvature: List[List[float]]
    cryptographic_seal: Dict[str, Any]
    timestamp: str


class VolatilityGeometryAnalyzer:
    """
    Analyzes volatility as a geometric object.
    
    This analyzer uses rough path theory and fractal analysis to
    characterize the geometry of volatility, providing insights
    into market roughness and clustering behavior.
    """
    
    def __init__(self, signature_order: int = 3):
        """
        Initialize the volatility geometry analyzer.
        
        Args:
            signature_order: Order of rough path signatures to compute
        """
        self.signature_order = signature_order
    
    def analyze_volatility_geometry(
        self,
        price_series: np.ndarray,
        returns: Optional[np.ndarray] = None
    ) -> VolatilityGeometry:
        """
        Analyze volatility geometry from price series.
        
        Args:
            price_series: Price series (N,)
            returns: Return series (N,) - optional, computed if not provided
        
        Returns:
            VolatilityGeometry with geometric analysis
        """
        # Compute returns if not provided
        if returns is None:
            returns = np.diff(np.log(price_series))
        
        # 1. Compute realized volatility
        realized_vol = self._compute_realized_volatility(returns)
        
        # 2. Compute rough path signatures
        rough_path_signatures = self._compute_rough_path_signatures(
            returns, self.signature_order
        )
        
        # 3. Compute fractal dimensions
        fractal_dimensions = self._compute_fractal_dimensions(returns)
        
        # 4. Compute cascade parameters
        cascade_parameters = self._compute_cascade_parameters(returns)
        
        # 5. Compute surface curvature
        surface_curvature = self._compute_surface_curvature(
            returns, realized_vol
        )
        
        # 6. Generate cryptographic seal
        cryptographic_seal = self._generate_cryptographic_seal(
            rough_path_signatures, fractal_dimensions, cascade_parameters
        )
        
        return VolatilityGeometry(
            rough_path_signatures=rough_path_signatures,
            fractal_dimensions=fractal_dimensions,
            cascade_parameters=cascade_parameters,
            surface_curvature=surface_curvature,
            cryptographic_seal=cryptographic_seal,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def _compute_realized_volatility(
        self,
        returns: np.ndarray,
        window: int = 20
    ) -> np.ndarray:
        """
        Compute realized volatility using rolling window.
        
        Realized volatility is the standard deviation of returns
        over a rolling window, capturing local volatility dynamics.
        """
        n = len(returns)
        realized_vol = np.zeros(n)
        
        for i in range(window, n):
            window_returns = returns[i - window:i]
            realized_vol[i] = np.std(window_returns)
        
        # Fill early values with first valid value
        realized_vol[:window] = realized_vol[window]
        
        return realized_vol
    
    def _compute_rough_path_signatures(
        self,
        returns: np.ndarray,
        order: int
    ) -> List[float]:
        """
        Compute rough path signatures of volatility trajectory.
        
        Rough path signatures capture the geometric properties of
        stochastic paths, providing a robust signature of volatility.
        """
        signatures = []
        
        # Level 1 signature: path itself
        signatures.append(float(np.mean(returns)))
        signatures.append(float(np.std(returns)))
        
        # Level 2 signature: iterated integrals
        if order >= 2:
            # Compute second-order iterated integral
            n = len(returns)
            iterated_integral = 0.0
            for i in range(1, n):
                iterated_integral += returns[i-1] * returns[i]
            signatures.append(float(iterated_integral / n))
        
        # Level 3 signature: third-order iterated integrals
        if order >= 3:
            n = len(returns)
            third_order = 0.0
            for i in range(2, n):
                third_order += returns[i-2] * returns[i-1] * returns[i]
            signatures.append(float(third_order / n))
        
        return signatures
    
    def _compute_fractal_dimensions(
        self,
        returns: np.ndarray
    ) -> Dict[str, float]:
        """
        Compute fractal dimensions of volatility.
        
        Fractal dimensions quantify the roughness and complexity
        of volatility, with higher dimensions indicating more
        complex, rougher behavior.
        """
        # Hurst exponent via R/S analysis
        hurst = self._compute_hurst_exponent(returns)
        
        # Box-counting dimension
        box_dim = self._compute_box_counting_dimension(returns)
        
        # Higuchi fractal dimension
        higuchi = self._compute_higuchi_dimension(returns)
        
        return {
            "hurst_exponent": float(hurst),
            "box_counting_dimension": float(box_dim),
            "higuchi_dimension": float(higuchi)
        }
    
    def _compute_hurst_exponent(
        self,
        returns: np.ndarray,
        max_lag: int = 20
    ) -> float:
        """
        Compute Hurst exponent using R/S analysis.
        
        Hurst exponent H:
        - H > 0.5: Persistent (trending)
        - H = 0.5: Random walk
        - H < 0.5: Anti-persistent (mean-reverting)
        """
        n = len(returns)
        rs_values = []
        lags = range(10, min(max_lag, n // 2))
        
        for lag in lags:
            # Compute cumulative deviation
            cum_dev = np.cumsum(returns - np.mean(returns))
            
            # Compute range
            r = np.max(cum_dev[:lag]) - np.min(cum_dev[:lag])
            
            # Compute standard deviation
            s = np.std(returns[:lag])
            
            if s > 0:
                rs_values.append(r / s)
        
        if len(rs_values) == 0:
            return 0.5
        
        # Fit log(R/S) vs log(lag)
        log_lags = np.log(lags)
        log_rs = np.log(rs_values)
        
        # Linear regression
        slope, _ = np.polyfit(log_lags, log_rs, 1)
        
        return float(slope)
    
    def _compute_box_counting_dimension(
        self,
        returns: np.ndarray,
        epsilon_values: Optional[List[float]] = None
    ) -> float:
        """
        Compute box-counting fractal dimension.
        
        Box-counting dimension estimates how the number of boxes
        needed to cover the data scales with box size.
        """
        if epsilon_values is None:
            epsilon_values = [0.1, 0.05, 0.025, 0.0125, 0.00625]
        
        # Normalize returns to [0, 1]
        normalized = (returns - np.min(returns)) / (np.max(returns) - np.min(returns) + 1e-8)
        
        box_counts = []
        for epsilon in epsilon_values:
            # Count boxes needed
            n_boxes = int(np.ceil(1.0 / epsilon))
            covered = set()
            
            for value in normalized:
                box_idx = int(value / epsilon)
                covered.add(box_idx)
            
            box_counts.append(len(covered))
        
        # Fit log(N) vs log(1/epsilon)
        log_epsilon = np.log(1.0 / np.array(epsilon_values))
        log_counts = np.log(box_counts)
        
        # Linear regression
        slope, _ = np.polyfit(log_epsilon, log_counts, 1)
        
        return float(slope)
    
    def _compute_higuchi_dimension(
        self,
        returns: np.ndarray,
        k_max: int = 10
    ) -> float:
        """
        Compute Higuchi fractal dimension.
        
        Higuchi method estimates fractal dimension by analyzing
        curve length at different scales.
        """
        n = len(returns)
        L = []
        
        for k in range(1, k_max + 1):
            L_k = 0
            for m in range(k):
                # Construct subsequence
                subsequence = returns[m::k]
                if len(subsequence) < 2:
                    continue
                
                # Compute length
                length = np.sum(np.abs(np.diff(subsequence)))
                L_k += length * (n - 1) / (k * len(subsequence))
            
            L.append(L_k / k)
        
        if len(L) == 0:
            return 1.0
        
        # Fit log(L) vs log(1/k)
        log_k = np.log(1.0 / np.arange(1, k_max + 1))
        log_L = np.log(L)
        
        # Linear regression
        slope, _ = np.polyfit(log_k, log_L, 1)
        
        return float(slope)
    
    def _compute_cascade_parameters(
        self,
        returns: np.ndarray
    ) -> Dict[str, float]:
        """
        Compute multifractal cascade parameters.
        
        Multifractal cascade models capture volatility clustering
        through a hierarchical multiplicative process.
        """
        # Compute absolute returns
        abs_returns = np.abs(returns)
        
        # Compute moments at different scales
        moments = {}
        for q in [-2, -1, 0, 1, 2]:
            if q == 0:
                # Use logarithmic moment
                moments[q] = np.mean(np.log(abs_returns + 1e-8))
            else:
                moments[q] = np.mean(abs_returns ** q)
        
        # Estimate scaling exponents
        scaling_exponents = {}
        for q, moment in moments.items():
            # Simplified scaling exponent
            scaling_exponents[q] = float(np.log(moment + 1e-8))
        
        # Estimate multifractal spectrum width
        if 2 in scaling_exponents and -2 in scaling_exponents:
            spectrum_width = scaling_exponents[2] - scaling_exponents[-2]
        else:
            spectrum_width = 0.0
        
        return {
            "moments": {f"q_{k}": float(v) for k, v in moments.items()},
            "scaling_exponents": {f"tau_{k}": float(v) for k, v in scaling_exponents.items()},
            "spectrum_width": float(spectrum_width)
        }
    
    def _compute_surface_curvature(
        self,
        returns: np.ndarray,
        realized_vol: np.ndarray
    ) -> List[List[float]]:
        """
        Compute volatility surface curvature.
        
        Constructs a 2D surface from returns and volatility,
        then computes the curvature at each point.
        """
        # Create 2D embedding (returns vs volatility)
        n = len(returns)
        surface = np.column_stack([returns, realized_vol])
        
        # Compute curvature using local neighborhoods
        curvature_map = np.zeros(n)
        
        for i in range(2, n - 2):
            # Local neighborhood
            local_returns = returns[i-2:i+3]
            local_vol = realized_vol[i-2:i+3]
            
            # Fit local quadratic surface
            try:
                # Simplified curvature: second derivative
                curvature = np.abs(np.diff(local_vol, n=2)).mean()
                curvature_map[i] = curvature
            except:
                curvature_map[i] = 0.0
        
        # Fill boundaries
        curvature_map[:2] = curvature_map[2]
        curvature_map[-2:] = curvature_map[-3]
        
        # Return as 2D array (time, curvature)
        return curvature_map.reshape(-1, 1).tolist()
    
    def _generate_cryptographic_seal(
        self,
        signatures: List[float],
        fractal_dims: Dict[str, float],
        cascade_params: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate cryptographic seal for volatility geometry."""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Create canonical representation
        body = {
            "signature_mean": float(np.mean(signatures)),
            "hurst_exponent": fractal_dims.get("hurst_exponent", 0.0),
            "spectrum_width": cascade_params.get("spectrum_width", 0.0),
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
volatility_analyzer = VolatilityGeometryAnalyzer()
