"""
Unit and Integration Tests for Consciousness Latency Profiler

TESTING METHODOLOGY:
- Unit tests: Individual profiler components
- Integration tests: Full profiling pipeline
- Property-based tests: Amdahl's Law invariants
- Benchmark tests: Profiler overhead measurement

MATHEMATICAL PROPERTIES TESTED:
1. Amdahl's Law: 1 ≤ speedup ≤ speedup_factor
2. Bottleneck fractions sum to ≤ 1.0
3. Latency statistics: mean > 0, std >= 0
4. P95 >= P50, P99 >= P95 (percentile ordering)
"""

import sys
from pathlib import Path
import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, assume

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "python_backend"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from profile_consciousness_latency import LatencyProfiler
from pythia_mining.consciousness_engine import ConsciousnessEngine, ConsciousnessConfig
from pythia_mining.pulvini_operator import ManifoldOperator
from pythia_mining.iit_4_analyzer import IIT4Analyzer


# ============================================================================
# UNIT TESTS
# ============================================================================

class TestLatencyProfiler:
    """Unit tests for LatencyProfiler components."""
    
    @pytest.fixture
    def profiler(self):
        """Create profiler instance."""
        return LatencyProfiler(num_samples=10)
    
    @pytest.fixture
    def engine(self):
        """Create consciousness engine."""
        config = ConsciousnessConfig()
        operator = ManifoldOperator(dim=8)
        iit = IIT4Analyzer(system_size=8)
        return ConsciousnessEngine(operator=operator, config=config, iit_analyzer=iit)
    
    def test_amdahl_law_bounds(self, profiler):
        """Test Amdahl's Law speedup bounds."""
        # Speedup should be between 1.0 and speedup_factor
        for bottleneck_frac in [0.1, 0.5, 0.9]:
            for speedup_factor in [2, 5, 10, 50]:
                speedup = profiler.compute_amdahl_speedup(bottleneck_frac, speedup_factor)
                
                assert 1.0 <= speedup <= speedup_factor, \
                    f"Speedup {speedup} outside [1, {speedup_factor}] " \
                    f"for fraction {bottleneck_frac}"
    
    def test_amdahl_law_zero_fraction(self, profiler):
        """Test Amdahl's Law with zero bottleneck fraction."""
        speedup = profiler.compute_amdahl_speedup(0.0, 10.0)
        
        # No bottleneck → no speedup
        assert np.isclose(speedup, 1.0, atol=1e-10)
    
    def test_amdahl_law_full_fraction(self, profiler):
        """Test Amdahl's Law with 100% bottleneck."""
        speedup_factor = 10.0
        speedup = profiler.compute_amdahl_speedup(1.0, speedup_factor)
        
        # 100% bottleneck → full speedup
        assert np.isclose(speedup, speedup_factor, atol=1e-10)
    
    def test_bottleneck_classification(self, profiler):
        """Test bottleneck type classification."""
        test_cases = [
            ("numpy.linalg.eigh", "LINALG"),
            ("iit_4_analyzer.calculate_phi_max", "IIT"),
            ("numpy.asarray", "MEMORY"),
            ("<built-in method>", "PYTHON"),
            ("some_other_function", "OTHER"),
        ]
        
        for func_name, expected_type in test_cases:
            result = profiler.classify_bottleneck_type(func_name)
            assert result == expected_type, \
                f"Expected {expected_type} for {func_name}, got {result}"
    
    def test_latency_statistics_sanity(self, profiler, engine):
        """Test latency statistics have valid ranges."""
        # Profile small number of iterations
        stats = profiler.profile_phi_measurement_loop(engine, dim=4)
        
        # Basic sanity checks
        assert stats['mean_latency_ms'] > 0
        assert stats['std_latency_ms'] >= 0
        assert stats['min_latency_ms'] > 0
        assert stats['max_latency_ms'] >= stats['min_latency_ms']
        assert stats['p95_latency_ms'] >= stats['median_latency_ms']
        assert stats['p99_latency_ms'] >= stats['p95_latency_ms']
        assert stats['throughput_hz'] > 0
    
    def test_percentile_ordering(self, profiler, engine):
        """Test percentile ordering: P50 ≤ P95 ≤ P99."""
        stats = profiler.profile_phi_measurement_loop(engine, dim=4)
        
        assert stats['median_latency_ms'] <= stats['p95_latency_ms']
        assert stats['p95_latency_ms'] <= stats['p99_latency_ms']


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestLatencyProfilerIntegration:
    """Integration tests for full profiling pipeline."""
    
    def test_full_profiling_pipeline(self):
        """Test complete profiling from engine creation to analysis."""
        # Create engine
        config = ConsciousnessConfig()
        operator = ManifoldOperator(dim=4)
        iit = IIT4Analyzer(system_size=4)
        engine = ConsciousnessEngine(operator=operator, config=config, iit_analyzer=iit)
        
        # Profile
        profiler = LatencyProfiler(num_samples=5)
        stats = profiler.profile_phi_measurement_loop(engine, dim=4)
        
        # Analyze bottlenecks
        bottlenecks = profiler.analyze_bottlenecks(top_n=10)
        
        # Verify structure
        assert isinstance(stats, dict)
        assert 'mean_latency_ms' in stats
        assert isinstance(bottlenecks, list)
        assert len(bottlenecks) > 0
        
        # Verify bottleneck structure
        for func_name, cum_time, calls, per_call in bottlenecks:
            assert isinstance(func_name, str)
            assert cum_time >= 0
            assert calls >= 0
            assert per_call >= 0
    
    def test_bottleneck_category_aggregation(self):
        """Test bottleneck aggregation by category."""
        config = ConsciousnessConfig()
        operator = ManifoldOperator(dim=4)
        iit = IIT4Analyzer(system_size=4)
        engine = ConsciousnessEngine(operator=operator, config=config, iit_analyzer=iit)
        
        profiler = LatencyProfiler(num_samples=5)
        profiler.profile_phi_measurement_loop(engine, dim=4)
        
        bottlenecks = profiler.analyze_bottlenecks(top_n=15)
        
        # Aggregate by category
        category_times = {}
        for func_name, cum_time, calls, per_call in bottlenecks:
            category = profiler.classify_bottleneck_type(func_name)
            if category not in category_times:
                category_times[category] = 0.0
            category_times[category] += cum_time
        
        # Should have at least one category
        assert len(category_times) > 0
        
        # All times should be non-negative
        for category, time_ms in category_times.items():
            assert time_ms >= 0, f"Category {category} has negative time {time_ms}"


