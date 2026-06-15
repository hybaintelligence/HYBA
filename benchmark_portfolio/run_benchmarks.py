#!/usr/bin/env python3
"""
HYBA Φ-Trifecta Comprehensive Benchmark Suite

Runs evidence-collection scripts and compiles the results into a single
benchmark portfolio report.

Evidence-first guardrail: this runner fails before executing long or networked
benchmarks when the active Python interpreter is missing required packages. Run
it through the project virtual environment or npm gate, not the system Python.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
OUTPUT_DIR = ROOT / "benchmark_portfolio" / "run_output"
REQUIRED_IMPORTS = ("numpy",)


def banner(text: str) -> None:
    line = "━" * 72
    print(f"\n{line}")
    print(f"  {text}")
    print(f"{line}\n")


def environment_status() -> dict[str, object]:
    missing = [name for name in REQUIRED_IMPORTS if importlib.util.find_spec(name) is None]
    return {
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "required_imports": list(REQUIRED_IMPORTS),
        "missing_imports": missing,
        "status": "ready" if not missing else "blocked",
    }


def fail_fast_environment() -> None:
    status = environment_status()
    if status["status"] == "ready":
        return
    print(json.dumps({"benchmark_environment": status}, indent=2, sort_keys=True))
    print("\nBenchmark runner blocked before execution: active Python is missing required imports.")
    print("Use the project virtual environment, for example:")
    print("  source .venv/bin/activate")
    print("  python benchmark_portfolio/run_benchmarks.py --quick")
    raise SystemExit(2)


def run_script(script_name: str, extra_args: list[str] | None = None, timeout: int = 600) -> dict[str, object]:
    script_path = SCRIPTS / script_name
    if not script_path.exists():
        return {
            "script": script_name,
            "status": "SKIPPED",
            "error": f"Script not found: {script_path}",
            "stdout": "",
            "stderr": "",
            "duration_s": 0,
        }

    cmd = [sys.executable, str(script_path)]
    if extra_args:
        cmd.extend(extra_args)

    print(f"  Running: {' '.join(cmd)}")
    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(ROOT))
        duration = time.time() - start
        status = "PASSED" if result.returncode == 0 else "FAILED"
        print(f"  Status: {status} ({duration:.1f}s)")
        if result.returncode != 0:
            print(f"  stderr: {result.stderr[:500]}")
        return {
            "script": script_name,
            "status": status,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration_s": round(duration, 2),
        }
    except subprocess.TimeoutExpired:
        return {
            "script": script_name,
            "status": "TIMEOUT",
            "error": f"Exceeded {timeout}s timeout",
            "stdout": "",
            "stderr": "",
            "duration_s": timeout,
        }


def collect_artifact(path: str) -> dict[str, object]:
    full_path = ROOT / path
    if full_path.exists():
        try:
            with open(full_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            return {"error": str(exc)}
    return {"error": f"Not found: {path}"}


def artifact_key(path: str) -> str:
    return path.replace("artifacts/", "").replace("/", "__")


def first_artifact(artifacts: dict[str, object], suffix: str) -> dict[str, object]:
    for key, value in artifacts.items():
        if key.endswith(suffix) and isinstance(value, dict) and "error" not in value:
            return value
    return {}


def portfolio_report(results: list[dict[str, object]], artifacts: dict[str, object], run_mode: str) -> dict[str, object]:
    passed = sum(1 for r in results if r["status"] == "PASSED")
    failed = sum(1 for r in results if r["status"] == "FAILED")
    skipped = sum(1 for r in results if r["status"] == "SKIPPED")
    timed_out = sum(1 for r in results if r["status"] == "TIMEOUT")
    total_time = sum(float(r["duration_s"]) for r in results)

    quantum_math = first_artifact(artifacts, "quantum_mathematics_final_verification.json")
    structured_search = first_artifact(artifacts, "structured_search_comparison.json")
    phi_resonance = first_artifact(artifacts, "phi_resonance_summary.json")
    hash_validity = first_artifact(artifacts, "phi_hash_correlation_summary.json")
    stack = first_artifact(artifacts, "complete_stack_analysis.json")

    resonance_summary = phi_resonance.get("summary", {}) if isinstance(phi_resonance.get("summary"), dict) else phi_resonance
    stack_summary = stack.get("summary", {}) if isinstance(stack.get("summary"), dict) else stack

    return {
        "portfolio_title": "HYBA Φ-Trifecta Benchmark Portfolio",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_repository": "HYBA_FULLSTACK",
        "run_mode": run_mode,
        "benchmark_environment": environment_status(),
        "scripts_results": results,
        "summary": {
            "total_scripts": len(results),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "timed_out": timed_out,
            "total_duration_s": round(total_time, 2),
            "pass_rate": f"{passed / max(len(results) - skipped, 1) * 100:.1f}%",
            "all_scripts_passed": failed == 0 and timed_out == 0 and skipped == 0,
        },
        "key_metrics": {
            "quantum_math_tests": quantum_math.get("total_tests", "N/A"),
            "quantum_math_passed": quantum_math.get("passed", "N/A"),
            "quantum_math_pass_rate": quantum_math.get("pass_rate", "N/A"),
            "structured_search_strategies": (
                [s["name"] for s in structured_search.get("strategies", [])]
                if "strategies" in structured_search else []
            ),
            "phi_resonance_rate": resonance_summary.get("phi_resonance_rate", resonance_summary.get("resonance_rate", "N/A")),
            "phi_resonance_z_score": resonance_summary.get("z_score_vs_random", resonance_summary.get("z_score", "N/A")),
            "hash_validity_correlation": hash_validity.get("correlation", hash_validity.get("r", "N/A")),
            "structured_advantage_over_grover": stack_summary.get("advantage_over_grover", stack_summary.get("grover_advantage", "N/A")),
        },
        "evidence_artifacts_included": list(artifacts.keys()),
        "evidence_boundary": {
            "partial_reports_are_not_acceptance_evidence": True,
            "failed_scripts_block_portfolio_gate": True,
            "quick_mode_is_smoke_evidence_only": run_mode == "quick_smoke",
        },
    }


def write_markdown_summary(md_path: Path, portfolio: dict[str, object]) -> None:
    summary = portfolio["summary"]
    metrics = portfolio["key_metrics"]
    results = portfolio["scripts_results"]
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# HYBA Φ-Trifecta Benchmark Portfolio\n\n")
        f.write(f"**Generated:** {portfolio['generated_at']}\n\n")
        f.write(f"**Run mode:** `{portfolio['run_mode']}`\n\n")
        f.write("## Executive Summary\n\n")
        f.write(f"- **Scripts executed:** {summary['total_scripts']}\n")
        f.write(f"- **Passed:** {summary['passed']}\n")
        f.write(f"- **Failed:** {summary['failed']}\n")
        f.write(f"- **Timed out:** {summary['timed_out']}\n")
        f.write(f"- **Skipped:** {summary['skipped']}\n")
        f.write(f"- **Pass rate:** {summary['pass_rate']}\n")
        f.write(f"- **All scripts passed:** {summary['all_scripts_passed']}\n")
        f.write(f"- **Total duration:** {summary['total_duration_s']}s\n\n")
        f.write("## Key Metrics\n\n")
        f.write("| Metric | Value |\n|---|---|\n")
        f.write(f"| Quantum math verification | {metrics.get('quantum_math_passed', '?')}/{metrics.get('quantum_math_tests', '?')} |\n")
        f.write(f"| Φ¹⁵ block resonance rate | {metrics.get('phi_resonance_rate', '?')} |\n")
        f.write(f"| Z-score vs random | {metrics.get('phi_resonance_z_score', '?')} |\n")
        f.write(f"| Hash-validity correlation | {metrics.get('hash_validity_correlation', '?')} |\n")
        f.write(f"| Structured advantage over Grover | {metrics.get('structured_advantage_over_grover', '?')} |\n")
        f.write(f"| Strategies | {', '.join(metrics.get('structured_search_strategies', []))} |\n\n")
        f.write("## Script Results\n\n")
        f.write("| Script | Status | Duration |\n|---|---|---|\n")
        for item in results:
            f.write(f"| {item['script']} | {item['status']} | {item['duration_s']}s |\n")
        f.write("\n## Evidence Boundary\n\n")
        f.write("Partial reports are smoke evidence only. A portfolio is acceptance-grade only when all scripts pass.\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="HYBA Φ-Trifecta Benchmark Suite")
    parser.add_argument("--quick", action="store_true", help="Run reduced iterations")
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    fail_fast_environment()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_mode = "quick_smoke" if args.quick else "full"

    print("\n" + "=" * 72)
    print("     HYBA Φ-TRIFECTA COMPREHENSIVE BENCHMARK SUITE")
    print("     Quantum Mathematics · Memory Folding · Golden Ratio Scaling")
    print("=" * 72)

    banner("1/6  Quantum Mathematics Verification")
    r1 = run_script("quantum_math_final_verification.py")

    banner("2/6  Structured Search Comparison (HENDRIX-Φ vs baselines)")
    r2 = run_script("phi_structured_search_demonstration.py", ["--steps", "10" if args.quick else "50000"])

    banner("3/6  Φ¹⁵ Resonance in Bitcoin Blocks")
    r3 = run_script("collect_100_blocks.py", ["10" if args.quick else "100"])

    banner("4/6  Hash Validity Correlation")
    r4 = run_script("phi_hash_validity_correlation.py")

    banner("5/6  Quantum Performance Benchmarks")
    r5 = run_script("benchmark_quantum.py", ["10" if args.quick else "100"])

    banner("6/6  Full Stack Analysis")
    r6 = run_script("phi_complete_stack_analysis.py")

    all_results = [r1, r2, r3, r4, r5, r6]

    banner("Collecting Evidence Artifacts")
    artifact_paths = [
        "artifacts/quantum_mathematics_final_verification.json",
        "artifacts/quantum_mathematics_verification_report.json",
        "artifacts/phi_structured_search_final/structured_search_comparison.json",
        "artifacts/phi_resonance_100blocks/phi_resonance_summary.json",
        "artifacts/phi_resonance_final/phi_resonance_summary.json",
        "artifacts/phi_hash_validity_final/phi_hash_correlation_summary.json",
        "artifacts/phi_stack_final/complete_stack_analysis.json",
        "artifacts/production_validation_report.json",
    ]
    collected: dict[str, object] = {}
    for path in artifact_paths:
        data = collect_artifact(path)
        key = artifact_key(path)
        collected[key] = data
        print(f"  {key}: {'✓' if 'error' not in data else '✗'}")

    banner("Compiling Portfolio Report")
    portfolio = portfolio_report(all_results, collected, run_mode=run_mode)

    report_path = output_dir / "portfolio_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(portfolio, f, indent=2, default=str)
    print(f"  Report written to: {report_path}")

    summary = portfolio["summary"]
    metrics = portfolio["key_metrics"]
    print("\n" + "=" * 72)
    print("  BENCHMARK PORTFOLIO SUMMARY")
    print("=" * 72)
    print(f"  Scripts run:      {summary['total_scripts']}")
    print(f"  Passed:           {summary['passed']}")
    print(f"  Failed:           {summary['failed']}")
    print(f"  Timed out:        {summary['timed_out']}")
    print(f"  Skipped:          {summary['skipped']}")
    print(f"  Pass rate:        {summary['pass_rate']}")
    print(f"  Total duration:   {summary['total_duration_s']}s")
    print()
    print(f"  Quantum math:     {metrics.get('quantum_math_passed', '?')}/{metrics.get('quantum_math_tests', '?')} tests passed")
    print(f"  Φ resonance:      {metrics.get('phi_resonance_rate', '?')} of blocks")
    print(f"  Z-score:          {metrics.get('phi_resonance_z_score', '?')}")
    print(f"  Hash boundary r:  {metrics.get('hash_validity_correlation', '?')}")
    print(f"  Grover advantage: {metrics.get('structured_advantage_over_grover', '?')}")
    print()
    print(f"  Strategies compared: {metrics.get('structured_search_strategies', [])}")

    if summary["failed"] > 0 or summary["timed_out"] > 0 or summary["skipped"] > 0:
        print("\n  ⚠  INCOMPLETE BENCHMARK RUN:")
        for item in all_results:
            if item["status"] != "PASSED":
                print(f"     - {item['script']}: {item['status']} returncode={item.get('returncode')}")
                if item.get("stderr"):
                    print(f"       {str(item['stderr'])[:200]}")
        print("\n  This report is smoke/diagnostic evidence only until all scripts pass.")

    md_path = output_dir / "PORTFOLIO_SUMMARY.md"
    write_markdown_summary(md_path, portfolio)
    print(f"\n  Markdown summary: {md_path}")
    print("=" * 72)

    return 0 if summary["all_scripts_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
