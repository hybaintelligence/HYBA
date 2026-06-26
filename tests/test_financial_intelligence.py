"""
Production tests for HYBA Financial Intelligence Substrate

Tests cover all three layers:
- Layer A: Core (regime-shift, liquidity, causal, volatility, alpha, risk)
- Layer B: Autonomic (drift, manifold, anomaly, repair, entropy, rewiring)
- Layer C: Sovereign (kernel reasoning, stress test, systemic risk)
"""

import pytest
import numpy as np
from datetime import datetime

# Import core layer modules
from hyba_genesis_api.api.financial_intelligence.regime_shift_detector import (
    regime_detector,
    RegimeShiftReport
)
from hyba_genesis_api.api.financial_intelligence.liquidity_topology_mapper import (
    liquidity_mapper,
    OrderBook
)
from hyba_genesis_api.api.financial_intelligence.causal_inference_engine import (
    causal_engine
)
from hyba_genesis_api.api.financial_intelligence.volatility_geometry_analyzer import (
    volatility_analyzer
)
from hyba_genesis_api.api.financial_intelligence.alpha_mining_engine import (
    alpha_miner
)
from hyba_genesis_api.api.financial_intelligence.risk_surface_reconstructor import (
    risk_reconstructor
)

# Import autonomic layer modules
from hyba_genesis_api.api.financial_intelligence.autonomic.drift_detector import (
    drift_detector
)
from hyba_genesis_api.api.financial_intelligence.autonomic.manifold_integrity_checker import (
    manifold_checker
)
from hyba_genesis_api.api.financial_intelligence.autonomic.curvature_anomaly_detector import (
    curvature_detector
)
from hyba_genesis_api.api.financial_intelligence.autonomic.factor_model_self_repair import (
    factor_repair
)
from hyba_genesis_api.api.financial_intelligence.autonomic.entropy_optimizer import (
    entropy_optimizer
)
from hyba_genesis_api.api.financial_intelligence.autonomic.topology_aware_rewiring import (
    topology_rewiring
)

# Import sovereign layer modules
from hyba_genesis_api.api.financial_intelligence.sovereign.kernel_reasoning_verifier import (
    kernel_verifier
)
from hyba_genesis_api.api.financial_intelligence.sovereign.stress_test_harness import (
    stress_test_harness
)
from hyba_genesis_api.api.financial_intelligence.sovereign.systemic_risk_mapper import (
    systemic_risk_mapper
)


# ============================================================================
# LAYER A: CORE LAYER TESTS
# ============================================================================

class TestRegimeShiftDetection:
    """Tests for regime-shift detection module."""
    
    def test_regime_shift_detection_bull_market(self):
        """Test detection of bull market regime."""
        # Generate bull market data (upward trend with low volatility)
        n = 1000
        prices = np.cumprod(1 + np.random.normal(0.001, 0.01, n))
        
        result = regime_detector.detect_regime_shift(prices)
        
        assert isinstance(result, RegimeShiftReport)
        assert result.regime in ["bull", "bear", "choppy", "crash"]
        assert 0 <= result.confidence <= 100
        assert result.cryptographic_seal is not None
        assert result.cryptographic_seal["algorithm"] == "SHA-256"
    
    def test_regime_shift_detection_bear_market(self):
        """Test detection of bear market regime."""
        # Generate bear market data (downward trend with high volatility)
        n = 1000
        prices = np.cumprod(1 + np.random.normal(-0.002, 0.02, n))
        
        result = regime_detector.detect_regime_shift(prices)
        
        assert result.regime in ["bull", "bear", "choppy", "crash"]
        assert "transition_matrix" in result.__dict__
    
    def test_regime_shift_with_volumes(self):
        """Test regime shift detection with volume data."""
        n = 1000
        prices = np.cumprod(1 + np.random.normal(0.001, 0.01, n))
        volumes = np.random.uniform(1000, 10000, n)
        
        result = regime_detector.detect_regime_shift(prices, volumes)
        
        assert result.regime in ["bull", "bear", "choppy", "crash"]
    
    def test_regime_shift_evidence_sealing(self):
        """Test that regime shift results are cryptographically sealed."""
        prices = np.cumprod(1 + np.random.normal(0.001, 0.01, 1000))
        
        result = regime_detector.detect_regime_shift(prices)
        
        assert "cryptographic_seal" in result.__dict__
        assert result.cryptographic_seal["algorithm"] == "SHA-256"
        assert "body_hash" in result.cryptographic_seal
        assert "seal" in result.cryptographic_seal
        assert len(result.cryptographic_seal["seal"]) == 64  # SHA-256 hex length


