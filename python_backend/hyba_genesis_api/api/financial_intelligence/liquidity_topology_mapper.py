"""
Liquidity Topology Mapping Module for HYBA Financial Intelligence Substrate

This module models liquidity as a dynamic topological surface using:
- Liquidity as a Riemannian manifold
- Curvature analysis for liquidity shocks
- Geodesic distance for liquidity path planning
- Morse theory for liquidity basin identification

Mathematical Foundation:
- Liquidity surface constructed from order book depth
- Gaussian curvature identifies liquidity concentration
- Geodesic paths optimize execution routing
- Critical points (local minima/maxima) identify liquidity basins
"""

from __future__ import annotations

import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from scipy.spatial import distance_matrix
from scipy.interpolate import griddata
import hashlib
import json


@dataclass
class OrderBook:
    """Order book data structure."""
    asks: List[Tuple[float, float]]  # (price, quantity)
    bids: List[Tuple[float, float]]  # (price, quantity)
    timestamp: str


@dataclass
class LiquidityTopology:
    """Liquidity topology mapping result."""
    
    curvature_map: List[List[float]]
    liquidity_basins: List[Dict[str, Any]]
    geodesic_paths: List[List[float]]
    shock_vectors: List[List[float]]
    topological_invariants: Dict[str, float]
    cryptographic_seal: Dict[str, Any]
    timestamp: str


