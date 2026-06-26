"""
Financial Intelligence API Router for HYBA

This module provides FastAPI endpoints for the Financial Intelligence Substrate,
exposing all three layers:
- Layer A: Core (regime-shift, liquidity, causal, volatility, alpha, risk)
- Layer B: Autonomic (drift, manifold, anomaly, repair, entropy, rewiring)
- Layer C: Sovereign (kernel reasoning, stress test, systemic risk)
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import numpy as np

# Import core layer modules
from .regime_shift_detector import regime_detector, RegimeShiftReport
from .liquidity_topology_mapper import liquidity_mapper, LiquidityTopology, OrderBook
from .causal_inference_engine import causal_engine, CausalGraph
from .volatility_geometry_analyzer import volatility_analyzer, VolatilityGeometry
from .alpha_mining_engine import alpha_miner, AlphaSignals
from .risk_surface_reconstructor import risk_reconstructor, RiskSurface

# Import autonomic layer modules
from .autonomic.drift_detector import drift_detector, DriftReport
from .autonomic.manifold_integrity_checker import manifold_checker, IntegrityReport
from .autonomic.curvature_anomaly_detector import curvature_detector, AnomalyReport
from .autonomic.factor_model_self_repair import factor_repair, RepairReport
from .autonomic.entropy_optimizer import entropy_optimizer, OptimizationReport
from .autonomic.topology_aware_rewiring import topology_rewiring, RewiringReport

# Import sovereign layer modules
from .sovereign.kernel_reasoning_verifier import kernel_verifier, VerificationReport
from .sovereign.stress_test_harness import stress_test_harness, StressTestReport
from .sovereign.systemic_risk_mapper import systemic_risk_mapper, SystemicRiskMap

router = APIRouter(prefix="/api/financial", tags=["financial-intelligence"])


# ============================================================================
# LAYER A: CORE ENDPOINTS
# ============================================================================

@router.post("/regime-shift/detect")
async def detect_regime_shift(
    prices: List[float],
    volumes: Optional[List[float]] = None,
    returns: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Detect regime shift in market data.
    
    Args:
        prices: Price series
        volumes: Optional volume series
        returns: Optional return series
    
    Returns:
        RegimeShiftReport with detected regime and evidence
    """
    prices_array = np.array(prices)
    volumes_array = np.array(volumes) if volumes else None
    returns_array = np.array(returns) if returns else None
    
    result = regime_detector.detect_regime_shift(
        prices_array, volumes_array, returns_array
    )
    
    return {
        "regime": result.regime,
        "confidence": result.confidence,
        "topological_evidence": result.topological_evidence,
        "transition_matrix": result.transition_matrix,
        "phi_density_windows": result.phi_density_windows,
        "betti_numbers": result.betti_numbers,
        "cryptographic_seal": result.cryptographic_seal,
        "timestamp": result.timestamp
    }


@router.post("/liquidity/map")
async def map_liquidity_topology(
    asks: List[List[float]],
    bids: List[List[float]],
    timestamp: str
) -> Dict[str, Any]:
    """
    Map liquidity surface from order book.
    
    Args:
        asks: List of (price, quantity) for asks
        bids: List of (price, quantity) for bids
        timestamp: Order book timestamp
    
    Returns:
        LiquidityTopology with curvature, basins, and paths
    """
    order_book = OrderBook(
        asks=[(a[0], a[1]) for a in asks],
        bids=[(b[0], b[1]) for b in bids],
        timestamp=timestamp
    )
    
    result = liquidity_mapper.map_liquidity_surface(order_book)
    
    return {
        "curvature_map": result.curvature_map,
        "liquidity_basins": result.liquidity_basins,
        "geodesic_paths": result.geodesic_paths,
        "shock_vectors": result.shock_vectors,
        "topological_invariants": result.topological_invariants,
        "cryptographic_seal": result.cryptographic_seal,
        "timestamp": result.timestamp
    }