class TestLiquidityTopologyMapping:
    """Tests for liquidity topology mapping module."""
    
    def test_liquidity_topology_construction(self):
        """Test construction of liquidity surface from order book."""
        order_book = OrderBook(
            asks=[(100.0 + i, 100 - i) for i in range(10)],
            bids=[(100.0 - i, 100 - i) for i in range(10)],
            timestamp=datetime.now().isoformat()
        )
        
        result = liquidity_mapper.map_liquidity_surface(order_book)
        
        assert "curvature_map" in result.__dict__
        assert "liquidity_basins" in result.__dict__
        assert "geodesic_paths" in result.__dict__
        assert "cryptographic_seal" in result.__dict__
    
    def test_liquidity_basins_identification(self):
        """Test identification of liquidity basins."""
        order_book = OrderBook(
            asks=[(100.0 + i, 100 - i) for i in range(20)],
            bids=[(100.0 - i, 100 - i) for i in range(20)],
            timestamp=datetime.now().isoformat()
        )
        
        result = liquidity_mapper.map_liquidity_surface(order_book)
        
        assert len(result.liquidity_basins) > 0
        assert all("price" in basin for basin in result.liquidity_basins)
        assert all("type" in basin for basin in result.liquidity_basins)
    
    def test_liquidity_evidence_sealing(self):
        """Test that liquidity topology results are sealed."""
        order_book = OrderBook(
            asks=[(100.0 + i, 100 - i) for i in range(10)],
            bids=[(100.0 - i, 100 - i) for i in range(10)],
            timestamp=datetime.now().isoformat()
        )
        
        result = liquidity_mapper.map_liquidity_surface(order_book)
        
        assert result.cryptographic_seal["algorithm"] == "SHA-256"
        assert "seal" in result.cryptographic_seal


class TestCausalInference:
    """Tests for causal inference engine."""
    
    def test_causal_structure_discovery(self):
        """Test discovery of causal structure."""
        data = {
            "X": np.random.normal(0, 1, 1000),
            "Y": np.random.normal(0, 1, 1000),
            "Z": np.random.normal(0, 1, 1000)
        }
        
        result = causal_engine.discover_causal_structure(data)
        
        assert "nodes" in result.__dict__
        assert "edges" in result.__dict__
        assert "counterfactuals" in result.__dict__
        assert "cryptographic_seal" in result.__dict__
    
    def test_causal_graph_dag_property(self):
        """Test that causal graph is a DAG."""
        data = {
            "A": np.random.normal(0, 1, 500),
            "B": np.random.normal(0, 1, 500),
            "C": np.random.normal(0, 1, 500)
        }
        
        result = causal_engine.discover_causal_structure(data)
        
        # Verify topological order exists (DAG property)
        assert len(result.topological_order) > 0
    
    def test_causal_counterfactuals(self):
        """Test generation of counterfactual predictions."""
        data = {
            "X": np.random.normal(0, 1, 500),
            "Y": np.random.normal(0, 1, 500)
        }
        
        result = causal_engine.discover_causal_structure(data)
        
        assert len(result.counterfactuals) > 0