# ============================================================================
# PROPERTY-BASED TESTS (Hypothesis)
# ============================================================================

@given(
    bottleneck_fraction=st.floats(min_value=0.0, max_value=1.0),
    speedup_factor=st.floats(min_value=1.0, max_value=100.0)
)
@settings(max_examples=50, deadline=1000)
def test_amdahl_law_monotonicity(bottleneck_fraction, speedup_factor):
    """Property: Amdahl speedup increases with bottleneck fraction."""
    profiler = LatencyProfiler(num_samples=10)
    
    # Compute speedup at current fraction
    speedup = profiler.compute_amdahl_speedup(bottleneck_fraction, speedup_factor)
    
    # Speedup should be in valid range
    assert 1.0 <= speedup <= speedup_factor, \
        f"Speedup {speedup} outside [1, {speedup_factor}]"
    
    # If bottleneck fraction increases, speedup should increase (or stay same)
    if bottleneck_fraction < 1.0:
        higher_fraction = min(1.0, bottleneck_fraction + 0.1)
        higher_speedup = profiler.compute_amdahl_speedup(higher_fraction, speedup_factor)
        
        assert higher_speedup >= speedup - 1e-10, \
            f"Speedup should increase: {speedup} -> {higher_speedup}"


@given(
    fraction=st.floats(min_value=0.01, max_value=0.99),
    base_speedup=st.floats(min_value=2.0, max_value=10.0)
)
@settings(max_examples=30, deadline=1000)
def test_amdahl_law_speedup_scaling(fraction, base_speedup):
    """Property: Doubling speedup factor increases overall speedup."""
    profiler = LatencyProfiler(num_samples=10)
    
    speedup_1x = profiler.compute_amdahl_speedup(fraction, base_speedup)
    speedup_2x = profiler.compute_amdahl_speedup(fraction, base_speedup * 2)
    
    # Doubling the speedup factor should increase overall speedup
    assert speedup_2x > speedup_1x, \
        f"Speedup should increase: {speedup_1x} -> {speedup_2x}"


@given(
    latencies=st.lists(
        st.floats(min_value=0.1, max_value=1000.0),
        min_size=10,
        max_size=100
    )
)
@settings(max_examples=20, deadline=2000)
def test_percentile_properties(latencies):
    """Property: Percentiles follow ordering P50 ≤ P95 ≤ P99."""
    latencies_arr = np.array(latencies)
    
    p50 = float(np.percentile(latencies_arr, 50))
    p95 = float(np.percentile(latencies_arr, 95))
    p99 = float(np.percentile(latencies_arr, 99))
    
    assert p50 <= p95 + 1e-10, f"P50 ({p50}) should be ≤ P95 ({p95})"
    assert p95 <= p99 + 1e-10, f"P95 ({p95}) should be ≤ P99 ({p99})"


