"""Benchmark script for CausalAttributionEngine module with auditable JSON output.

This script benchmarks the CausalAttributionEngine module performance and generates
auditable JSON output for reproducible evidence.

Benchmarks:
1. Hotspot ranking performance
2. Counterfactual coverage computation
3. Explanation generation performance
4. Fabric graph traversal performance
5. Domain-specific graph performance
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

from python_backend.core.attribution.causal_router import (
    CausalAttributionEngine,
    CausalHotspot,
    CounterfactualResult,
    CausalExplanation,
    FabricGraph,
    MiningGraph,
    SecuritySwarmGraph,
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


class CausalAttributionBenchmark:
    """Benchmark suite for CausalAttributionEngine module."""

    def __init__(self, iterations: int = 1000):
        """Initialize the benchmark suite.

        Args:
            iterations: Number of iterations for each benchmark
        """
        self.iterations = int(iterations)
        self._setup_test_graphs()

    def _setup_test_graphs(self):
        """Setup test graphs for benchmarking."""
        # Mining graph
        self.mining_nodes = {
            "solver": {"type": "hendrix_phi", "impact": 0.8},
            "memory": {"type": "hebbian_kernel", "impact": 0.6},
            "network": {"type": "stratum_client", "impact": 0.5},
        }
        self.mining_edges = {
            "solver": ["memory", "network"],
            "memory": ["solver"],
            "network": ["solver"],
        }
        self.mining_graph = MiningGraph(self.mining_nodes, self.mining_edges)
        self.mining_engine = CausalAttributionEngine(self.mining_graph)

        # Security graph
        self.security_nodes = {
            "detector": {"type": "intrusion_detection", "impact": 0.9},
            "firewall": {"type": "circuit_breaker", "impact": 0.7},
            "logger": {"type": "audit_logger", "impact": 0.4},
        }
        self.security_edges = {
            "detector": ["firewall", "logger"],
            "firewall": ["detector"],
            "logger": ["detector"],
        }
        self.security_graph = SecuritySwarmGraph(self.security_nodes, self.security_edges)
        self.security_engine = CausalAttributionEngine(self.security_graph)

    def benchmark_hotspot_ranking(self) -> BenchmarkResult:
        """Benchmark hotspot ranking performance."""
        times = []

        for _ in range(self.iterations):
            event = {"type": "nonce_found", "nonce": 12345}
            start = time.perf_counter()
            hotspots = self.mining_engine.rank_hotspots(event)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="hotspot_ranking",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"graph_type": "mining", "num_hotspots": len(hotspots)},
        )

    def benchmark_counterfactual_coverage(self) -> BenchmarkResult:
        """Benchmark counterfactual coverage computation."""
        times = []

        for _ in range(self.iterations):
            event = {"type": "nonce_found", "nonce": 12345}
            claim = {"route": "solver", "type": "routing_decision"}
            start = time.perf_counter()
            counterfactual = self.mining_engine.compute_counterfactual(event, claim)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="counterfactual_coverage",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"coverage_ratio": counterfactual.coverage_ratio},
        )

    def benchmark_explanation_generation(self) -> BenchmarkResult:
        """Benchmark explanation generation performance."""
        times = []

        for _ in range(self.iterations):
            event = {"type": "nonce_found", "nonce": 12345}
            claim = {"route": "solver", "type": "routing_decision"}
            start = time.perf_counter()
            explanation = self.mining_engine.explain(event, claim)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="explanation_generation",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={
                "explanation_quality": explanation.explanation_quality,
                "num_hotspots": len(explanation.hotspots),
            },
        )

    def benchmark_graph_traversal(self) -> BenchmarkResult:
        """Benchmark fabric graph traversal performance."""
        times = []

        for _ in range(self.iterations):
            event = {"type": "nonce_found", "nonce": 12345}
            start = time.perf_counter()
            self.mining_graph.participating_nodes(event)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="graph_traversal",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"graph_type": "mining", "num_nodes": len(self.mining_nodes)},
        )

    def benchmark_domain_specific_graphs(self) -> BenchmarkResult:
        """Benchmark domain-specific graph performance."""
        times = []

        for _ in range(self.iterations):
            event = {"type": "mode_transition", "mode": "safe"}
            start = time.perf_counter()
            hotspots = self.security_engine.rank_hotspots(event)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="domain_specific_graphs",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"graph_type": "security_swarm", "num_hotspots": len(hotspots)},
        )

    def run_all_benchmarks(self) -> Sequence[BenchmarkResult]:
        """Run all benchmarks and return results."""
        results = []

        print("Running CausalAttributionEngine benchmarks...")
        print(f"Iterations: {self.iterations}")
        print()

        results.append(self.benchmark_hotspot_ranking())
        print(f"✓ Hotspot ranking: {results[-1].avg_time_ms:.3f}ms avg")

        results.append(self.benchmark_counterfactual_coverage())
        print(f"✓ Counterfactual coverage: {results[-1].avg_time_ms:.3f}ms avg")

        results.append(self.benchmark_explanation_generation())
        print(f"✓ Explanation generation: {results[-1].avg_time_ms:.3f}ms avg")

        results.append(self.benchmark_graph_traversal())
        print(f"✓ Graph traversal: {results[-1].avg_time_ms:.3f}ms avg")

        results.append(self.benchmark_domain_specific_graphs())
        print(f"✓ Domain-specific graphs: {results[-1].avg_time_ms:.3f}ms avg")

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
            "benchmark_suite": "CausalAttributionEngine",
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
            "CAUSAL ATTRIBUTION ENGINE BENCHMARK REPORT",
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
        description="Benchmark CausalAttributionEngine module with auditable JSON output"
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
        default=Path("artifacts/causal_attribution_benchmark.json"),
        help="Output file for benchmark results (default: artifacts/causal_attribution_benchmark.json)",
    )

    args = parser.parse_args()

    # Run benchmarks
    benchmark = CausalAttributionBenchmark(iterations=args.iterations)
    results = benchmark.run_all_benchmarks()

    # Generate report
    report = benchmark.generate_benchmark_report(results, args.output)
    print()
    print(report)
    print()


if __name__ == "__main__":
    main()
