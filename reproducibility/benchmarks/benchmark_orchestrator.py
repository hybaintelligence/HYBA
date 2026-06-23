"""
Benchmark Orchestrator - Enterprise Benchmark Execution & Validation Framework
Manages benchmark execution, result tracking, validation, and reporting
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import hashlib
import logging
from collections import defaultdict
import statistics
import numpy as np


# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BenchmarkStatus(Enum):
    """Benchmark execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATED = "validated"


class ValidationLevel(Enum):
    """Result validation levels"""

    NONE = 0
    BASIC = 1
    STATISTICAL = 2
    COMPREHENSIVE = 3


@dataclass
class BenchmarkRun:
    """Single benchmark run execution"""

    run_id: str
    benchmark_name: str
    domain: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: BenchmarkStatus = BenchmarkStatus.PENDING
    metrics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_seconds: float = 0.0
    validation_status: bool = False
    validation_details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["start_time"] = self.start_time.isoformat()
        data["end_time"] = self.end_time.isoformat() if self.end_time else None
        data["status"] = self.status.value
        return data

    def calculate_duration(self) -> float:
        """Calculate execution duration"""
        if self.end_time:
            self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        return self.duration_seconds


@dataclass
class BenchmarkComparison:
    """Comparison between two benchmark runs"""

    baseline_run: BenchmarkRun
    comparison_run: BenchmarkRun
    metric_changes: Dict[str, float] = field(default_factory=dict)
    percent_changes: Dict[str, float] = field(default_factory=dict)
    statistical_significance: Dict[str, Tuple[float, float]] = field(
        default_factory=dict
    )
    conclusion: str = ""

    def calculate_changes(self) -> None:
        """Calculate metric changes"""
        for metric in self.baseline_run.metrics:
            if metric in self.comparison_run.metrics:
                baseline_val = self.baseline_run.metrics[metric]
                comparison_val = self.comparison_run.metrics[metric]

                if isinstance(baseline_val, (int, float)) and baseline_val != 0:
                    change = comparison_val - baseline_val
                    percent_change = (change / baseline_val) * 100

                    self.metric_changes[metric] = change
                    self.percent_changes[metric] = percent_change