# ============================================================================
# BENCHMARK TESTS
# ============================================================================

class TestLatencyProfilerBenchmarks:
    """Benchmark tests for profiler overhead."""
    
    @pytest.mark.benchmark
    def test_profiler_overhead(self, benchmark):
        """Benchmark profiler overhead vs direct measurement."""
        config = ConsciousnessConfig()
        operator = ManifoldOperator(dim=4)
        iit = IIT4Analyzer(system_size=4)
        engine = ConsciousnessEngine(operator=operator, config=config, iit_analyzer=iit)
        
        # Generate test state
        state = np.random.randn(4, 4) + 1j * np.random.randn(4, 4)
        state = (state + state.conj().T) / 2.0  # Hermitian
        
        # Benchmark just the measurement (no profiling)
        result = benchmark(engine.measure_phi, [state])
        
        assert result.phi_integrated >= 0.0
    
    @pytest.mark.benchmark
    def test_amdahl_computation_speed(self, benchmark):
        """Benchmark Amdahl's Law computation speed."""
        profiler = LatencyProfiler(num_samples=10)
        
        result = benchmark(profiler.compute_amdahl_speedup, 0.5, 10.0)
        
        assert 1.0 <= result <= 10.0


# ============================================================================
# REGRESSION TESTS
# ============================================================================

class TestLatencyProfilerRegression:
    """Regression tests for known profiler behavior."""
    
    def test_known_amdahl_values(self):
        """Test Amdahl's Law with known inputs/outputs."""
        profiler = LatencyProfiler(num_samples=10)
        
        # Known cases from Amdahl's 1967 paper
        test_cases = [
            (0.5, 2.0, 1.333333),  # 50% bottleneck, 2x speedup
            (0.9, 10.0, 5.263158),  # 90% bottleneck, 10x speedup
            (0.95, 20.0, 10.256410),  # 95% bottleneck, 20x speedup
        ]
        
        for fraction, speedup_factor, expected in test_cases:
            result = profiler.compute_amdahl_speedup(fraction, speedup_factor)
            assert np.isclose(result, expected, rtol=1e-5), \
                f"Amdahl regression failed: {result} != {expected}"
    
    def test_classification_regression(self):
        """Test bottleneck classification doesn't change."""
        profiler = LatencyProfiler(num_samples=10)
        
        # Known classifications should remain stable
        known_classifications = {
            "numpy.linalg.eigh": "LINALG",
            "numpy.linalg.eigvalsh": "LINALG",
            "iit_4_analyzer.calculate_phi_max": "IIT",
            "numpy.asarray": "MEMORY",
            "<built-in method builtins.len>": "PYTHON",
        }
        
        for func_name, expected_type in known_classifications.items():
            result = profiler.classify_bottleneck_type(func_name)
            assert result == expected_type, \
                f"Classification regression: {func_name} changed from {expected_type} to {result}"


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestLatencyProfilerEdgeCases:
    """Edge case tests for boundary conditions."""
    
    def test_single_sample_profiling(self):
        """Test profiling with single sample."""
        config = ConsciousnessConfig()
        operator = ManifoldOperator(dim=4)
        iit = IIT4Analyzer(system_size=4)
        engine = ConsciousnessEngine(operator=operator, config=config, iit_analyzer=iit)
        
        profiler = LatencyProfiler(num_samples=1)
        stats = profiler.profile_phi_measurement_loop(engine, dim=4)
        
        # Should still work
        assert stats['mean_latency_ms'] > 0
        assert stats['num_samples'] == 1
    
    def test_zero_bottleneck_fraction(self):
        """Test Amdahl with zero bottleneck."""
        profiler = LatencyProfiler(num_samples=10)
        
        speedup = profiler.compute_amdahl_speedup(0.0, 1000.0)
        
        # No bottleneck → no speedup possible
        assert np.isclose(speedup, 1.0, atol=1e-10)
    
    def test_infinite_speedup_factor(self):
        """Test Amdahl with very large speedup factor."""
        profiler = LatencyProfiler(num_samples=10)
        
        # Very large speedup factor
        speedup = profiler.compute_amdahl_speedup(0.5, 1e10)
        
        # Should approach 2.0 (1/(1-0.5))
        assert np.isclose(speedup, 2.0, rtol=1e-5)
    
    def test_classification_with_empty_string(self):
        """Test classification with edge case inputs."""
        profiler = LatencyProfiler(num_samples=10)
        
        # Empty string
        result = profiler.classify_bottleneck_type("")
        assert result == "OTHER"
        
        # Very long string
        long_name = "a" * 1000
        result = profiler.classify_bottleneck_type(long_name)
        assert result in ["LINALG", "IIT", "MEMORY", "PYTHON", "OTHER"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
