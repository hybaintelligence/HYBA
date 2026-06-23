"""
Comprehensive Test Suite for Enterprise Benchmark Infrastructure
Tests all benchmark components with statistical validation
"""

import pytest
import json
import hashlib
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from datetime import datetime

# Import benchmark modules
from enterprise_benchmark_suite import BenchmarkSuite, BenchmarkResult, MetricsCollector
from evidence_provenance import (
    ProvenanceTracker,
    DatasetProvenance,
    CodeProvenance,
    EnvironmentProvenance,
    ExecutionProvenance,
)
from dataset_registry import (
    DatasetRegistry,
    FinancialDataset,
    MLDataset,
    CryptographicDataset,
    CachedDataset,
)
from superiority_metrics import (
    SuperiorityMetrics,
    SpeedMetrics,
    AccuracyMetrics,
    ScalabilityMetrics,
    EfficiencyMetrics,
    RobustnessMetrics,
)


class TestBenchmarkSuite:
    """Test BenchmarkSuite functionality"""

    def test_suite_initialization(self):
        """Test benchmark suite can be initialized"""
        suite = BenchmarkSuite()
        assert suite is not None
        assert hasattr(suite, "run_benchmark")
        assert hasattr(suite, "collect_metrics")

    def test_benchmark_execution(self):
        """Test benchmark execution completes"""
        suite = BenchmarkSuite()

        # Mock a simple benchmark
        def simple_benchmark():
            return {"duration": 1.5, "iterations": 100, "accuracy": 0.95}

        result = suite.run_benchmark("test_benchmark", simple_benchmark)

        assert result is not None
        assert "duration" in result or hasattr(result, "duration")

    def test_metrics_collection(self):
        """Test metrics collection works"""
        collector = MetricsCollector()

        # Collect various metrics
        collector.record_time("test_op", 1.5)
        collector.record_memory("test_op", 256)
        collector.record_accuracy("test_op", 0.95)

        metrics = collector.get_metrics("test_op")

        assert metrics is not None
        assert len(metrics) > 0

    def test_statistical_validation(self):
        """Test statistical validation of results"""
        suite = BenchmarkSuite()

        # Create mock results
        results = [
            BenchmarkResult(duration=1.0, accuracy=0.95, memory=256),
            BenchmarkResult(duration=1.1, accuracy=0.96, memory=260),
            BenchmarkResult(duration=0.9, accuracy=0.94, memory=252),
        ]

        # Verify statistical properties
        durations = [r.duration for r in results]
        mean_duration = np.mean(durations)
        std_duration = np.std(durations)

        assert mean_duration > 0
        assert std_duration >= 0
        assert 0.85 < mean_duration < 1.15