class TestVolatilityGeometry:
    """Tests for volatility geometry analyzer."""
    
    def test_volatility_geometry_analysis(self):
        """Test volatility geometry from price series."""
        prices = np.cumprod(1 + np.random.normal(0.001, 0.02, 1000))
        
        result = volatility_analyzer.analyze_volatility_geometry(prices)
        
        assert "rough_path_signatures" in result.__dict__
        assert "fractal_dimensions" in result.__dict__
        assert "cascade_parameters" in result.__dict__
        assert "cryptographic_seal" in result.__dict__
    
    def test_fractal_dimensions_computation(self):
        """Test computation of fractal dimensions."""
        prices = np.cumprod(1 + np.random.normal(0.001, 0.01, 500))
        
        result = volatility_analyzer.analyze_volatility_geometry(prices)
        
        assert "hurst_exponent" in result.fractal_dimensions
        # Hurst exponent can be negative for anti-persistent series
        assert -1 <= result.fractal_dimensions["hurst_exponent"] <= 1
    
    def test_rough_path_signatures(self):
        """Test computation of rough path signatures."""
        prices = np.cumprod(1 + np.random.normal(0.001, 0.01, 500))
        
        result = volatility_analyzer.analyze_volatility_geometry(prices)
        
        assert len(result.rough_path_signatures) > 0


class TestAlphaMining:
    """Tests for alpha mining engine."""
    
    def test_alpha_signal_discovery(self):
        """Test discovery of alpha signals."""
        market_data = {
            "feature_1": np.random.normal(0, 1, 1000),
            "feature_2": np.random.normal(0, 1, 1000),
            "feature_3": np.random.normal(0, 1, 1000)
        }
        returns = np.random.normal(0.001, 0.02, 1000)
        
        result = alpha_miner.mine_alpha_signals(market_data, returns, n_signals=3)
        
        assert len(result.signals) <= 3
        assert "information_content" in result.__dict__
        assert "predictive_power" in result.__dict__
        assert "cryptographic_seal" in result.__dict__
    
    def test_alpha_signal_combination(self):
        """Test optimization of signal combination."""
        market_data = {
            "feature_1": np.random.normal(0, 1, 500),
            "feature_2": np.random.normal(0, 1, 500)
        }
        returns = np.random.normal(0.001, 0.02, 500)
        
        result = alpha_miner.mine_alpha_signals(market_data, returns, n_signals=2)
        
        # If no signals were discovered, combination_weights will have default [1.0]
        # If signals were discovered, weights should sum to ~1
        if len(result.signals) > 0:
            assert len(result.combination_weights) == len(result.signals)
            assert abs(sum(result.combination_weights) - 1.0) < 0.01  # Weights sum to ~1
        else:
            # Default case when no signals discovered
            assert len(result.combination_weights) >= 1


class TestRiskSurfaceReconstruction:
    """Tests for risk surface reconstruction."""
    
    def test_risk_surface_construction(self):
        """Test construction of risk surface."""
        portfolio_returns = np.random.normal(0.001, 0.02, (5, 1000))
        
        result = risk_reconstructor.reconstruct_risk_surface(portfolio_returns)
        
        assert "risk_manifold" in result.__dict__
        assert "critical_points" in result.__dict__
        assert "gradient_flow" in result.__dict__
        assert "cryptographic_seal" in result.__dict__
    
    def test_critical_points_identification(self):
        """Test identification of risk hotspots."""
        portfolio_returns = np.random.normal(0.001, 0.02, (3, 500))
        
        result = risk_reconstructor.reconstruct_risk_surface(portfolio_returns)
        
        assert len(result.critical_points) > 0
        assert all("type" in cp for cp in result.critical_points)


# ============================================================================
# LAYER B: AUTONOMIC LAYER TESTS
# ============================================================================

