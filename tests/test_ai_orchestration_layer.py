"""
Comprehensive Test Suite for AI Orchestration Layer
Testing AI-powered capabilities at every stage of the mining lifecycle
"""

import pytest
import numpy as np
import time
from typing import Dict, Any

# Add python_backend to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "python_backend"))

from pythia_mining.ai_orchestration_layer import (
    UnifiedAIOrchestrationLayer,
    AIPoweredInitialization,
    AIDecisionMaker,
    AIOptimizedShareSubmission,
    AIAdvisorySystem,
    AIStage,
    AIDecision,
    AIRecommendation,
)


class TestAIStage:
    """Test AI stage enumeration."""
    
    def test_ai_stage_values(self):
        """Test AI stage enum values."""
        assert AIStage.INITIALIZATION.value == "initialization"
        assert AIStage.PARAMETER_OPTIMIZATION.value == "parameter_optimization"
        assert AIStage.NONCE_GENERATION.value == "nonce_generation"
        assert AIStage.SHARE_SUBMISSION.value == "share_submission"
        assert AIStage.ADVISORY.value == "advisory"
        assert AIStage.ANOMALY_DETECTION.value == "anomaly_detection"
        assert AIStage.RECOVERY.value == "recovery"


class TestAIPoweredInitialization:
    """Test AI-powered initialization system."""
    
    def test_initialization_initialization(self):
        """Test initialization system initialization."""
        init = AIPoweredInitialization()
        assert len(init.initialization_history) == 0
        assert len(init.system_capabilities) == 0
    
    def test_analyze_system_capabilities(self):
        """Test system capability analysis."""
        init = AIPoweredInitialization()
        
        system_info = {
            "cpu_cores": 8,
            "gpu_available": True,
            "memory_gb": 16,
            "network_bandwidth_mbps": 1000
        }
        
        capabilities = init.analyze_system_capabilities(system_info)
        
        assert "cpu_cores" in capabilities
        assert "gpu_available" in capabilities
        assert "memory_gb" in capabilities
        assert "capability_score" in capabilities
        assert capabilities["capability_score"] > 0
    
    def test_generate_initial_configuration(self):
        """Test AI-generated initial configuration."""
        init = AIPoweredInitialization()
        
        system_info = {
            "cpu_cores": 8,
            "gpu_available": True,
            "memory_gb": 16,
            "network_bandwidth_mbps": 1000
        }
        
        decision = init.generate_initial_configuration(system_info)
        
        assert isinstance(decision, AIDecision)
        assert decision.stage == AIStage.INITIALIZATION
        assert decision.decision_type == "initial_configuration"
        assert "thread_count" in decision.action
        assert "intensity" in decision.action
        assert 0 <= decision.confidence <= 1
        assert len(decision.explanation) > 0
    
    def test_initialization_history(self):
        """Test initialization history tracking."""
        init = AIPoweredInitialization()
        
        system_info = {
            "cpu_cores": 8,
            "gpu_available": True,
            "memory_gb": 16,
            "network_bandwidth_mbps": 1000
        }
        
        init.generate_initial_configuration(system_info)
        
        assert len(init.initialization_history) == 1
    
    def test_get_initialization_summary(self):
        """Test getting initialization summary."""
        init = AIPoweredInitialization()
        
        system_info = {
            "cpu_cores": 8,
            "gpu_available": True,
            "memory_gb": 16,
            "network_bandwidth_mbps": 1000
        }
        
        init.generate_initial_configuration(system_info)
        
        summary = init.get_initialization_summary()
        
        assert "total_initializations" in summary
        assert "current_capabilities" in summary
        assert summary["total_initializations"] == 1