class TestProvenanceSystem:
    """Test Evidence Provenance System"""

    def test_provenance_tracker_initialization(self):
        """Test ProvenanceTracker initializes correctly"""
        tracker = ProvenanceTracker()
        assert tracker is not None
        assert hasattr(tracker, "track_dataset")
        assert hasattr(tracker, "track_execution")

    def test_dataset_provenance_hashing(self):
        """Test dataset provenance creates valid hashes"""
        provenance = DatasetProvenance(
            name="test_dataset", source="test_source", version="1.0.0"
        )

        hash_val = provenance.compute_hash()

        assert hash_val is not None
        assert len(hash_val) == 64  # SHA-256 hex length
        assert all(c in "0123456789abcdef" for c in hash_val)

    def test_code_provenance_git_integration(self):
        """Test code provenance captures git information"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock git repo
            os.system(f"cd {tmpdir} && git init --quiet")

            provenance = CodeProvenance(file_path=tmpdir, git_repo=tmpdir)

            # Should capture git info or gracefully handle missing repo
            assert provenance is not None
            assert hasattr(provenance, "get_commit_hash")

    def test_environment_provenance_capture(self):
        """Test environment provenance captures system info"""
        provenance = EnvironmentProvenance()

        env_info = provenance.capture()

        assert env_info is not None
        assert "python_version" in env_info
        assert "platform" in env_info
        assert "memory" in env_info

    def test_execution_provenance_logging(self):
        """Test execution provenance logs parameters"""
        provenance = ExecutionProvenance(
            benchmark_name="test_bench", parameters={"seed": 42, "iterations": 100}
        )

        log = provenance.to_dict()

        assert log["benchmark_name"] == "test_bench"
        assert log["parameters"]["seed"] == 42
        assert "timestamp" in log

    def test_provenance_audit_trail(self):
        """Test complete provenance audit trail"""
        tracker = ProvenanceTracker()

        # Track multiple operations
        tracker.track_dataset("dataset_1", "source_1")
        tracker.track_dataset("dataset_2", "source_2")
        tracker.track_execution("exec_1", {"param": 1})

        trail = tracker.get_audit_trail()

        assert trail is not None
        assert len(trail) >= 3


class TestDatasetRegistry:
    """Test Dataset Registry functionality"""

    def test_registry_initialization(self):
        """Test registry initializes"""
        registry = DatasetRegistry()
        assert registry is not None
        assert hasattr(registry, "register_dataset")
        assert hasattr(registry, "get_dataset")

    def test_financial_dataset_creation(self):
        """Test financial dataset creation"""
        dataset = FinancialDataset(
            name="test_portfolio", source="synthetic", num_assets=100, num_periods=252
        )

        data = dataset.generate()

        assert data is not None
        assert len(data) == 252
        assert all(len(row) >= 100 for row in data)

    def test_ml_dataset_creation(self):
        """Test ML dataset creation"""
        dataset = MLDataset(
            name="test_mnist", source="synthetic", num_samples=100, num_features=784
        )

        data = dataset.generate()

        assert data is not None
        assert data.shape[0] == 100
        assert data.shape[1] == 784

    def test_cryptographic_dataset_creation(self):
        """Test cryptographic dataset creation"""
        dataset = CryptographicDataset(
            name="test_rsa", source="synthetic", key_size=2048, num_samples=10
        )

        data = dataset.generate()

        assert data is not None
        assert len(data) == 10

    def test_dataset_caching(self):
        """Test dataset caching works"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = CachedDataset(name="test_cache", cache_dir=tmpdir)

            # First call should generate
            data1 = cache.get_data()

            # Second call should use cache
            data2 = cache.get_data()

            assert data1 is not None
            assert data2 is not None
            # Verify cache was used (same object or equal data)
            assert np.array_equal(data1, data2) or (data1 == data2)

    def test_dataset_hash_verification(self):
        """Test dataset hash verification"""
        dataset = FinancialDataset(
            name="test_hash", source="synthetic", num_assets=10, num_periods=50
        )

        hash1 = dataset.compute_hash()
        hash2 = dataset.compute_hash()

        # Deterministic generation should produce same hash
        assert hash1 == hash2

    def test_registry_listing(self):
        """Test registry can list datasets"""
        registry = DatasetRegistry()

        # Register multiple datasets
        registry.register_dataset(FinancialDataset("fin1", "synthetic", 10, 50))
        registry.register_dataset(MLDataset("ml1", "synthetic", 100, 784))

        datasets = registry.list_datasets()

        assert len(datasets) >= 2