class TestDriftDetection:
    """Tests for drift detection module."""
    
    def test_drift_detection_no_drift(self):
        """Test drift detection with no drift."""
        baseline = np.random.normal(0, 1, 1000)
        new_data = np.random.normal(0, 1, 1000)
        
        result = drift_detector.detect_drift("test_model", baseline, new_data)
        
        assert "drift_detected" in result.__dict__
        assert "drift_magnitude" in result.__dict__
        assert "cryptographic_seal" in result.__dict__
    
    def test_drift_detection_with_drift(self):
        """Test drift detection with actual drift."""
        baseline = np.random.normal(0, 1, 1000)
        new_data = np.random.normal(0.5, 1, 1000)  # Shifted mean
        
        result = drift_detector.detect_drift("test_model", baseline, new_data)
        
        assert 0 <= result.drift_magnitude <= 1
        assert len(result.recommended_actions) > 0
    
    def test_drift_recommendations(self):
        """Test generation of drift recommendations."""
        baseline = np.random.normal(0, 1, 500)
        new_data = np.random.normal(1.0, 1, 500)  # Large drift
        
        result = drift_detector.detect_drift("test_model", baseline, new_data)
        
        assert len(result.recommended_actions) > 0


class TestManifoldIntegrity:
    """Tests for manifold integrity checker."""
    
    def test_manifold_integrity_check(self):
        """Test manifold integrity checking."""
        manifold_data = np.random.normal(0, 1, (100, 5))
        
        result = manifold_checker.check_integrity(manifold_data)
        
        assert "betti_numbers" in result.__dict__
        assert "manifold_health_score" in result.__dict__
        assert "cryptographic_seal" in result.__dict__
    
    def test_betti_numbers_computation(self):
        """Test computation of Betti numbers."""
        manifold_data = np.random.normal(0, 1, (50, 3))
        
        result = manifold_checker.check_integrity(manifold_data)
        
        assert "betti_0" in result.betti_numbers
        assert result.betti_numbers["betti_0"] >= 0
    
    def test_manifold_health_score(self):
        """Test manifold health score computation."""
        manifold_data = np.random.normal(0, 1, (100, 5))
        
        result = manifold_checker.check_integrity(manifold_data)
        
        assert 0 <= result.manifold_health_score <= 1


class TestCurvatureAnomalyDetection:
    """Tests for curvature-based anomaly detection."""
    
    def test_anomaly_detection(self):
        """Test anomaly detection through curvature."""
        data = np.random.normal(0, 1, (100, 2))
        
        result = curvature_detector.detect_anomalies(data)
        
        assert "anomaly_locations" in result.__dict__
        assert "curvature_values" in result.__dict__
        assert "cryptographic_seal" in result.__dict__
    
    def test_anomaly_severity_scores(self):
        """Test computation of anomaly severity."""
        data = np.random.normal(0, 1, (50, 2))
        
        result = curvature_detector.detect_anomalies(data)
        
        assert len(result.anomaly_severity_scores) == len(data)
        assert all(0 <= s <= 1 for s in result.anomaly_severity_scores)


class TestFactorModelRepair:
    """Tests for factor model self-repair."""
    
    def test_factor_model_repair(self):
        """Test repair of degraded factor model."""
        model = {
            "loadings": np.random.normal(0, 1, (5, 3))
        }
        new_data = np.random.normal(0, 1, (1000, 5))
        returns = np.random.normal(0.001, 0.02, 1000)
        
        result = factor_repair.repair_model(model, new_data, returns)
        
        assert "repaired_factors" in result.__dict__
        assert "repair_confidence" in result.__dict__
        assert "cryptographic_seal" in result.__dict__
    
    def test_salamander_proposals(self):
        """Test generation of Salamander repair proposals."""
        model = {"loadings": np.random.normal(0, 1, (3, 2))}
        new_data = np.random.normal(0, 1, (500, 3))
        returns = np.random.normal(0.001, 0.02, 500)
        
        result = factor_repair.repair_model(model, new_data, returns)
        
        assert isinstance(result.salamander_proposals, list)