class TestAIDecisionMaker:
    """Test AI decision-making throughout mining pipeline."""
    
    def test_decision_maker_initialization(self):
        """Test decision maker initialization."""
        maker = AIDecisionMaker()
        assert len(maker.decision_history) == 0
        assert len(maker.performance_metrics) == 0
    
    def test_analyze_performance_metrics(self):
        """Test performance metrics analysis."""
        maker = AIDecisionMaker()
        
        metrics = {
            "hashrate": 100.0,
            "efficiency": 0.8,
            "temperature": 50.0,
            "power_consumption": 200.0
        }
        
        analysis = maker.analyze_performance_metrics(metrics)
        
        assert "performance_score" in analysis
        assert "metrics" in analysis
        assert 0 <= analysis["performance_score"] <= 1
    
    def test_make_parameter_adjustment_decision(self):
        """Test parameter adjustment decision."""
        maker = AIDecisionMaker()
        
        metrics = {
            "hashrate": 50.0,
            "efficiency": 0.5,
            "temperature": 60.0,
            "power_consumption": 300.0,
            "intensity": 0.7,
            "thread_count": 4
        }
        
        decision = maker.make_parameter_adjustment_decision(metrics)
        
        assert isinstance(decision, AIDecision)
        assert decision.stage == AIStage.PARAMETER_OPTIMIZATION
        assert decision.decision_type == "parameter_adjustment"
        assert "parameter" in decision.action
        assert "old_value" in decision.action
        assert "new_value" in decision.action
    
    def test_parameter_adjustment_low_performance(self):
        """Test parameter adjustment for low performance."""
        maker = AIDecisionMaker()
        
        metrics = {
            "hashrate": 10.0,
            "efficiency": 0.3,
            "temperature": 70.0,
            "power_consumption": 400.0,
            "intensity": 0.9,
            "thread_count": 4
        }
        
        decision = maker.make_parameter_adjustment_decision(metrics)
        
        # Should reduce intensity for low performance
        assert decision.action["new_value"] < decision.action["old_value"]
    
    def test_parameter_adjustment_high_performance(self):
        """Test parameter adjustment for high performance."""
        maker = AIDecisionMaker()
        
        metrics = {
            "hashrate": 150.0,
            "efficiency": 0.9,
            "temperature": 40.0,
            "power_consumption": 150.0,
            "intensity": 0.5,
            "thread_count": 4
        }
        
        decision = maker.make_parameter_adjustment_decision(metrics)
        
        # Should increase intensity for high performance
        assert decision.action["new_value"] > decision.action["old_value"]
    
    def test_make_nonce_generation_decision(self):
        """Test nonce generation decision."""
        maker = AIDecisionMaker()
        
        context = {
            "difficulty": 1.0,
            "recent_shares": [
                {"accepted": True},
                {"accepted": True},
                {"accepted": False}
            ],
            "pool_type": "standard"
        }
        
        decision = maker.make_nonce_generation_decision(context)
        
        assert isinstance(decision, AIDecision)
        assert decision.stage == AIStage.NONCE_GENERATION
        assert decision.decision_type == "nonce_generation_strategy"
        assert "strategy" in decision.action
        assert "nonce_range" in decision.action
    
    def test_nonce_generation_low_success_rate(self):
        """Test nonce generation for low success rate."""
        maker = AIDecisionMaker()
        
        context = {
            "difficulty": 1.0,
            "recent_shares": [
                {"accepted": False},
                {"accepted": False},
                {"accepted": False}
            ],
            "pool_type": "standard"
        }
        
        decision = maker.make_nonce_generation_decision(context)
        
        # Should use conservative strategy
        assert decision.action["strategy"] == "conservative"
    
    def test_nonce_generation_high_success_rate(self):
        """Test nonce generation for high success rate."""
        maker = AIDecisionMaker()
        
        context = {
            "difficulty": 1.0,
            "recent_shares": [
                {"accepted": True},
                {"accepted": True},
                {"accepted": True}
            ],
            "pool_type": "standard"
        }
        
        decision = maker.make_nonce_generation_decision(context)
        
        # Should use aggressive strategy
        assert decision.action["strategy"] == "aggressive"
    
    def test_get_decision_summary(self):
        """Test getting decision summary."""
        maker = AIDecisionMaker()
        
        metrics = {
            "hashrate": 100.0,
            "efficiency": 0.8,
            "temperature": 50.0,
            "power_consumption": 200.0,
            "intensity": 0.7,
            "thread_count": 4
        }
        
        maker.make_parameter_adjustment_decision(metrics)
        
        summary = maker.get_decision_summary()
        
        assert "total_decisions" in summary
        assert "performance_metrics" in summary
        assert summary["total_decisions"] == 1


