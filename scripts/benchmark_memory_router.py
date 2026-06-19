"""Benchmark script for MemoryRoutedController module with auditable JSON output.

This script benchmarks the MemoryRoutedController module performance and generates
auditable JSON output for reproducible evidence.

Benchmarks:
1. Routing decision performance
2. Hebbian memory kernel performance
3. Circuit breaker performance
4. Memory learning performance (ACK/NACK)
5. Route probability computation
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

from python_backend.core.attribution.causal_router import CausalExplanation
from python_backend.core.meta_controller.memory_router import (
    CircuitBreaker,
    HebbianMemoryKernel,
    MemoryRoutedController,
    RouteDecision,
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


class MemoryRouterBenchmark:
    """Benchmark suite for MemoryRoutedController module."""

    def __init__(self, iterations: int = 1000):
        """Initialize the benchmark suite.

        Args:
            iterations: Number of iterations for each benchmark
        """
        self.iterations = int(iterations)
        self._setup_test_components()

    def _setup_test_components(self):
        """Setup test components for benchmarking."""
        # Mock causal router
        class MockCausalRouter:
            def explain(self, event, claim):
                return CausalExplanation(
                    hotspots=[],
                    counterfactual=None,
                    explanation_quality="high",
                    timestamp=time.time(),
                )

        # Mock audit log
        class MockAuditLog:
            def append(self, passport):
                pass

        self.causal_router = MockCausalRouter()
        self.audit_log = MockAuditLog()
        self.memory = HebbianMemoryKernel()
        self.breaker = CircuitBreaker()
        self.controller = MemoryRoutedController(
            self.memory,
            self.breaker,
            self.causal_router,
            self.audit_log,
        )

    def benchmark_routing_decision(self) -> BenchmarkResult:
        """Benchmark routing decision performance."""
        times = []

        for _ in range(self.iterations):
            signal = {"type": "test_signal"}
            start = time.perf_counter()
            result = self.controller.route(signal)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="routing_decision",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"decision": result.decision.value},
        )

    def benchmark_hebbian_memory(self) -> BenchmarkResult:
        """Benchmark Hebbian memory kernel performance."""
        self.memory.add_route("route_1", initial_weight=1.0)
        times = []

        for _ in range(self.iterations):
            start = time.perf_counter()
            self.memory.record_ack({"type": "test"}, "route_1")
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="hebbian_memory",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"history_length": len(self.memory.history)},
        )

    def benchmark_circuit_breaker(self) -> BenchmarkResult:
        """Benchmark circuit breaker performance."""
        times = []

        for _ in range(self.iterations):
            start = time.perf_counter()
            would_trip = self.breaker.would_trip("route_1", {"type": "test"})
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="circuit_breaker",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"would_trip": would_trip},
        )

    def benchmark_memory_learning(self) -> BenchmarkResult:
        """Benchmark memory learning performance (ACK/NACK)."""
        self.memory.add_route("route_2", initial_weight=0.0)
        times = []

        for i in range(self.iterations):
            signal = {"type": "test_signal"}
            start = time.perf_counter()
            # Alternate between ACK and NACK
            if i % 2 == 0:
                self.memory.record_ack(signal, "route_2")
            else:
                self.memory.record_nack(signal, "route_2")
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="memory_learning",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"final_weight": self.memory.weights.get("route_2", 0.0)},
        )

    def benchmark_route_probability(self) -> BenchmarkResult:
        """Benchmark route probability computation."""
        self.memory.add_route("route_3", initial_weight=1.0)
        self.memory.add_route("route_4", initial_weight=0.5)
        times = []

        for _ in range(self.iterations):
            start = time.perf_counter()
            probs = self.memory.current_route_probabilities()
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="route_probability",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"num_routes": len(probs)},
        )

    def run_all_benchmarks(self) -> Sequence[BenchmarkResult]:
        """Run all benchmarks and return results."""
        results = []

        print("Running MemoryRoutedController benchmarks...")
        print(f"Iterations: {self.iterations}")
        print()

        results.append(self.benchmark_routing_decision())
        print(f"✓ Routing decision: {results[-1].avg_time_ms:.3f}ms avg")

        results.append(self.benchmark_hebbian_memory())
        print(f"✓ Hebbian memory: {results[-1].avg_time_ms:.3f}ms avg")

        results.append(self.benchmark_circuit_breaker())
        print(f"✓ Circuit breaker: {results[-1].avg_time_ms:.3f}ms avg")

        results.append(self.benchmark_memory_learning())
        print(f"✓ Memory learning: {results[-1].avg_time_ms:.3f}ms avg")

        results.append(self.benchmark_route_probability())
        print(f"✓ Route probability: {results[-1].avg_time_ms:.3f}ms avg")

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
            "benchmark_suite": "MemoryRoutedController",
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
            "MEMORY ROUTED CONTROLLER BENCHMARK REPORT",
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
        description="Benchmark MemoryRoutedController module with auditable JSON output"
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
        default=Path("artifacts/memory_router_benchmark.json"),
        help="Output file for benchmark results (default: artifacts/memory_router_benchmark.json)",
    )

    args = parser.parse_args()

    # Run benchmarks
    benchmark = MemoryRouterBenchmark(iterations=args.iterations)
    results = benchmark.run_all_benchmarks()

    # Generate report
    report = benchmark.generate_benchmark_report(results, args.output)
    print()
    print(report)
    print()


if __name__ == "__main__":
    main()