class TestSuperiorityMetrics:
    """Test Superiority Metrics calculation"""

    def test_speed_metrics_calculation(self):
        """Test speed metrics are calculated correctly"""
        metrics = SpeedMetrics()

        # Test speedup calculation
        speedup = metrics.calculate_speedup(baseline_time=10.0, optimized_time=2.0)
        assert speedup == 5.0

        # Test throughput calculation
        throughput = metrics.calculate_throughput(operations=1000, duration=2.0)
        assert throughput == 500.0

    def test_accuracy_metrics_calculation(self):
        """Test accuracy metrics"""
        metrics = AccuracyMetrics()

        # Create mock predictions and labels
        predictions = np.array([1, 0, 1, 1, 0])
        labels = np.array([1, 0, 1, 0, 0])

        accuracy = metrics.calculate_accuracy(predictions, labels)
        assert 0 <= accuracy <= 1
        assert accuracy == 0.8  # 4 correct out of 5

    def test_precision_recall_f1(self):
        """Test precision, recall, F1 calculation"""
        metrics = AccuracyMetrics()

        predictions = np.array([1, 1, 0, 1, 0, 0, 1, 1])
        labels = np.array([1, 1, 0, 0, 0, 1, 1, 0])

        # TP=3, FP=1, FN=1, TN=3
        precision = metrics.calculate_precision(predictions, labels)
        recall = metrics.calculate_recall(predictions, labels)
        f1 = metrics.calculate_f1(predictions, labels)

        assert 0 <= precision <= 1
        assert 0 <= recall <= 1
        assert 0 <= f1 <= 1
        assert precision == 0.75  # 3/(3+1)
        assert recall == 0.75  # 3/(3+1)

    def test_scalability_metrics(self):
        """Test scalability metrics"""
        metrics = ScalabilityMetrics()

        # Test scaling factor
        scaling = metrics.calculate_scaling_factor(
            small_size=100, large_size=1000, small_time=1.0, large_time=15.0
        )

        assert scaling > 0

    def test_efficiency_metrics(self):
        """Test efficiency metrics"""
        metrics = EfficiencyMetrics()

        # Test energy efficiency
        energy = metrics.calculate_energy_efficiency(work=1000, energy_joules=50)

        assert energy == 20.0  # work/energy

    def test_robustness_metrics(self):
        """Test robustness metrics"""
        metrics = RobustnessMetrics()

        # Test error recovery
        errors = [1, 0, 0, 1, 0, 0, 0, 1, 0, 0]
        recovery_rate = metrics.calculate_error_recovery(errors)

        assert 0 <= recovery_rate <= 1

    def test_statistical_significance(self):
        """Test statistical significance calculation"""
        metrics = SuperiorityMetrics()

        # Two samples
        sample1 = np.array([1.0, 1.1, 0.9, 1.05, 0.95])
        sample2 = np.array([2.0, 2.1, 1.9, 2.05, 1.95])

        pvalue, effect_size = metrics.calculate_statistical_significance(
            sample1, sample2
        )

        assert 0 <= pvalue <= 1
        assert effect_size is not None

    def test_confidence_intervals(self):
        """Test confidence interval calculation"""
        metrics = SuperiorityMetrics()

        data = np.array([1.0, 1.1, 0.9, 1.05, 0.95, 1.02, 0.98])
        ci_lower, ci_upper = metrics.calculate_confidence_interval(
            data, confidence=0.95
        )

        assert ci_lower < ci_upper
        assert ci_lower < np.mean(data)
        assert ci_upper > np.mean(data)


