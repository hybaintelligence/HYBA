#!/usr/bin/env python3
"""
Distributed Benchmark Executor

Enables parallel execution of benchmarks across multiple nodes or processes,
with result aggregation and performance optimization.
"""

import asyncio
import json
import multiprocessing
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


@dataclass
class BenchmarkTask:
    """Represents a single benchmark task."""

    name: str
    function: Callable
    args: tuple = ()
    kwargs: Dict[str, Any] = None
    timeout: int = 300

    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}


@dataclass
class BenchmarkResult:
    """Result from a benchmark execution."""

    task_name: str
    status: str
    duration_seconds: float
    start_time: str
    end_time: str
    error: Optional[str] = None
    return_value: Optional[Any] = None


class DistributedBenchmarkExecutor:
    """Executes benchmarks in parallel across multiple processes."""

    def __init__(self, num_workers: Optional[int] = None):
        """Initialize executor with specified number of workers."""
        self.num_workers = num_workers or multiprocessing.cpu_count()
        self.results: List[BenchmarkResult] = []
        self.tasks: List[BenchmarkTask] = []

    def add_task(
        self,
        name: str,
        function: Callable,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        timeout: int = 300,
    ) -> None:
        """Add a benchmark task to the queue."""
        if kwargs is None:
            kwargs = {}

        task = BenchmarkTask(
            name=name,
            function=function,
            args=args,
            kwargs=kwargs,
            timeout=timeout,
        )
        self.tasks.append(task)

    def _execute_task(self, task: BenchmarkTask) -> BenchmarkResult:
        """Execute a single task and return result."""
        start_time = datetime.utcnow()
        start_timestamp = start_time.isoformat()

        try:
            # Execute function with timeout
            result = asyncio.run(
                self._run_with_timeout(task.function, task.args, task.kwargs, task.timeout)
            )

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            return BenchmarkResult(
                task_name=task.name,
                status="passed",
                duration_seconds=duration,
                start_time=start_timestamp,
                end_time=end_time.isoformat(),
                return_value=result,
            )

        except asyncio.TimeoutError:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            return BenchmarkResult(
                task_name=task.name,
                status="timeout",
                duration_seconds=duration,
                start_time=start_timestamp,
                end_time=end_time.isoformat(),
                error=f"Task exceeded {task.timeout}s timeout",
            )

        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            return BenchmarkResult(
                task_name=task.name,
                status="failed",
                duration_seconds=duration,
                start_time=start_timestamp,
                end_time=end_time.isoformat(),
                error=str(e),
            )

    async def _run_with_timeout(
        self,
        func: Callable,
        args: tuple,
        kwargs: Dict[str, Any],
        timeout: int,
    ) -> Any:
        """Run function with timeout."""
        loop = asyncio.get_event_loop()

        async def run():
            return await loop.run_in_executor(
                None,
                lambda: func(*args, **kwargs),
            )

        return await asyncio.wait_for(run(), timeout=timeout)

    def execute_sequential(self) -> List[BenchmarkResult]:
        """Execute benchmarks sequentially."""
        print(f"Executing {len(self.tasks)} tasks sequentially...")

        for i, task in enumerate(self.tasks, 1):
            print(f"[{i}/{len(self.tasks)}] Executing {task.name}...")
            result = self._execute_task(task)
            self.results.append(result)
            print(f"  Status: {result.status} ({result.duration_seconds:.2f}s)")

        return self.results

    def execute_parallel(self) -> List[BenchmarkResult]:
        """Execute benchmarks in parallel."""
        print(f"Executing {len(self.tasks)} tasks in parallel with {self.num_workers} workers...")

        with multiprocessing.Pool(processes=self.num_workers) as pool:
            self.results = pool.map(self._execute_task, self.tasks)

        return self.results

    def execute_optimal(self) -> List[BenchmarkResult]:
        """Choose optimal execution strategy."""
        if len(self.tasks) <= 3:
            return self.execute_sequential()
        else:
            return self.execute_parallel()

    def generate_report(self) -> Dict[str, Any]:
        """Generate execution report."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "num_workers": self.num_workers,
            "total_tasks": len(self.tasks),
            "results": [],
            "summary": {},
        }

        for result in self.results:
            report["results"].append({
                "task_name": result.task_name,
                "status": result.status,
                "duration_seconds": result.duration_seconds,
                "start_time": result.start_time,
                "end_time": result.end_time,
                "error": result.error,
            })

        # Calculate summary
        total_duration = sum(r.duration_seconds for r in self.results)
        passed = sum(1 for r in self.results if r.status == "passed")
        failed = sum(1 for r in self.results if r.status == "failed")
        timeout = sum(1 for r in self.results if r.status == "timeout")

        report["summary"] = {
            "total_duration_seconds": total_duration,
            "passed": passed,
            "failed": failed,
            "timeout": timeout,
            "pass_rate": (passed / len(self.results) * 100) if self.results else 0,
        }

        return report

    def save_report(self, output_file: str = "distributed_execution_report.json") -> None:
        """Save execution report to file."""
        report = self.generate_report()

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"Report saved to {output_file}")

    def print_summary(self) -> None:
        """Print execution summary."""
        report = self.generate_report()
        summary = report["summary"]

        print("\n" + "=" * 60)
        print("DISTRIBUTED BENCHMARK EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Total Duration: {summary['total_duration_seconds']:.2f}s")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Timeout: {summary['timeout']}")
        print(f"Pass Rate: {summary['pass_rate']:.1f}%")
        print("=" * 60 + "\n")


# Example benchmark functions
def cpu_benchmark(duration: int = 5) -> float:
    """Simple CPU benchmark."""
    start = time.time()
    count = 0

    while time.time() - start < duration:
        count += sum(range(100))

    return count


def memory_benchmark(size_mb: int = 100) -> int:
    """Memory allocation benchmark."""
    data = bytearray(size_mb * 1024 * 1024)
    return len(data)


def io_benchmark(num_files: int = 100) -> int:
    """File I/O benchmark."""
    import tempfile

    created = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(num_files):
            filepath = Path(tmpdir) / f"test_{i}.txt"
            filepath.write_text(f"Test data {i}" * 100)
            created += 1

    return created


def main():
    """Example usage."""
    executor = DistributedBenchmarkExecutor(num_workers=4)

    # Add benchmark tasks
    executor.add_task("cpu_benchmark_1", cpu_benchmark, args=(2,))
    executor.add_task("cpu_benchmark_2", cpu_benchmark, args=(2,))
    executor.add_task("memory_benchmark", memory_benchmark, args=(50,))
    executor.add_task("io_benchmark", io_benchmark, args=(50,))

    # Execute benchmarks
    results = executor.execute_optimal()

    # Print summary
    executor.print_summary()

    # Save report
    executor.save_report()


if __name__ == "__main__":
    main()