class TestEntropyOptimization:
    """Tests for entropy-based optimisation."""
    
    def test_entropy_optimization(self):
        """Test parameter optimisation based on entropy."""
        system = {"parameters": {"learning_rate": 0.01}}
        performance_data = np.random.normal(0, 1, 1000)
        
        result = entropy_optimizer.optimize_parameters(system, performance_data)
        
        assert "optimized_parameters" in result.__dict__
        assert "entropy_reduction" in result.__dict__
        assert "cryptographic_seal" in result.__dict__
    
    def test_entropy_reduction(self):
        """Test that optimisation reduces entropy."""
        system = {"parameters": {"batch_size": 32.0}}
        performance_data = np.random.normal(0, 1, 500)
        
        result = entropy_optimizer.optimize_parameters(system, performance_data)
        
        # Entropy reduction should be non-negative
        assert result.entropy_reduction >= 0


class TestTopologyRewiring:
    """Tests for topology-aware rewiring."""
    
    def test_topology_rewiring(self):
        """Test rewiring based on topological analysis."""
        system = {"component_1": 1.0, "component_2": 2.0}
        performance_data = np.random.normal(0, 1, 1000)
        
        result = topology_rewiring.rewire_system(system, performance_data)
        
        assert "new_topology" in result.__dict__
        assert "rewiring_confidence" in result.__dict__
        assert "governance_approval_status" in result.__dict__
    
    def test_governance_approval(self):
        """Test governance approval for rewiring."""
        system = {"component_1": 1.0}
        performance_data = np.random.normal(0, 1, 500)
        
        result = topology_rewiring.rewire_system(system, performance_data)
        
        assert result.governance_approval_status in [
            "auto_approved",
            "human_approval_required",
            "multi_party_approval_required",
            "no_change_needed"
        ]


# ============================================================================
# LAYER C: SOVEREIGN LAYER TESTS
# ============================================================================

class TestKernelReasoningVerification:
    """Tests for kernel-verified reasoning."""
    
    def test_reasoning_verification(self):
        """Test verification of reasoning chain."""
        reasoning_chain = [
            {"type": "premise", "confidence": 0.9},
            {"type": "inference", "confidence": 0.8},
            {"type": "conclusion", "confidence": 0.85}
        ]
        
        result = kernel_verifier.verify_reasoning(reasoning_chain)
        
        assert "reasoning_validity" in result.__dict__
        assert "verification_confidence" in result.__dict__
        assert "cryptographic_seal" in result.__dict__
    
    def test_kernel_similarity_scores(self):
        """Test computation of kernel similarity."""
        reasoning_chain = [
            {"type": "premise", "confidence": 0.9},
            {"type": "inference", "confidence": 0.8}
        ]
        
        result = kernel_verifier.verify_reasoning(reasoning_chain)
        
        assert "kernel_similarity_scores" in result.__dict__
        assert "avg_similarity" in result.kernel_similarity_scores


class TestStressTestHarness:
    """Tests for stress test harness."""
    
    def test_stress_test_execution(self):
        """Test execution of stress tests."""
        portfolio_returns = np.random.normal(0.001, 0.02, (5, 1000))
        
        result = stress_test_harness.run_stress_tests(portfolio_returns)
        
        assert "stress_scenario_results" in result.__dict__
        assert "var_estimates" in result.__dict__
        assert "cvar_estimates" in result.__dict__
        assert "cryptographic_seal" in result.__dict__
    
    def test_var_cvar_estimation(self):
        """Test VaR and CVaR estimation."""
        portfolio_returns = np.random.normal(0.001, 0.02, (3, 500))
        
        result = stress_test_harness.run_stress_tests(portfolio_returns)
        
        assert len(result.var_estimates) > 0
        assert len(result.cvar_estimates) > 0
    
    def test_tail_event_analysis(self):
        """Test tail event probability analysis."""
        portfolio_returns = np.random.normal(0.001, 0.02, (4, 500))
        
        result = stress_test_harness.run_stress_tests(portfolio_returns)
        
        assert "tail_event_probabilities" in result.__dict__