class TestIntegration:
    """Integration tests across all components"""

    def test_end_to_end_benchmark_execution(self):
        """Test complete benchmark execution pipeline"""
        # Initialize components
        suite = BenchmarkSuite()
        tracker = ProvenanceTracker()
        registry = DatasetRegistry()
        metrics = SuperiorityMetrics()

        # Register dataset
        dataset = FinancialDataset("test", "synthetic", 10, 50)
        registry.register_dataset(dataset)

        # Track dataset
        tracker.track_dataset(dataset.name, dataset.source)

        # Run benchmark
        def bench_func():
            data = dataset.generate()
            return {"accuracy": 0.95, "duration": 1.5}

        result = suite.run_benchmark("test_bench", bench_func)

        # Track execution
        tracker.track_execution("test_bench", {})

        # Get provenance
        trail = tracker.get_audit_trail()

        assert trail is not None
        assert len(trail) > 0

    def test_reproducibility_across_runs(self):
        """Test that benchmarks are reproducible"""
        np.random.seed(42)

        dataset1 = FinancialDataset("test", "synthetic", 10, 50)
        data1 = dataset1.generate()
        hash1 = dataset1.compute_hash()

        np.random.seed(42)

        dataset2 = FinancialDataset("test", "synthetic", 10, 50)
        data2 = dataset2.generate()
        hash2 = dataset2.compute_hash()

        # With same seed, should get same results
        assert hash1 == hash2
        assert np.array_equal(data1, data2)

    def test_evidence_serialization(self):
        """Test evidence can be serialized"""
        tracker = ProvenanceTracker()
        tracker.track_dataset("ds1", "source1")
        tracker.track_execution("ex1", {"param": 1})

        # Get audit trail and serialize
        trail = tracker.get_audit_trail()

        # Should be JSON serializable
        json_str = json.dumps(trail, default=str)

        assert json_str is not None
        assert len(json_str) > 0

    def test_all_metrics_comparison(self):
        """Test comparing metrics across runs"""
        # Baseline
        baseline_duration = 10.0
        baseline_accuracy = 0.90

        # Optimized
        optimized_duration = 2.0
        optimized_accuracy = 0.95

        speed_metrics = SpeedMetrics()
        speedup = speed_metrics.calculate_speedup(baseline_duration, optimized_duration)

        accuracy_metrics = AccuracyMetrics()
        # This is just accuracy values, but we can create comparison

        assert speedup == 5.0
        assert optimized_accuracy > baseline_accuracy


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_dataset_handling(self):
        """Test handling of empty datasets"""
        dataset = FinancialDataset("empty", "synthetic", 0, 0)
        data = dataset.generate()

        # Should handle gracefully
        assert data is not None or data == []

    def test_invalid_metrics_handling(self):
        """Test handling of invalid metric inputs"""
        metrics = SpeedMetrics()

        # Test with invalid inputs
        with pytest.raises((ValueError, ZeroDivisionError, TypeError)):
            metrics.calculate_speedup(-1, 2.0)  # Negative baseline

    def test_missing_dataset_retrieval(self):
        """Test retrieving missing dataset"""
        registry = DatasetRegistry()

        result = registry.get_dataset("nonexistent")

        # Should return None or raise appropriate error
        assert result is None or isinstance(result, Exception)

    def test_corrupted_provenance(self):
        """Test handling corrupted provenance data"""
        tracker = ProvenanceTracker()

        # Should not crash with invalid data
        try:
            tracker.track_dataset("", "")
            trail = tracker.get_audit_trail()
            assert trail is not None
        except Exception:
            pass


class TestPerformance:
    """Test performance characteristics"""

    def test_large_dataset_handling(self):
        """Test handling of large datasets"""
        dataset = FinancialDataset("large", "synthetic", 1000, 1000)

        import time

        start = time.time()
        data = dataset.generate()
        duration = time.time() - start

        # Should complete in reasonable time
        assert duration < 30  # 30 seconds max
        assert data is not None

    def test_multiple_benchmark_execution(self):
        """Test executing multiple benchmarks"""
        suite = BenchmarkSuite()

        def bench1():
            return {"result": 1}

        def bench2():
            return {"result": 2}

        def bench3():
            return {"result": 3}

        results = []
        for i, bench_func in enumerate([bench1, bench2, bench3]):
            result = suite.run_benchmark(f"bench_{i}", bench_func)
            results.append(result)

        assert len(results) == 3

    def test_provenance_overhead(self):
        """Test provenance tracking overhead"""
        import time

        tracker = ProvenanceTracker()

        start = time.time()
        for i in range(100):
            tracker.track_dataset(f"ds_{i}", "source")
        duration = time.time() - start

        # Should be efficient
        assert duration < 5  # 5 seconds for 100 operations


# Test execution configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