@router.post("/causal/discover")
async def discover_causal_structure(
    data: Dict[str, List[float]],
    method: str = "pc"
) -> Dict[str, Any]:
    """
    Discover causal structure from observational data.
    
    Args:
        data: Dictionary of variable names to time series
        method: Causal discovery method ("pc", "fci", "ges")
    
    Returns:
        CausalGraph with discovered structure and counterfactuals
    """
    data_arrays = {k: np.array(v) for k, v in data.items()}
    
    result = causal_engine.discover_causal_structure(data_arrays, method)
    
    return {
        "nodes": result.nodes,
        "edges": result.edges,
        "edge_weights": result.edge_weights,
        "counterfactuals": result.counterfactuals,
        "topological_order": result.topological_order,
        "cryptographic_seal": result.cryptographic_seal,
        "timestamp": result.timestamp
    }


@router.post("/volatility/analyze")
async def analyze_volatility_geometry(
    price_series: List[float],
    returns: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Analyze volatility geometry from price series.
    
    Args:
        price_series: Price series
        returns: Optional return series
    
    Returns:
        VolatilityGeometry with geometric analysis
    """
    price_array = np.array(price_series)
    returns_array = np.array(returns) if returns else None
    
    result = volatility_analyzer.analyze_volatility_geometry(price_array, returns_array)
    
    return {
        "rough_path_signatures": result.rough_path_signatures,
        "fractal_dimensions": result.fractal_dimensions,
        "cascade_parameters": result.cascade_parameters,
        "surface_curvature": result.surface_curvature,
        "cryptographic_seal": result.cryptographic_seal,
        "timestamp": result.timestamp
    }


@router.post("/alpha/mine")
async def mine_alpha_signals(
    market_data: Dict[str, List[float]],
    returns: List[float],
    n_signals: int = 5
) -> Dict[str, Any]:
    """
    Mine alpha signals from market data.
    
    Args:
        market_data: Dictionary of feature names to time series
        returns: Target return series
        n_signals: Number of signals to discover
    
    Returns:
        AlphaSignals with discovered signals and combination weights
    """
    market_data_arrays = {k: np.array(v) for k, v in market_data.items()}
    returns_array = np.array(returns)
    
    result = alpha_miner.mine_alpha_signals(market_data_arrays, returns_array, n_signals)
    
    return {
        "signals": result.signals,
        "information_content": result.information_content,
        "predictive_power": result.predictive_power,
        "combination_weights": result.combination_weights,
        "cryptographic_seal": result.cryptographic_seal,
        "timestamp": result.timestamp
    }


@router.post("/risk/reconstruct")
async def reconstruct_risk_surface(
    portfolio_returns: List[List[float]],
    asset_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Reconstruct risk surface from portfolio returns.
    
    Args:
        portfolio_returns: Portfolio returns (N_assets, N_timepoints)
        asset_names: Optional list of asset names
    
    Returns:
        RiskSurface with manifold, critical points, and contours
    """
    portfolio_array = np.array(portfolio_returns)
    
    result = risk_reconstructor.reconstruct_risk_surface(portfolio_array, asset_names)
    
    return {
        "risk_manifold": result.risk_manifold,
        "critical_points": result.critical_points,
        "gradient_flow": result.gradient_flow,
        "risk_contours": result.risk_contours,
        "topological_invariants": result.topological_invariants,
        "cryptographic_seal": result.cryptographic_seal,
        "timestamp": result.timestamp
    }


# ============================================================================
# LAYER B: AUTONOMIC ENDPOINTS
# ============================================================================

@router.post("/autonomic/drift/detect")
async def detect_drift(
    model_name: str,
    baseline_data: List[float],
    new_data: List[float],
    model_components: Optional[List[str]] = None
) -> Dict[str, Any]:
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
    baseline_array = np.array(baseline_data)
    new_array = np.array(new_data)
    
    result = drift_detector.detect_drift(model_name, baseline_array, new_array, model_components)
    
    return {
        "drift_detected": result.drift_detected,
        "drift_magnitude": result.drift_magnitude,
        "affected_components": result.affected_components,
        "recommended_actions": result.recommended_actions,
        "phi_density_shift": result.phi_density_shift,
        "kl_divergence": result.kl_divergence,
        "wasserstein_distance": result.wasserstein_distance,
        "cryptographic_seal": result.cryptographic_seal,
        "timestamp": result.timestamp
    }


@router.post("/autonomic/manifold/check")
async def check_manifold_integrity(
    manifold_data: List[List[float]],
    historical_baseline: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """
    Check integrity of latent manifold.
    
    Args:
        manifold_data: Manifold data (N_samples, N_features)
        historical_baseline: Optional historical Betti numbers for comparison
    
    Returns:
        IntegrityReport with topological analysis and recommendations
    """
    manifold_array = np.array(manifold_data)
    
    result = manifold_checker.check_integrity(manifold_array, historical_baseline)
    
    return {
        "betti_numbers": result.betti_numbers,
        "topological_breaks_detected": result.topological_breaks_detected,
        "manifold_health_score": result.manifold_health_score,
        "recommended_repairs": result.recommended_repairs,
        "topological_invariants": result.topological_invariants,
        "cryptographic_seal": result.cryptographic_seal,
        "timestamp": result.timestamp
    }


@router.post("/autonomic/anomaly/detect")
async def detect_anomalies(
    data: List[List[float]],
    returns: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Detect anomalies through curvature analysis.
    
    Args:
        data: Data manifold (N_samples, N_features)
        returns: Optional return series for context
    
    Returns:
        AnomalyReport with detected anomalies and context
    """
    data_array = np.array(data)
    returns_array = np.array(returns) if returns else None
    
    result = curvature_detector.detect_anomalies(data_array, returns_array)
    
    return {
        "anomaly_locations": result.anomaly_locations,
        "curvature_values": result.curvature_values,
        "anomaly_severity_scores": result.anomaly_severity_scores,
        "topological_context": result.topological_context,
        "cryptographic_seal": result.cryptographic_seal,
        "timestamp": result.timestamp
    }


@router.post("/autonomic/repair/factor")
async def repair_factor_model(
    model: Dict[str, Any],
    new_data: List[List[float]],
    returns: List[float]
) -> Dict[str, Any]:
    """
    Repair degraded factor model.
    
    Args:
        model: Factor model with loadings and factors
        new_data: New feature data
        returns: Target returns
    
    Returns:
        RepairReport with repaired factors and performance
    """
    new_data_array = np.array(new_data)
    returns_array = np.array(returns)
    
    result = factor_repair.repair_model(model, new_data_array, returns_array)
    
    return {
        "repaired_factors": result.repaired_factors,
        "repair_confidence": result.repair_confidence,
        "performance_improvement": result.performance_improvement,
        "salamander_proposals": result.salamander_proposals,
        "cryptographic_seal": result.cryptographic_seal,
        "timestamp": result.timestamp
    }


@router.post("/autonomic/optimize/entropy")
async def optimize_entropy(
    system: Dict[str, Any],
    performance_data: List[float],
    parameter_bounds: Optional[Dict[str, List[float]]] = None
) -> Dict[str, Any]:
    """
    Optimise system parameters to minimize entropy production.
    
    Args:
        system: System with parameters to optimize
        performance_data: Performance metrics for evaluation
        parameter_bounds: Optional bounds for parameters
    
    Returns:
        OptimizationReport with optimized parameters and metrics
    """
    performance_array = np.array(performance_data)
    
    result = entropy_optimizer.optimize_parameters(system, performance_array, parameter_bounds)
    
    return {
        "optimized_parameters": result.optimized_parameters,
        "entropy_reduction": result.entropy_reduction,
        "performance_improvement": result.performance_improvement,
        "stability_metrics": result.stability_metrics,
        "cryptographic_seal": result.cryptographic_seal,
        "timestamp": result.timestamp
    }


@router.post("/autonomic/rewire/topology")
async def rewire_topology(
    system: Dict[str, Any],
    performance_data: List[float]
) -> Dict[str, Any]:
    """
    Rewire system based on topological analysis.
    
    Args:
        system: System with connection topology
        performance_data: Performance metrics for evaluation
    
    Returns:
        RewiringReport with new topology and approval status
    """
    performance_array = np.array(performance_data)
    
    result = topology_rewiring.rewire_system(system, performance_array)
    
    return {
        "new_topology": result.new_topology,
        "rewiring_confidence": result.rewiring_confidence,
        "performance_impact": result.performance_impact,
        "governance_approval_status": result.governance_approval_status,
        "cryptographic_seal": result.cryptographic_seal,
        "timestamp": result.timestamp
    }


# ============================================================================
# LAYER C: SOVEREIGN ENDPOINTS
# ============================================================================

@router.post("/sovereign/verify/reasoning")
async def verify_reasoning(
    reasoning_chain: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Verify reasoning chain using kernel methods.
    
    Args:
        reasoning_chain: List of reasoning steps
        context: Optional context for verification
    
    Returns:
        VerificationReport with validity and metrics
    """
    result = kernel_verifier.verify_reasoning(reasoning_chain, context)
    
    return {
        "reasoning_validity": result.reasoning_validity,
        "kernel_similarity_scores": result.kernel_similarity_scores,
        "logical_consistency_metrics": result.logical_consistency_metrics,
        "verification_confidence": result.verification_confidence,
        "cryptographic_seal": result.cryptographic_seal,
        "timestamp": result.timestamp
    }


@router.post("/sovereign/stress-test")
async def run_stress_tests(
    portfolio_returns: List[List[float]],
    portfolio_weights: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Run comprehensive stress tests on portfolio.
    
    Args:
        portfolio_returns: Portfolio returns (N_assets, N_timepoints)
        portfolio_weights: Optional portfolio weights
    
    Returns:
        StressTestReport with scenario results and risk metrics
    """
    portfolio_array = np.array(portfolio_returns)
    weights_array = np.array(portfolio_weights) if portfolio_weights else None
    
    result = stress_test_harness.run_stress_tests(portfolio_array, weights_array)
    
    return {
        "stress_scenario_results": result.stress_scenario_results,
        "tail_event_probabilities": result.tail_event_probabilities,
        "var_estimates": result.var_estimates,
        "cvar_estimates": result.cvar_estimates,
        "topological_resilience_metrics": result.topological_resilience_metrics,
        "cryptographic_seal": result.cryptographic_seal,
        "timestamp": result.timestamp
    }


@router.post("/sovereign/systemic-risk/map")
async def map_systemic_risk(
    financial_system: Dict[str, Any],
    exposure_matrix: Optional[List[List[float]]] = None
) -> Dict[str, Any]:
    """
    Map systemic risk topology of financial system.
    
    Args:
        financial_system: Dictionary of financial entities and connections
        exposure_matrix: Optional exposure matrix between entities
    
    Returns:
        SystemicRiskMap with network topology and risk analysis
    """
    exposure_array = np.array(exposure_matrix) if exposure_matrix else None
    
    result = systemic_risk_mapper.map_systemic_risk(financial_system, exposure_array)
    
    return {
        "financial_network": result.financial_network,
        "centrality_rankings": result.centrality_rankings,
        "contagion_pathways": result.contagion_pathways,
        "systemic_risk_hotspots": result.systemic_risk_hotspots,
        "cryptographic_seal": result.cryptographic_seal,
        "timestamp": result.timestamp
    }


# ============================================================================
# HEALTH ENDPOINT
# ============================================================================

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for financial intelligence service."""
    return {
        "status": "healthy",
        "service": "financial-intelligence",
        "layers": {
            "core": "operational",
            "autonomic": "operational",
            "sovereign": "operational"
        }
    }