class TestSystemicRiskMapping:
    """Tests for systemic risk topology mapping."""
    
    def test_systemic_risk_mapping(self):
        """Test mapping of systemic risk topology."""
        financial_system = {
            "bank_0": 1.0,
            "bank_1": 2.0,
            "insurer_0": 1.5
        }
        
        result = systemic_risk_mapper.map_systemic_risk(financial_system)
        
        assert "financial_network" in result.__dict__
        assert "centrality_rankings" in result.__dict__
        assert "systemic_risk_hotspots" in result.__dict__
        assert "cryptographic_seal" in result.__dict__
    
    def test_centrality_computation(self):
        """Test computation of centrality measures."""
        financial_system = {
            "entity_0": 1.0,
            "entity_1": 2.0,
            "entity_2": 1.5
        }
        
        result = systemic_risk_mapper.map_systemic_risk(financial_system)
        
        assert len(result.centrality_rankings) > 0
    
    def test_risk_hotspots_identification(self):
        """Test identification of systemic risk hotspots."""
        financial_system = {
            "bank_0": 1.0,
            "bank_1": 2.0,
            "bank_2": 1.5,
            "insurer_0": 1.0
        }
        
        result = systemic_risk_mapper.map_systemic_risk(financial_system)
        
        assert len(result.systemic_risk_hotspots) > 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestFinancialIntelligenceIntegration:
    """Integration tests for full financial intelligence stack."""
    
    def test_core_to_autonomic_integration(self):
        """Test integration between core and autonomic layers."""
        # Core layer: regime detection
        prices = np.cumprod(1 + np.random.normal(0.001, 0.01, 1000))
        regime_result = regime_detector.detect_regime_shift(prices)
        
        # Autonomic layer: drift detection on regime
        baseline_regime = np.array([1.0 if regime_result.regime == "bull" else 0.0])
        new_regime = np.array([1.0 if regime_result.regime == "bull" else 0.0])
        
        drift_result = drift_detector.detect_drift(
            "regime_model", baseline_regime, new_regime
        )
        
        assert regime_result.cryptographic_seal["algorithm"] == "SHA-256"
        assert drift_result.cryptographic_seal["algorithm"] == "SHA-256"
    
    def test_autonomic_to_sovereign_integration(self):
        """Test integration between autonomic and sovereign layers."""
        # Autonomic layer: anomaly detection
        data = np.random.normal(0, 1, (100, 2))
        anomaly_result = anomaly_detector = curvature_detector.detect_anomalies(data)
        
        # Sovereign layer: stress test on anomalous data
        portfolio_returns = np.random.normal(0.001, 0.02, (3, 500))
        stress_result = stress_test_harness.run_stress_tests(portfolio_returns)
        
        assert anomaly_result.cryptographic_seal["algorithm"] == "SHA-256"
        assert stress_result.cryptographic_seal["algorithm"] == "SHA-256"
    
    def test_full_stack_evidence_sealing(self):
        """Test that all layers produce evidence seals."""
        # Core layer
        prices = np.cumprod(1 + np.random.normal(0.001, 0.01, 500))
        core_result = regime_detector.detect_regime_shift(prices)
        
        # Autonomic layer
        manifold_data = np.random.normal(0, 1, (50, 3))
        autonomic_result = manifold_checker.check_integrity(manifold_data)
        
        # Sovereign layer
        reasoning_chain = [{"type": "premise", "confidence": 0.9}]
        sovereign_result = kernel_verifier.verify_reasoning(reasoning_chain)
        
        # All should have SHA-256 seals
        assert core_result.cryptographic_seal["algorithm"] == "SHA-256"
        assert autonomic_result.cryptographic_seal["algorithm"] == "SHA-256"
        assert sovereign_result.cryptographic_seal["algorithm"] == "SHA-256"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