class TestAIOptimizedShareSubmission:
    """Test AI-optimized share submission system."""
    
    def test_submission_initialization(self):
        """Test submission system initialization."""
        submission = AIOptimizedShareSubmission()
        assert len(submission.submission_history) == 0
        assert len(submission.submission_patterns) == 0
    
    def test_analyze_submission_timing_empty(self):
        """Test submission timing analysis with empty history."""
        submission = AIOptimizedShareSubmission()
        
        analysis = submission.analyze_submission_timing([])
        
        assert "optimal_interval" in analysis
        assert "batch_size" in analysis
        assert analysis["batch_size"] == 1
    
    def test_analyze_submission_timing_with_data(self):
        """Test submission timing analysis with data."""
        submission = AIOptimizedShareSubmission()
        
        now = time.time()
        recent_submissions = [
            {"timestamp": now - 2.0, "accepted": True},
            {"timestamp": now - 1.0, "accepted": True},
            {"timestamp": now, "accepted": False}
        ]
        
        analysis = submission.analyze_submission_timing(recent_submissions)
        
        assert "optimal_interval" in analysis
        assert "batch_size" in analysis
        assert "success_rate" in analysis
        assert 0 <= analysis["success_rate"] <= 1
    
    def test_make_submission_decision(self):
        """Test share submission decision."""
        submission = AIOptimizedShareSubmission()
        
        shares = [
            {"nonce": 12345, "difficulty": 1.0},
            {"nonce": 12346, "difficulty": 1.0}
        ]
        
        pool_info = {
            "pool_name": "test_pool",
            "stratum_url": "stratum+tcp://test.com:3333"
        }
        
        decision = submission.make_submission_decision(shares, pool_info)
        
        assert isinstance(decision, AIDecision)
        assert decision.stage == AIStage.SHARE_SUBMISSION
        assert decision.decision_type == "share_submission_strategy"
        assert "strategy" in decision.action
        assert "batch_size" in decision.action
    
    def test_submission_decision_batched(self):
        """Test batched submission decision."""
        submission = AIOptimizedShareSubmission()
        
        # Add some history to enable batching
        now = time.time()
        for i in range(10):
            submission.submission_history.append({
                "timestamp": now - i,
                "accepted": True
            })
        
        shares = [{"nonce": i, "difficulty": 1.0} for i in range(20)]
        
        pool_info = {
            "pool_name": "test_pool",
            "stratum_url": "stratum+tcp://test.com:3333"
        }
        
        decision = submission.make_submission_decision(shares, pool_info)
        
        # Should use batched strategy with multiple shares
        assert decision.action["strategy"] in ["batched", "individual"]
        assert decision.action["num_batches"] >= 1
    
    def test_get_submission_summary(self):
        """Test getting submission summary."""
        submission = AIOptimizedShareSubmission()
        
        shares = [{"nonce": 12345, "difficulty": 1.0}]
        pool_info = {"pool_name": "test_pool"}
        
        submission.make_submission_decision(shares, pool_info)
        
        summary = submission.get_submission_summary()
        
        assert "total_submissions" in summary
        assert "submission_patterns" in summary
        assert summary["total_submissions"] == 1


class TestAIAdvisorySystem:
    """Test AI advisory system."""
    
    def test_advisory_initialization(self):
        """Test advisory system initialization."""
        advisory = AIAdvisorySystem()
        assert len(advisory.recommendations) == 0
        assert len(advisory.anomalies) == 0
    
    def test_generate_advisory_critical_temperature(self):
        """Test advisory generation for critical temperature."""
        advisory = AIAdvisorySystem()
        
        system_state = {
            "hashrate": 100.0,
            "temperature": 85.0,
            "efficiency": 0.8,
            "error_rate": 0.01
        }
        
        recommendation = advisory.generate_advisory(system_state)
        
        assert isinstance(recommendation, AIRecommendation)
        assert recommendation.stage == AIStage.ADVISORY
        assert recommendation.priority == "critical"
        assert "thermal" in recommendation.recommendation_type.lower()
    
    def test_generate_advisory_high_error_rate(self):
        """Test advisory generation for high error rate."""
        advisory = AIAdvisorySystem()
        
        system_state = {
            "hashrate": 100.0,
            "temperature": 50.0,
            "efficiency": 0.8,
            "error_rate": 0.15
        }
        
        recommendation = advisory.generate_advisory(system_state)
        
        assert isinstance(recommendation, AIRecommendation)
        assert recommendation.priority == "high"
        assert "error" in recommendation.recommendation_type.lower()
    
    def test_generate_advisory_low_hashrate(self):
        """Test advisory generation for low hashrate."""
        advisory = AIAdvisorySystem()
        
        system_state = {
            "hashrate": 30.0,
            "temperature": 50.0,
            "efficiency": 0.7,
            "error_rate": 0.01
        }
        
        recommendation = advisory.generate_advisory(system_state)
        
        assert isinstance(recommendation, AIRecommendation)
        assert recommendation.priority == "medium"
        assert "performance" in recommendation.recommendation_type.lower() or "optimization" in recommendation.recommendation_type.lower()
    
    def test_generate_advisory_normal_operation(self):
        """Test advisory generation for normal operation."""
        advisory = AIAdvisorySystem()
        
        system_state = {
            "hashrate": 100.0,
            "temperature": 50.0,
            "efficiency": 0.85,
            "error_rate": 0.01
        }
        
        recommendation = advisory.generate_advisory(system_state)
        
        assert isinstance(recommendation, AIRecommendation)
        assert recommendation.priority == "low"
        assert "maintenance" in recommendation.recommendation_type.lower()
    
    def test_detect_anomalies(self):
        """Test anomaly detection."""
        advisory = AIAdvisorySystem()
        
        metrics = {
            "hashrate": 100.0,
            "temperature": 50.0,
            "efficiency": 0.8,
            "invalid_metric": -1.0  # Should trigger anomaly
        }
        
        anomalies = advisory.detect_anomalies(metrics)
        
        assert isinstance(anomalies, list)
        # Should detect the invalid metric
        assert len(anomalies) > 0
    
    def test_detect_anomalies_normal(self):
        """Test anomaly detection with normal metrics."""
        advisory = AIAdvisorySystem()
        
        metrics = {
            "hashrate": 100.0,
            "temperature": 50.0,
            "efficiency": 0.8
        }
        
        anomalies = advisory.detect_anomalies(metrics)
        
        assert isinstance(anomalies, list)
        # Should not detect anomalies for normal metrics
        assert len(anomalies) == 0
    
    def test_get_advisory_summary(self):
        """Test getting advisory summary."""
        advisory = AIAdvisorySystem()
        
        system_state = {
            "hashrate": 100.0,
            "temperature": 50.0,
            "efficiency": 0.8,
            "error_rate": 0.01
        }
        
        advisory.generate_advisory(system_state)
        
        summary = advisory.get_advisory_summary()
        
        assert "total_recommendations" in summary
        assert "total_anomalies" in summary
        assert summary["total_recommendations"] == 1


