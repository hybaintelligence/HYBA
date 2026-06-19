"""Benchmark script for UnifiedSearchKernel module with auditable JSON output.

This script benchmarks the UnifiedSearchKernel module performance and generates
auditable JSON output for reproducible evidence.

Benchmarks:
1. Search performance across different budgets
2. Warm cache vs cold cache latency
3. Domain-specific search performance
4. Resonance score computation
5. Neighbor generation performance
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

# Add python_backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from python_backend.core.search.unified_search_kernel import (
    PythiaMiningDomain,
    SatGeodesicDomain,
    UnifiedSearchKernel,
    WarmCache,
    YangMillsDomain,
)


@dataclass(frozen=True)
class BenchmarkResult:
    """Result of a single benchmark operation."""

    operation: str
    iterations: int
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    throughput_ops_per_sec: float
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "operation": self.operation,
            "iterations": self.iterations,
            "total_time_ms": self.total_time_ms,
            "avg_time_ms": self.avg_time_ms,
            "min_time_ms": self.min_time_ms,
            "max_time_ms": self.max_time_ms,
            "throughput_ops_per_sec": self.throughput_ops_per_sec,
            "metadata": dict(self.metadata),
        }


class UnifiedSearchBenchmark:
    """Benchmark suite for UnifiedSearchKernel module."""

    def __init__(self, iterations: int = 1000):
        """Initialize the benchmark suite.

        Args:
            iterations: Number of iterations for each benchmark
        """
        self.iterations = int(iterations)
        self._setup_test_domains()

    def _setup_test_domains(self):
        """Setup test domains for benchmarking."""
        # Mining domain
        self.mining_domain = PythiaMiningDomain(
            target_nonce=50,
            nonce_range=(0, 100),
        )
        self.mining_kernel = UnifiedSearchKernel(self.mining_domain)

        # SAT domain
        self.sat_domain = SatGeodesicDomain(
            num_variables=3,
            clauses=[[1, 2], [-1, 3]],
        )
        self.sat_kernel = UnifiedSearchKernel(self.sat_domain)

        # Yang-Mills domain
        self.yang_mills_domain = YangMillsDomain(
            lattice_size=10,
            initial_action=1.0,
        )
        self.yang_mills_kernel = UnifiedSearchKernel(self.yang_mills_domain)

    def benchmark_search_performance(self, budget: int = 10) -> BenchmarkResult:
        """Benchmark search performance with given budget."""
        times = []

        for _ in range(self.iterations):
            start = time.perf_counter()
            result = self.mining_kernel.search(budget=budget, seed=42)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="search_performance",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"budget": budget, "domain": "mining"},
        )

    def benchmark_warm_cache(self) -> BenchmarkResult:
        """Benchmark warm cache performance."""
        cache = WarmCache(max_size=100)
        kernel = UnifiedSearchKernel(self.mining_domain, warm_cache=cache)

        # Pre-warm the cache
        cache.store_warm(self.mining_domain.domain_id, 50)

        times = []

        for _ in range(self.iterations):
            start = time.perf_counter()
            result = kernel.search(budget=10, seed=42)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="warm_cache",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"cache_hit": result.latency_mode.value},
        )

    def benchmark_cold_cache(self) -> BenchmarkResult:
        """Benchmark cold cache performance."""
        cache = WarmCache(max_size=100)
        kernel = UnifiedSearchKernel(self.mining_domain, warm_cache=cache)

        times = []

        for _ in range(self.iterations):
            start = time.perf_counter()
            result = kernel.search(budget=10, seed=42)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="cold_cache",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"cache_hit": result.latency_mode.value},
        )

    def benchmark_domain_specific_search(self) -> BenchmarkResult:
        """Benchmark domain-specific search performance."""
        times = []

        for _ in range(self.iterations):
            start = time.perf_counter()
            result = self.sat_kernel.search(budget=10, seed=42)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="domain_specific_search",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"domain": "sat_geodesic"},
        )

    def benchmark_resonance_score(self) -> BenchmarkResult:
        """Benchmark resonance score computation."""
        times = []

        for _ in range(self.iterations):
            start = time.perf_counter()
            score = self.mining_domain.resonance_score(618)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="resonance_score",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"score": score},
        )

    def benchmark_neighbor_generation(self) -> BenchmarkResult:
        """Benchmark neighbor generation performance."""
        times = []

        for _ in range(self.iterations):
            start = time.perf_counter()
            neighbors = self.mining_domain.neighbor_fn(50)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="neighbor_generation",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"num_neighbors": len(neighbors)},
        )

    def run_all_benchmarks(self) -> Sequence[BenchmarkResult]:
        """Run all benchmarks and return results."""
        results = []

        print("Running UnifiedSearchKernel benchmarks...")
        print(f"Iterations: {self.iterations}")
        print()

        results.append(self.benchmark_search_performance(budget=10))
        print(f"✓ Search performance (budget=10): {results[-1].avg_time_ms:.3f}ms avg")

        results.append(self.benchmark_warm_cache())
        print(f"✓ Warm cache: {results[-1].avg_time_ms:.3f}ms avg")

        results.append(self.benchmark_cold_cache())
        print(f"✓ Cold cache: {results[-1].avg_time_ms:.3f}ms avg")

        results.append(self.benchmark_domain_specific_search())
        print(f"✓ Domain-specific search: {results[-1].avg_time_ms:.3f}ms avg")

        results.append(self.benchmark_resonance_score())
        print(f"✓ Resonance score: {results[-1].avg_time_ms:.3f}ms avg")

        results.append(self.benchmark_neighbor_generation())
        print(f"✓ Neighbor generation: {results[-1].avg_time_ms:.3f}ms avg")

        return results

    def generate_benchmark_report(
        self,
        results: Sequence[BenchmarkResult],
        output_file: Path,
    ) -> str:
        """Generate auditable benchmark report.

        Args:
            results: Benchmark results
            output_file: Path to output JSON file

        Returns:
            Formatted report string
        """
        report_dict = {
            "benchmark_suite": "UnifiedSearchKernel",
            "timestamp": time.time(),
            "iterations": self.iterations,
            "results": [r.to_dict() for r in results],
            "summary": {
                "total_operations": len(results),
                "total_time_ms": sum(r.total_time_ms for r in results),
                "avg_throughput": sum(r.throughput_ops_per_sec for r in results) / len(results),
            },
        }

        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write auditable JSON output
        output_file.write_text(json.dumps(report_dict, indent=2))

        # Generate human-readable report
        lines = [
            "=" * 80,
            "UNIFIED SEARCH KERNEL BENCHMARK REPORT",
            "=" * 80,
            "",
            f"Timestamp: {time.ctime(report_dict['timestamp'])}",
            f"Iterations: {self.iterations}",
            f"Results saved to: {output_file}",
            "",
            "-" * 80,
            "BENCHMARK RESULTS",
            "-" * 80,
            "",
        ]

        for result in results:
            lines.append(
                f"{result.operation:25s}: "
                f"{result.avg_time_ms:8.3f}ms avg | "
                f"{result.throughput_ops_per_sec:8.1f} ops/sec"
            )

        lines.append("")
        lines.append("-" * 80)
        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Total operations: {report_dict['summary']['total_operations']}")
        lines.append(f"Total time: {report_dict['summary']['total_time_ms']:.3f}ms")
        lines.append(f"Avg throughput: {report_dict['summary']['avg_throughput']:.1f} ops/sec")
        lines.append("=" * 80)

        return "\n".join(lines)


def main():
    """Main entry point for benchmark script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Benchmark UnifiedSearchKernel module with auditable JSON output"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1000,
        help="Number of iterations for each benchmark (default: 1000)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/unified_search_benchmark.json"),
        help="Output file for benchmark results (default: artifacts/unified_search_benchmark.json)",
    )

    args = parser.parse_args()

    # Run benchmarks
    benchmark = UnifiedSearchBenchmark(iterations=args.iterations)
    results = benchmark.run_all_benchmarks()

    # Generate report
    report = benchmark.generate_benchmark_report(results, args.output)
    print()
    print(report)
    print()


if __name__ == "__main__":
    main()
