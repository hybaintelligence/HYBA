"""Integration benchmark for all modules working together with auditable JSON output.

This script benchmarks the complete integration of all core modules and generates
auditable JSON output for reproducible evidence.

Integration Workflow:
1. UniversalPassport creation and verification
2. CausalAttributionEngine explanation generation
3. UnifiedSearchKernel search execution
4. MemoryRoutedController routing decision
5. End-to-end workflow with all modules
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

from python_backend.core.audit.universal_passport import (
    ClaimType,
    EpistemicBound,
    SharedAuditLog,
    Subsystem,
    make_passport,
)
from python_backend.core.attribution.causal_router import (
    CausalAttributionEngine,
    CausalExplanation,
    MiningGraph,
)
from python_backend.core.meta_controller.memory_router import (
    CircuitBreaker,
    HebbianMemoryKernel,
    MemoryRoutedController,
)
from python_backend.core.search.unified_search_kernel import (
    PythiaMiningDomain,
    UnifiedSearchKernel,
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


class IntegrationBenchmark:
    """Benchmark suite for complete module integration."""

    def __init__(self, iterations: int = 1000):
        """Initialize the benchmark suite.

        Args:
            iterations: Number of iterations for each benchmark
        """
        self.iterations = int(iterations)
        self._setup_integration_components()

    def _setup_integration_components(self):
        """Setup all integration components."""
        # UniversalPassport components
        self.audit_log = SharedAuditLog()

        # CausalAttributionEngine components
        mining_nodes = {
            "solver": {"type": "hendrix_phi", "impact": 0.8},
            "memory": {"type": "hebbian_kernel", "impact": 0.6},
        }
        mining_edges = {
            "solver": ["memory"],
            "memory": ["solver"],
        }
        self.mining_graph = MiningGraph(mining_nodes, mining_edges)
        self.causal_engine = CausalAttributionEngine(self.mining_graph)

        # UnifiedSearchKernel components
        self.mining_domain = PythiaMiningDomain(target_nonce=50, nonce_range=(0, 100))
        self.search_kernel = UnifiedSearchKernel(self.mining_domain)

        # MemoryRoutedController components
        class MockCausalRouter:
            def explain(self, event, claim):
                return CausalExplanation(
                    hotspots=[],
                    counterfactual=None,
                    explanation_quality="high",
                    timestamp=time.time(),
                )

        class MockAuditLog:
            def append(self, passport):
                pass

        self.memory_kernel = HebbianMemoryKernel()
        self.circuit_breaker = CircuitBreaker()
        self.memory_controller = MemoryRoutedController(
            self.memory_kernel,
            self.circuit_breaker,
            MockCausalRouter(),
            MockAuditLog(),
        )

    def benchmark_passport_to_audit_log(self) -> BenchmarkResult:
        """Benchmark passport creation and audit log append."""
        times = []

        for i in range(self.iterations):
            start = time.perf_counter()
            passport = make_passport(
                subsystem=Subsystem.PYTHIA.value,
                claim_type=ClaimType.NONCE_FOUND.value,
                payload={"nonce": i, "job_id": "test_job"},
                epistemic_bounds=[EpistemicBound.NO_QUANTUM_SPEEDUP.value],
            )
            self.audit_log.append(passport)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="passport_to_audit_log",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"final_log_size": len(self.audit_log.get_entries())},
        )

    def benchmark_search_to_causal(self) -> BenchmarkResult:
        """Benchmark search followed by causal explanation."""
        times = []

        for _ in range(self.iterations):
            start = time.perf_counter()
            # Search
            search_result = self.search_kernel.search(budget=10, seed=42)
            # Causal explanation
            event = {"type": "nonce_found", "nonce": search_result.candidate}
            claim = {"route": "solver", "type": "routing_decision"}
            explanation = self.causal_engine.explain(event, claim)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="search_to_causal",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"explanation_quality": explanation.explanation_quality},
        )

    def benchmark_memory_routing(self) -> BenchmarkResult:
        """Benchmark memory-based routing with learning."""
        self.memory_kernel.add_route("route_1", initial_weight=1.0)
        times = []

        for i in range(self.iterations):
            signal = {"type": "test_signal", "iteration": i}
            start = time.perf_counter()
            result = self.memory_controller.route(signal)
            # Record learning
            if result.decision.value == "execute":
                self.memory_kernel.record_ack(signal, result.route)
            else:
                self.memory_kernel.record_nack(signal, result.route)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="memory_routing",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"final_weight": self.memory_kernel.weights.get("route_1", 0.0)},
        )

    def benchmark_end_to_end_workflow(self) -> BenchmarkResult:
        """Benchmark complete end-to-end workflow with all modules."""
        times = []

        for i in range(self.iterations):
            start = time.perf_counter()

            # Step 1: Create passport
            passport = make_passport(
                subsystem=Subsystem.PYTHIA.value,
                claim_type=ClaimType.NONCE_FOUND.value,
                payload={"nonce": i, "job_id": "test_job"},
                epistemic_bounds=[EpistemicBound.NO_QUANTUM_SPEEDUP.value],
            )

            # Step 2: Append to audit log
            self.audit_log.append(passport)

            # Step 3: Search
            search_result = self.search_kernel.search(budget=10, seed=42)

            # Step 4: Causal explanation
            event = {"type": "nonce_found", "nonce": search_result.candidate}
            claim = {"route": "solver", "type": "routing_decision"}
            explanation = self.causal_engine.explain(event, claim)

            # Step 5: Memory routing
            signal = {"type": "test_signal", "nonce": search_result.candidate}
            routing_result = self.memory_controller.route(signal)

            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="end_to_end_workflow",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={
                "workflow_steps": 5,
                "log_size": len(self.audit_log.get_entries()),
            },
        )

    def benchmark_module_interoperability(self) -> BenchmarkResult:
        """Benchmark interoperability between modules."""
        times = []

        for _ in range(self.iterations):
            start = time.perf_counter()

            # Create passport with causal context
            passport = make_passport(
                subsystem=Subsystem.PYTHIA.value,
                claim_type=ClaimType.NONCE_FOUND.value,
                payload={
                    "nonce": 42,
                    "causal_hotspots": ["solver", "memory"],
                    "search_confidence": 0.8,
                },
                epistemic_bounds=[EpistemicBound.NO_QUANTUM_SPEEDUP.value],
            )

            # Use passport data in causal engine
            event = {"type": "nonce_found", "passport": passport.to_dict()}
            claim = {"route": "solver", "type": "routing_decision"}
            explanation = self.causal_engine.explain(event, claim)

            # Use causal result in memory routing
            signal = {
                "type": "test_signal",
                "explanation": explanation.to_dict(),
            }
            routing_result = self.memory_controller.route(signal)

            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="module_interoperability",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"modules_used": 3},
        )

    def run_all_benchmarks(self) -> Sequence[BenchmarkResult]:
        """Run all integration benchmarks and return results."""
        results = []

        print("Running Integration benchmarks...")
        print(f"Iterations: {self.iterations}")
        print()

        results.append(self.benchmark_passport_to_audit_log())
        print(f"✓ Passport to audit log: {results[-1].avg_time_ms:.3f}ms avg")

        results.append(self.benchmark_search_to_causal())
        print(f"✓ Search to causal: {results[-1].avg_time_ms:.3f}ms avg")

        results.append(self.benchmark_memory_routing())
        print(f"✓ Memory routing: {results[-1].avg_time_ms:.3f}ms avg")

        results.append(self.benchmark_end_to_end_workflow())
        print(f"✓ End-to-end workflow: {results[-1].avg_time_ms:.3f}ms avg")

        results.append(self.benchmark_module_interoperability())
        print(f"✓ Module interoperability: {results[-1].avg_time_ms:.3f}ms avg")

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
            "benchmark_suite": "Integration",
            "timestamp": time.time(),
            "iterations": self.iterations,
            "results": [r.to_dict() for r in results],
            "summary": {
                "total_operations": len(results),
                "total_time_ms": sum(r.total_time_ms for r in results),
                "avg_throughput": sum(r.throughput_ops_per_sec for r in results)
                / len(results),
            },
        }

        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write auditable JSON output
        output_file.write_text(json.dumps(report_dict, indent=2))

        # Generate human-readable report
        lines = [
            "=" * 80,
            "INTEGRATION BENCHMARK REPORT",
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
        lines.append(
            f"Avg throughput: {report_dict['summary']['avg_throughput']:.1f} ops/sec"
        )
        lines.append("=" * 80)

        return "\n".join(lines)


def main():
    """Main entry point for benchmark script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Benchmark integration of all modules with auditable JSON output"
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
        default=Path("artifacts/integration_benchmark.json"),
        help="Output file for benchmark results (default: artifacts/integration_benchmark.json)",
    )

    args = parser.parse_args()

    # Run benchmarks
    benchmark = IntegrationBenchmark(iterations=args.iterations)
    results = benchmark.run_all_benchmarks()

    # Generate report
    report = benchmark.generate_benchmark_report(results, args.output)
    print()
    print(report)
    print()


if __name__ == "__main__":
    main()
