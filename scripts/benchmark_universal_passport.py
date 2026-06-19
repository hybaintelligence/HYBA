"""Benchmark script for UniversalPassport module with auditable JSON output.

This script benchmarks the UniversalPassport module performance and generates
auditable JSON output for reproducible evidence.

Benchmarks:
1. Passport creation performance
2. Hash computation performance
3. Verification performance
4. Audit log append performance
5. Serialization/deserialization performance
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from python_backend.core.audit.universal_passport import (
    ClaimType,
    EpistemicBound,
    SharedAuditLog,
    Subsystem,
    UniversalPassport,
    make_circuit_breaker_passport,
    make_mining_passport,
    make_mode_transition_passport,
    make_passport,
    make_phi_measurement_passport,
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


class UniversalPassportBenchmark:
    """Benchmark suite for UniversalPassport module."""

    def __init__(self, iterations: int = 1000):
        """Initialize the benchmark suite.

        Args:
            iterations: Number of iterations for each benchmark
        """
        self.iterations = int(iterations)

    def benchmark_passport_creation(self) -> BenchmarkResult:
        """Benchmark passport creation performance."""
        times = []

        for _ in range(self.iterations):
            start = time.perf_counter()
            passport = make_passport(
                subsystem=Subsystem.PYTHIA.value,
                claim_type=ClaimType.NONCE_FOUND.value,
                payload={"nonce": 12345, "job_id": "test_job"},
                epistemic_bounds=[EpistemicBound.NO_QUANTUM_SPEEDUP.value],
            )
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="passport_creation",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"passport_type": "standard"},
        )

    def benchmark_hash_computation(self) -> BenchmarkResult:
        """Benchmark hash computation performance."""
        times = []

        for _ in range(self.iterations):
            start = time.perf_counter()
            passport = make_passport(
                subsystem=Subsystem.PYTHIA.value,
                claim_type=ClaimType.NONCE_FOUND.value,
                payload={"nonce": 12345, "job_id": "test_job"},
                epistemic_bounds=[EpistemicBound.NO_QUANTUM_SPEEDUP.value],
            )
            # Hash is computed during passport creation, so this measures that
            _ = passport.embedded_hash
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="hash_computation",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"hash_algorithm": "SHA-256"},
        )

    def benchmark_verification(self) -> BenchmarkResult:
        """Benchmark passport verification performance."""
        # Create a passport to verify
        passport = make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.NONCE_FOUND.value,
            payload={"nonce": 12345, "job_id": "test_job"},
            epistemic_bounds=[EpistemicBound.NO_QUANTUM_SPEEDUP.value],
        )

        times = []

        for _ in range(self.iterations):
            start = time.perf_counter()
            is_valid = passport.verify()
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="verification",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"verification_result": is_valid},
        )

    def benchmark_audit_log_append(self) -> BenchmarkResult:
        """Benchmark audit log append performance."""
        audit_log = SharedAuditLog()
        times = []

        for i in range(self.iterations):
            passport = make_passport(
                subsystem=Subsystem.PYTHIA.value,
                claim_type=ClaimType.NONCE_FOUND.value,
                payload={"nonce": i, "job_id": "test_job"},
                epistemic_bounds=[EpistemicBound.NO_QUANTUM_SPEEDUP.value],
            )
            start = time.perf_counter()
            audit_log.append(passport)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="audit_log_append",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"final_log_size": len(audit_log.get_entries())},
        )

    def benchmark_serialization(self) -> BenchmarkResult:
        """Benchmark passport serialization/deserialization performance."""
        passport = make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.NONCE_FOUND.value,
            payload={"nonce": 12345, "job_id": "test_job"},
            epistemic_bounds=[EpistemicBound.NO_QUANTUM_SPEEDUP.value],
        )

        times = []

        for _ in range(self.iterations):
            start = time.perf_counter()
            # Serialize
            passport_dict = passport.to_dict()
            json_str = json.dumps(passport_dict)
            # Deserialize
            deserialized = json.loads(json_str)
            end = time.perf_counter()
            times.append((end - start) * 1000)

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = self.iterations / (total_time / 1000)

        return BenchmarkResult(
            operation="serialization",
            iterations=self.iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_ops_per_sec=throughput,
            metadata={"serialization_format": "JSON"},
        )

    def run_all_benchmarks(self) -> Sequence[BenchmarkResult]:
        """Run all benchmarks and return results."""
        results = []

        print("Running UniversalPassport benchmarks...")
        print(f"Iterations: {self.iterations}")
        print()

        results.append(self.benchmark_passport_creation())
        print(f"✓ Passport creation: {results[-1].avg_time_ms:.3f}ms avg")

        results.append(self.benchmark_hash_computation())
        print(f"✓ Hash computation: {results[-1].avg_time_ms:.3f}ms avg")

        results.append(self.benchmark_verification())
        print(f"✓ Verification: {results[-1].avg_time_ms:.3f}ms avg")

        results.append(self.benchmark_audit_log_append())
        print(f"✓ Audit log append: {results[-1].avg_time_ms:.3f}ms avg")

        results.append(self.benchmark_serialization())
        print(f"✓ Serialization: {results[-1].avg_time_ms:.3f}ms avg")

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
            "benchmark_suite": "UniversalPassport",
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
            "UNIVERSAL PASSPORT BENCHMARK REPORT",
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
        description="Benchmark UniversalPassport module with auditable JSON output"
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
        default=Path("artifacts/universal_passport_benchmark.json"),
        help="Output file for benchmark results (default: artifacts/universal_passport_benchmark.json)",
    )

    args = parser.parse_args()

    # Run benchmarks
    benchmark = UniversalPassportBenchmark(iterations=args.iterations)
    results = benchmark.run_all_benchmarks()

    # Generate report
    report = benchmark.generate_benchmark_report(results, args.output)
    print()
    print(report)
    print()


if __name__ == "__main__":
    main()