class TestUnifiedAIOrchestrationLayer:
    """Test unified AI orchestration layer."""
    
    def test_orchestration_initialization(self):
        """Test orchestration layer initialization."""
        orchestration = UnifiedAIOrchestrationLayer()
        assert orchestration.initialization is not None
        assert orchestration.decision_maker is not None
        assert orchestration.share_submission is not None
        assert orchestration.advisory is not None
    
    def test_initialize_system(self):
        """Test system initialization through orchestration."""
        orchestration = UnifiedAIOrchestrationLayer()
        
        system_info = {
            "cpu_cores": 8,
            "gpu_available": True,
            "memory_gb": 16,
            "network_bandwidth_mbps": 1000
        }
        
        decision = orchestration.initialize_system(system_info)
        
        assert isinstance(decision, AIDecision)
        assert decision.stage == AIStage.INITIALIZATION
        assert len(orchestration.orchestration_history) == 1
    
    def test_make_pipeline_decision(self):
        """Test pipeline decision-making through orchestration."""
        orchestration = UnifiedAIOrchestrationLayer()
        
        metrics = {
            "hashrate": 100.0,
            "efficiency": 0.8,
            "temperature": 50.0,
            "power_consumption": 200.0,
            "intensity": 0.7,
            "thread_count": 4
        }
        
        context = {
            "difficulty": 1.0,
            "recent_shares": [{"accepted": True}],
            "pool_type": "standard"
        }
        
        decisions = orchestration.make_pipeline_decision(metrics, context)
        
        assert isinstance(decisions, dict)
        assert "parameter_adjustment" in decisions
        assert "nonce_generation" in decisions
        assert len(orchestration.orchestration_history) == 1
    
    def test_optimize_share_submission(self):
        """Test share submission optimization through orchestration."""
        orchestration = UnifiedAIOrchestrationLayer()
        
        shares = [{"nonce": 12345, "difficulty": 1.0}]
        pool_info = {"pool_name": "test_pool"}
        
        decision = orchestration.optimize_share_submission(shares, pool_info)
        
        assert isinstance(decision, AIDecision)
        assert decision.stage == AIStage.SHARE_SUBMISSION
        assert len(orchestration.orchestration_history) == 1
    
    def test_generate_advisory(self):
        """Test advisory generation through orchestration."""
        orchestration = UnifiedAIOrchestrationLayer()
        
        system_state = {
            "hashrate": 100.0,
            "temperature": 50.0,
            "efficiency": 0.8,
            "error_rate": 0.01
        }
        
        recommendation = orchestration.generate_advisory(system_state)
        
        assert isinstance(recommendation, AIRecommendation)
        assert recommendation.stage == AIStage.ADVISORY
        assert len(orchestration.orchestration_history) == 1
    
    def test_get_comprehensive_summary(self):
        """Test getting comprehensive summary."""
        orchestration = UnifiedAIOrchestrationLayer()
        
        system_info = {"cpu_cores": 8, "gpu_available": True, "memory_gb": 16, "network_bandwidth_mbps": 1000}
        orchestration.initialize_system(system_info)
        
        summary = orchestration.get_comprehensive_summary()
        
        assert "initialization_summary" in summary
        assert "decision_summary" in summary
        assert "submission_summary" in summary
        assert "advisory_summary" in summary
        assert "ai_stage_status" in summary
    
    def test_enable_disable_ai_stage(self):
        """Test enabling and disabling AI stages."""
        orchestration = UnifiedAIOrchestrationLayer()
        
        orchestration.disable_ai_stage(AIStage.INITIALIZATION)
        assert orchestration.ai_stage_status[AIStage.INITIALIZATION] == False
        
        orchestration.enable_ai_stage(AIStage.INITIALIZATION)
        assert orchestration.ai_stage_status[AIStage.INITIALIZATION] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