class BenchmarkValidator:
    """Validates benchmark results"""

    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STATISTICAL):
        self.validation_level = validation_level
        self.validation_rules = self._load_validation_rules()

    def _load_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load validation rules for different domains"""
        return {
            "quantum": {
                "fidelity_min": 0.9,
                "error_rate_max": 0.1,
                "coherence_time_min": 10.0,
            },
            "ml": {
                "accuracy_min": 0.7,
                "f1_score_min": 0.6,
                "inference_time_max": 1000.0,  # ms
            },
            "crypto": {
                "key_generation_min": 0.1,
                "throughput_min": 1.0,
                "security_level_min": 128,
            },
            "financial": {
                "return_min": -0.5,
                "return_max": 2.0,
                "sharpe_ratio_min": 0.5,
            },
        }

    def validate(self, run: BenchmarkRun) -> Tuple[bool, Dict[str, Any]]:
        """Validate a benchmark run"""
        validation_details = {
            "level": self.validation_level.name,
            "checks_performed": [],
            "checks_passed": 0,
            "checks_failed": 0,
            "errors": [],
        }

        # Basic validation
        if self.validation_level.value >= ValidationLevel.BASIC.value:
            validation_details["checks_performed"].append("basic_range_checks")
            passed, details = self._validate_basic(run)
            validation_details["checks_passed"] += passed
            validation_details["checks_failed"] += len(run.metrics) - passed
            validation_details.update(details)

        # Statistical validation
        if self.validation_level.value >= ValidationLevel.STATISTICAL.value:
            validation_details["checks_performed"].append("statistical_tests")
            passed, details = self._validate_statistical(run)
            validation_details["checks_passed"] += passed
            validation_details.update(details)

        # Comprehensive validation
        if self.validation_level.value >= ValidationLevel.COMPREHENSIVE.value:
            validation_details["checks_performed"].append("comprehensive_checks")
            passed, details = self._validate_comprehensive(run)
            validation_details["checks_passed"] += passed
            validation_details.update(details)

        overall_passed = validation_details["checks_failed"] == 0

        return overall_passed, validation_details

    def _validate_basic(self, run: BenchmarkRun) -> Tuple[int, Dict[str, Any]]:
        """Perform basic validation"""
        passed = 0
        details = {"basic_checks": {}}

        rules = self.validation_rules.get(run.domain, {})

        for metric, value in run.metrics.items():
            check_name = f"{metric}_check"

            if isinstance(value, (int, float)):
                # Check if value is within reasonable bounds
                if not np.isnan(value) and not np.isinf(value):
                    details["basic_checks"][check_name] = "passed"
                    passed += 1
                else:
                    details["basic_checks"][check_name] = "failed (invalid value)"
            else:
                details["basic_checks"][check_name] = "skipped (non-numeric)"

        return passed, details

    def _validate_statistical(self, run: BenchmarkRun) -> Tuple[int, Dict[str, Any]]:
        """Perform statistical validation"""
        passed = 0
        details = {"statistical_checks": {}}

        # Check for consistency (if metrics are arrays)
        for metric, value in run.metrics.items():
            if isinstance(value, list) and len(value) > 1:
                data = np.array(value)
                mean = np.mean(data)
                std = np.std(data)
                cv = std / mean if mean != 0 else 0  # Coefficient of variation

                # Low CV is better (less variance)
                check_name = f"{metric}_cv_check"
                if cv < 0.5:  # Less than 50% variation
                    details["statistical_checks"][check_name] = f"passed (CV={cv:.2f})"
                    passed += 1
                else:
                    details["statistical_checks"][
                        check_name
                    ] = f"warning (high CV={cv:.2f})"

        return passed, details

    def _validate_comprehensive(self, run: BenchmarkRun) -> Tuple[int, Dict[str, Any]]:
        """Perform comprehensive validation"""
        passed = 0
        details = {"comprehensive_checks": {}}

        # Check relationships between metrics
        if run.domain == "ml":
            if "precision" in run.metrics and "recall" in run.metrics:
                precision = run.metrics["precision"]
                recall = run.metrics["recall"]

                # F1 should be harmonic mean
                if precision > 0 and recall > 0:
                    expected_f1 = 2 * (precision * recall) / (precision + recall)
                    if "f1_score" in run.metrics:
                        actual_f1 = run.metrics["f1_score"]
                        if abs(actual_f1 - expected_f1) < 0.01:
                            details["comprehensive_checks"]["f1_consistency"] = "passed"
                            passed += 1

        return passed, details


class BenchmarkOrchestrator:
    """Orchestrates benchmark execution, tracking, and reporting"""

    def __init__(self, output_dir: str = "benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.runs: List[BenchmarkRun] = []
        self.comparisons: List[BenchmarkComparison] = []
        self.validator = BenchmarkValidator(ValidationLevel.COMPREHENSIVE)

        logger.info(f"Benchmark Orchestrator initialized. Output: {self.output_dir}")

    def schedule_benchmark(
        self,
        benchmark_func: Callable,
        benchmark_name: str,
        domain: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> BenchmarkRun:
        """Schedule a benchmark for execution"""
        run_id = self._generate_run_id()
        run = BenchmarkRun(
            run_id=run_id,
            benchmark_name=benchmark_name,
            domain=domain,
            start_time=datetime.now(),
        )

        logger.info(f"Scheduled benchmark: {benchmark_name} (ID: {run_id})")
        return run

    def execute_benchmark(
        self,
        benchmark_func: Callable,
        benchmark_name: str,
        domain: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> BenchmarkRun:
        """Execute a single benchmark"""
        run = self.schedule_benchmark(
            benchmark_func, benchmark_name, domain, parameters
        )
        run.status = BenchmarkStatus.RUNNING

        try:
            logger.info(f"Executing: {benchmark_name}")
            start = time.time()

            # Execute benchmark function
            if parameters:
                result = benchmark_func(**parameters)
            else:
                result = benchmark_func()

            duration = time.time() - start

            # Extract metrics
            if isinstance(result, dict):
                run.metrics = result
            elif hasattr(result, "__dict__"):
                run.metrics = result.__dict__
            else:
                run.metrics = {"result": result}

            run.end_time = datetime.now()
            run.duration_seconds = duration
            run.status = BenchmarkStatus.COMPLETED

            # Validate results
            validated, validation_details = self.validator.validate(run)
            run.validation_status = validated
            run.validation_details = validation_details

            if validated:
                run.status = BenchmarkStatus.VALIDATED
                logger.info(f"✅ Benchmark completed and validated: {benchmark_name}")
            else:
                logger.warning(
                    f"⚠️  Benchmark completed but validation failed: {benchmark_name}"
                )

        except Exception as e:
            run.status = BenchmarkStatus.FAILED
            run.error = str(e)
            run.end_time = datetime.now()
            logger.error(f"❌ Benchmark failed: {benchmark_name} - {str(e)}")

        self.runs.append(run)
        return run

    def execute_suite(
        self, benchmarks: Dict[str, Callable], domain: str
    ) -> List[BenchmarkRun]:
        """Execute a suite of benchmarks"""
        logger.info(f"Executing benchmark suite for domain: {domain}")

        results = []
        for bench_name, bench_func in benchmarks.items():
            run = self.execute_benchmark(bench_func, bench_name, domain)
            results.append(run)

        logger.info(f"Suite completed: {len(results)} benchmarks executed")
        return results

    def compare_runs(
        self, run1: BenchmarkRun, run2: BenchmarkRun
    ) -> BenchmarkComparison:
        """Compare two benchmark runs"""
        comparison = BenchmarkComparison(run1, run2)
        comparison.calculate_changes()

        # Generate conclusion
        if comparison.percent_changes:
            avg_improvement = statistics.mean(comparison.percent_changes.values())
            if avg_improvement > 10:
                comparison.conclusion = (
                    f"Run 2 is {avg_improvement:.1f}% better than Run 1"
                )
            elif avg_improvement < -10:
                comparison.conclusion = (
                    f"Run 1 is {-avg_improvement:.1f}% better than Run 2"
                )
            else:
                comparison.conclusion = "No significant difference between runs"

        self.comparisons.append(comparison)
        logger.info(f"Comparison generated: {comparison.conclusion}")

        return comparison

    def generate_report(self) -> str:
        """Generate comprehensive benchmark report"""
        report = "BENCHMARK EXECUTION REPORT\n"
        report += "=" * 80 + "\n"
        report += f"Generated: {datetime.now().isoformat()}\n"
        report += f"Total Benchmarks: {len(self.runs)}\n"
        report += f"Passed: {sum(1 for r in self.runs if r.validation_status)}\n"
        report += f"Failed: {sum(1 for r in self.runs if not r.validation_status)}\n"
        report += "\n"

        # Group by domain
        by_domain = defaultdict(list)
        for run in self.runs:
            by_domain[run.domain].append(run)

        for domain, runs in by_domain.items():
            report += f"\n{domain.upper()} DOMAIN\n"
            report += "-" * 40 + "\n"

            for run in runs:
                report += f"\nBenchmark: {run.benchmark_name}\n"
                report += f"  ID: {run.run_id}\n"
                report += f"  Status: {run.status.value}\n"
                report += f"  Duration: {run.duration_seconds:.2f}s\n"
                report += f"  Validated: {run.validation_status}\n"

                if run.metrics:
                    report += "  Metrics:\n"
                    for metric, value in run.metrics.items():
                        report += f"    {metric}: {value}\n"

                if run.error:
                    report += f"  Error: {run.error}\n"

        return report

    def export_results(self, format: str = "json") -> str:
        """Export results in specified format"""
        if format == "json":
            data = {
                "timestamp": datetime.now().isoformat(),
                "total_runs": len(self.runs),
                "runs": [run.to_dict() for run in self.runs],
                "comparisons": [
                    {
                        "baseline": self.comparisons.index(c),
                        "comparison": self.comparisons.index(c) + 1,
                        "metric_changes": c.metric_changes,
                        "percent_changes": c.percent_changes,
                        "conclusion": c.conclusion,
                    }
                    for c in self.comparisons
                ],
            }

            output_file = (
                self.output_dir
                / f'benchmarks_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            )
            with open(output_file, "w") as f:
                json.dump(data, f, indent=2, default=str)

            logger.info(f"Results exported to: {output_file}")
            return str(output_file)

        return ""

    def _generate_run_id(self) -> str:
        """Generate unique run ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        run_num = len(self.runs) + 1
        return f"run_{run_num}_{timestamp}"

    def save_summary(self) -> None:
        """Save execution summary"""
        summary = {
            "execution_time": datetime.now().isoformat(),
            "total_benchmarks": len(self.runs),
            "total_duration_s": sum(r.duration_seconds for r in self.runs),
            "validation_rate": (
                sum(1 for r in self.runs if r.validation_status) / len(self.runs)
                if self.runs
                else 0
            ),
            "by_domain": {},
        }

        by_domain = defaultdict(list)
        for run in self.runs:
            by_domain[run.domain].append(run)

        for domain, runs in by_domain.items():
            summary["by_domain"][domain] = {
                "count": len(runs),
                "passed": sum(1 for r in runs if r.validation_status),
                "avg_duration_s": (
                    statistics.mean(r.duration_seconds for r in runs) if runs else 0
                ),
            }

        summary_file = self.output_dir / "benchmark_summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Summary saved to: {summary_file}")


# Example usage
if __name__ == "__main__":
    orchestrator = BenchmarkOrchestrator(output_dir="./benchmark_results")

    # Define some benchmark functions
    def bench_fast():
        time.sleep(0.1)
        return {"duration": 0.1, "throughput": 1000}

    def bench_slow():
        time.sleep(1.0)
        return {"duration": 1.0, "throughput": 100}

    # Execute benchmarks
    run1 = orchestrator.execute_benchmark(bench_fast, "fast_op", "ml")
    run2 = orchestrator.execute_benchmark(bench_slow, "slow_op", "ml")

    # Compare results
    comparison = orchestrator.compare_runs(run1, run2)

    # Generate and print report
    report = orchestrator.generate_report()
    print(report)

    # Export results
    orchestrator.export_results("json")
    orchestrator.save_summary()

    print("\n✅ Benchmark orchestration completed!")
