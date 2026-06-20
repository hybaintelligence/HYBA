#!/usr/bin/env python3
"""
Automated Benchmark Runner for CI/CD Pipeline

Executes benchmarks automatically on every commit, tracks performance
trends, and generates performance reports.
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import psutil


class AutomatedBenchmarkRunner:
    """Runs benchmarks automatically with performance tracking."""

    def __init__(self, benchmark_dir: str = "."):
        self.benchmark_dir = Path(benchmark_dir)
        self.results: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "git_commit": self._get_git_commit(),
            "benchmarks": {},
            "system_info": self._get_system_info(),
        }

    def _get_git_commit(self) -> str:
        """Get current git commit hash."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "unknown"

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_total_gb": psutil.virtual_memory().total / (1024 ** 3),
            "memory_available_gb": psutil.virtual_memory().available / (1024 ** 3),
            "python_version": sys.version,
        }

    def run_enterprise_benchmarks(self) -> Dict[str, Any]:
        """Run enterprise benchmark suite."""
        print("Running enterprise benchmarks...")
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "reproducibility/benchmarks/test_benchmark_suite.py",
                    "-v",
                    "--tb=short",
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )

            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": "Benchmark execution exceeded 5 minutes",
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def run_domain_benchmarks(self) -> Dict[str, Any]:
        """Run domain-specific benchmarks."""
        print("Running domain-specific benchmarks...")
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "reproducibility/benchmarks/advanced_benchmark_expansion.py",
                    "-v",
                    "--tb=short",
                ],
                capture_output=True,
                text=True,
                timeout=600,
            )

            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": "Domain benchmarks exceeded 10 minutes",
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def run_orchestrator_benchmarks(self) -> Dict[str, Any]:
        """Run benchmark orchestrator."""
        print("Running benchmark orchestrator...")
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "reproducibility/benchmarks/benchmark_orchestrator.py",
                    "-v",
                    "--tb=short",
                ],
                capture_output=True,
                text=True,
                timeout=600,
            )

            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": "Orchestrator benchmarks exceeded 10 minutes",
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def generate_report(self) -> str:
        """Generate markdown report of benchmark results."""
        report = []
        report.append("# Automated Benchmark Report\n")
        report.append(f"**Date**: {self.results['timestamp']}\n")
        report.append(f"**Commit**: `{self.results['git_commit']}`\n")
        report.append("## System Information\n")

        sys_info = self.results["system_info"]
        report.append(f"- **CPU Cores**: {sys_info['cpu_count']}\n")
        report.append(f"- **CPU Usage**: {sys_info['cpu_percent']:.1f}%\n")
        report.append(f"- **Memory Total**: {sys_info['memory_total_gb']:.2f} GB\n")
        report.append(f"- **Memory Available**: {sys_info['memory_available_gb']:.2f} GB\n")

        report.append("## Benchmark Results\n")

        for bench_name, result in self.results["benchmarks"].items():
            status = result.get("status", "unknown")
            emoji = "✅" if status == "passed" else "❌"
            report.append(f"### {emoji} {bench_name}\n")
            report.append(f"- **Status**: {status}\n")

            if "return_code" in result:
                report.append(f"- **Return Code**: {result['return_code']}\n")

            if "error" in result:
                report.append(f"- **Error**: {result['error']}\n")

        report.append("## Summary\n")

        total = len(self.results["benchmarks"])
        passed = sum(
            1 for r in self.results["benchmarks"].values() if r.get("status") == "passed"
        )

        report.append(f"- **Total Benchmarks**: {total}\n")
        report.append(f"- **Passed**: {passed}\n")
        report.append(f"- **Failed**: {total - passed}\n")

        return "".join(report)

    def save_results(self, output_file: str = "benchmark_results.json") -> None:
        """Save results to JSON file."""
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"Results saved to {output_file}")

    def run_all(self) -> int:
        """Run all benchmarks and return exit code."""
        print("Starting automated benchmark suite...\n")

        self.results["benchmarks"]["enterprise"] = self.run_enterprise_benchmarks()
        print()

        self.results["benchmarks"]["domain-specific"] = self.run_domain_benchmarks()
        print()

        self.results["benchmarks"]["orchestrator"] = (
            self.run_orchestrator_benchmarks()
        )
        print()

        # Generate report
        report = self.generate_report()
        print("\n" + report)

        # Save results
        self.save_results("benchmark_results.json")

        # Save report
        with open("BENCHMARK_REPORT.md", "w") as f:
            f.write(report)

        # Determine exit code
        all_passed = all(
            r.get("status") == "passed"
            for r in self.results["benchmarks"].values()
        )

        return 0 if all_passed else 1


def main():
    """Entry point for automated benchmark runner."""
    runner = AutomatedBenchmarkRunner()
    exit_code = runner.run_all()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