class LiquidityTopologyMapper:
    """
    Maps liquidity as a topological surface for execution optimization.
    
    This mapper constructs a liquidity manifold from order book data,
    analyzes its curvature to identify liquidity concentrations and shocks,
    and computes geodesic paths for optimal execution routing.
    """
    
    def __init__(self, grid_resolution: int = 50):
        """
        Initialize the liquidity topology mapper.
        
        Args:
            grid_resolution: Resolution of the liquidity surface grid
        """
        self.grid_resolution = grid_resolution
    
    def map_liquidity_surface(
        self,
        order_book: OrderBook,
        price_range: Optional[Tuple[float, float]] = None
    ) -> LiquidityTopology:
        """
        Map liquidity surface from order book.
        
        Args:
            order_book: Order book with asks and bids
            price_range: Optional price range for mapping (min, max)
        
        Returns:
            LiquidityTopology with curvature, basins, and paths
        """
        # 1. Construct liquidity surface from order book
        price_grid, liquidity_surface = self._construct_liquidity_surface(
            order_book, price_range
        )
        
        # 2. Compute Gaussian curvature
        curvature_map = self._compute_gaussian_curvature(
            price_grid, liquidity_surface
        )
        
        # 3. Identify liquidity basins (critical points)
        liquidity_basins = self._identify_liquidity_basins(
            price_grid, liquidity_surface, curvature_map
        )
        
        # 4. Compute geodesic execution paths
        geodesic_paths = self._compute_geodesic_paths(
            price_grid, liquidity_surface
        )
        
        # 5. Compute shock propagation vectors
        shock_vectors = self._compute_shock_vectors(
            price_grid, liquidity_surface, curvature_map
        )
        
        # 6. Compute topological invariants
        topological_invariants = self._compute_topological_invariants(
            curvature_map, liquidity_basins
        )
        
        # 7. Generate cryptographic seal
        cryptographic_seal = self._generate_cryptographic_seal(
            curvature_map, liquidity_basins, topological_invariants
        )
        
        return LiquidityTopology(
            curvature_map=curvature_map.tolist(),
            liquidity_basins=liquidity_basins,
            geodesic_paths=geodesic_paths,
            shock_vectors=shock_vectors,
            topological_invariants=topological_invariants,
            cryptographic_seal=cryptographic_seal,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def _construct_liquidity_surface(
        self,
        order_book: OrderBook,
        price_range: Optional[Tuple[float, float]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Construct liquidity surface from order book.
        
        The liquidity surface represents the cumulative quantity available
        at each price level, creating a 3D surface (price, side, liquidity).
        """
        # Combine asks and bids
        all_orders = order_book.asks + order_book.bids
        prices = np.array([p for p, _ in all_orders])
        quantities = np.array([q for _, q in all_orders])
        
        # Determine price range
        if price_range is None:
            price_min, price_max = np.min(prices), np.max(prices)
        else:
            price_min, price_max = price_range
        
        # Create price grid
        price_grid = np.linspace(price_min, price_max, self.grid_resolution)
        
        # Interpolate liquidity surface
        # Cumulative quantity at each price level
        cumulative_liquidity = np.zeros(self.grid_resolution)
        for i, price in enumerate(price_grid):
            # Sum quantities at or near this price
            mask = np.abs(prices - price) < (price_max - price_min) / self.grid_resolution
            cumulative_liquidity[i] = np.sum(quantities[mask])
        
        # Smooth the surface
        liquidity_surface = np.convolve(
            cumulative_liquidity,
            np.ones(5) / 5,
            mode='same'
        )
        
        return price_grid, liquidity_surface
    
    def _compute_gaussian_curvature(
        self,
        price_grid: np.ndarray,
        liquidity_surface: np.ndarray
    ) -> np.ndarray:
        """
        Compute Gaussian curvature of liquidity surface.
        
        Gaussian curvature K = (f_xx * f_yy - f_xy^2) / (1 + f_x^2 + f_y^2)^2
        For 1D surface, simplifies to curvature of the curve.
        """
        # Compute first and second derivatives
        f_prime = np.gradient(liquidity_surface, price_grid)
        f_double_prime = np.gradient(f_prime, price_grid)
        
        # Curvature for 1D curve: k = f'' / (1 + f'^2)^(3/2)
        curvature = f_double_prime / (1 + f_prime**2)**(1.5)
        
        return curvature
    
    def _identify_liquidity_basins(
        self,
        price_grid: np.ndarray,
        liquidity_surface: np.ndarray,
        curvature_map: np.ndarray
    ) -> List[Dict[str, Any]]:
        """
        Identify liquidity basins using Morse theory.
        
        Liquidity basins are local minima in the liquidity surface,
        representing areas of high liquidity concentration.
        """
        basins = []
        
        # Find local minima (liquidity basins)
        from scipy.signal import find_peaks
        # Invert to find minima as peaks
        inverted_surface = -liquidity_surface
        minima_indices, _ = find_peaks(inverted_surface)
        
        for idx in minima_indices:
            basin = {
                "price": float(price_grid[idx]),
                "liquidity": float(liquidity_surface[idx]),
                "curvature": float(curvature_map[idx]),
                "depth": self._compute_basin_depth(
                    idx, liquidity_surface, price_grid
                ),
                "type": "local_minimum"
            }
            basins.append(basin)
        
        # Also find local maxima (liquidity voids)
        maxima_indices, _ = find_peaks(liquidity_surface)
        for idx in maxima_indices:
            basin = {
                "price": float(price_grid[idx]),
                "liquidity": float(liquidity_surface[idx]),
                "curvature": float(curvature_map[idx]),
                "depth": 0.0,
                "type": "local_maximum"
            }
            basins.append(basin)
        
        return basins
    
    def _compute_basin_depth(
        self,
        idx: int,
        liquidity_surface: np.ndarray,
        price_grid: np.ndarray
    ) -> float:
        """Compute depth of liquidity basin."""
        # Find nearest local maximum
        from scipy.signal import find_peaks
        maxima_indices, _ = find_peaks(liquidity_surface)
        
        if len(maxima_indices) == 0:
            return 0.0
        
        # Find nearest maximum
        distances = np.abs(maxima_indices - idx)
        nearest_max_idx = maxima_indices[np.argmin(distances)]
        
        # Depth is difference in liquidity
        depth = liquidity_surface[nearest_max_idx] - liquidity_surface[idx]
        return float(depth)
    
    def _compute_geodesic_paths(
        self,
        price_grid: np.ndarray,
        liquidity_surface: np.ndarray
    ) -> List[List[float]]:
        """
        Compute geodesic paths for optimal execution.
        
        Geodesic paths minimize the "cost" of execution, where cost
        is inversely proportional to liquidity.
        """
        # Create cost matrix (inverse of liquidity)
        cost = 1.0 / (liquidity_surface + 1e-8)
        
        # Compute shortest paths using Dijkstra-like approach
        # Simplified for 1D case
        geodesic_paths = []
        
        # Path from start to end
        start_idx = 0
        end_idx = len(price_grid) - 1
        
        # Greedy path following minimum cost
        current_idx = start_idx
        path = [float(price_grid[current_idx])]
        
        while current_idx < end_idx:
            # Look ahead for minimum cost
            lookahead = min(5, end_idx - current_idx)
            candidates = range(current_idx + 1, current_idx + lookahead + 1)
            next_idx = min(candidates, key=lambda i: cost[i])
            
            path.append(float(price_grid[next_idx]))
            current_idx = next_idx
        
        geodesic_paths.append(path)
        
        return geodesic_paths
    
    def _compute_shock_vectors(
        self,
        price_grid: np.ndarray,
        liquidity_surface: np.ndarray,
        curvature_map: np.ndarray
    ) -> List[List[float]]:
        """
        Compute shock propagation vectors.
        
        Shock vectors indicate how liquidity shocks would propagate
        through the market based on the topology of the liquidity surface.
        """
        shock_vectors = []
        
        # Compute gradient of liquidity surface
        gradient = np.gradient(liquidity_surface, price_grid)
        
        # Shock direction is opposite to gradient (flows toward low liquidity)
        for i in range(len(price_grid)):
            # Shock vector at this point
            shock_vector = [
                float(price_grid[i]),
                float(-gradient[i]),  # Opposite to gradient
                float(curvature_map[i])  # Magnitude affected by curvature
            ]
            shock_vectors.append(shock_vector)
        
        return shock_vectors
    
    def _compute_topological_invariants(
        self,
        curvature_map: np.ndarray,
        liquidity_basins: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Compute topological invariants of liquidity surface.
        
        Topological invariants are properties that remain unchanged
        under continuous deformations of the surface.
        """
        # Total curvature (Gauss-Bonnet theorem)
        total_curvature = np.sum(curvature_map)
        
        # Number of critical points (Morse theory)
        n_minima = sum(1 for b in liquidity_basins if b["type"] == "local_minimum")
        n_maxima = sum(1 for b in liquidity_basins if b["type"] == "local_maximum")
        
        # Euler characteristic (for 1D manifold: χ = #vertices - #edges)
        # Simplified as difference between maxima and minima
        euler_characteristic = n_maxima - n_minima
        
        # Average curvature
        avg_curvature = np.mean(np.abs(curvature_map))
        
        # Curvature variance (measure of surface complexity)
        curvature_variance = np.var(curvature_map)
        
        return {
            "total_curvature": float(total_curvature),
            "n_minima": float(n_minima),
            "n_maxima": float(n_maxima),
            "euler_characteristic": float(euler_characteristic),
            "avg_curvature": float(avg_curvature),
            "curvature_variance": float(curvature_variance)
        }
    
    def _generate_cryptographic_seal(
        self,
        curvature_map: np.ndarray,
        liquidity_basins: List[Dict[str, Any]],
        invariants: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate cryptographic seal for liquidity topology."""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Create canonical representation
        body = {
            "curvature_mean": float(np.mean(curvature_map)),
            "curvature_std": float(np.std(curvature_map)),
            "n_basins": len(liquidity_basins),
            "invariants": invariants,
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
liquidity_mapper = LiquidityTopologyMapper()
