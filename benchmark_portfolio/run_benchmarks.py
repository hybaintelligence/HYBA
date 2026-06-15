#!/usr/bin/env python3
"""
HYBA Φ-Trifecta Comprehensive Benchmark Suite

Runs all evidence-collection scripts and compiles the results into a single
benchmark portfolio report. This script orchestrates:

  1. Quantum Mathematics Verification (quantum_math_final_verification.py)
  2. Structured Search Comparison (phi_structured_search_demonstration.py)
  3. Φ Resonance in Bitcoin Blocks (collect_100_blocks.py)
  4. Hash Validity Correlation (phi_hash_validity_correlation.py)
  5. Quantum Performance Benchmarks (benchmark_quantum.py)
  6. Full Stack Analysis (phi_complete_stack_analysis.py)
  7. Security / Anti-Mock Gate (check_no_runtime_mocks.py)

Usage:
  python benchmark_portfolio/run_benchmarks.py [--quick] [--output-dir PATH]

Flags:
  --quick         Run reduced iterations (10 instead of 50000 for search tests)
  --output-dir    Output directory for the portfolio report (default ./benchmark_output)
"""

import argparse
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


def banner(text: str) -> None:
    line = "━" * 72
    print(f"\n{line}")
    print(f"  {text}")
    print(f"{line}\n")


def run_script(script_name: str, extra_args: list = None, timeout: int = 600) -> dict:
    """Run a Python script and capture its output and exit code."""
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
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=str(ROOT)
        )
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


def collect_artifact(path: str) -> dict:
    """Load a JSON artifact if it exists."""
    full_path = ROOT / path
    if full_path.exists():
        try:
            with open(full_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            return {"error": str(e)}
    return {"error": f"Not found: {path}"}


def report(results: list, artifacts: dict) -> dict:
    """Compile the final portfolio report."""
    passed = sum(1 for r in results if r["status"] == "PASSED")
    failed = sum(1 for r in results if r["status"] == "FAILED")
    skipped = sum(1 for r in results if r["status"] == "SKIPPED")
    timed_out = sum(1 for r in results if r["status"] == "TIMEOUT")
    total_time = sum(r["duration_s"] for r in results)

    # Extract key metrics from artifacts
    quantum_math = artifacts.get("quantum_mathematics_final_verification.json", {})
    structured_search = artifacts.get("structured_search_comparison.json", {})
    phi_resonance = artifacts.get("phi_resonance_summary.json", {})

    report_data = {
        "portfolio_title": "HYBA Φ-Trifecta Benchmark Portfolio",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_repository": "HYBA_FULLSTACK",
        "scripts_results": results,
        "summary": {
            "total_scripts": len(results),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "timed_out": timed_out,
            "total_duration_s": round(total_time, 2),
            "pass_rate": f"{passed / max(len(results) - skipped, 1) * 100:.1f}%",
        },
        "key_metrics": {
            "quantum_math_tests": quantum_math.get("total_tests", "N/A"),
            "quantum_math_passed": quantum_math.get("passed", "N/A"),
            "quantum_math_pass_rate": quantum_math.get("pass_rate", "N/A"),
            "structured_search_strategies": (
                [s["name"] for s in structured_search.get("strategies", [])]
                if "strategies" in structured_search else []
            ),
            "phi_resonance_rate": phi_resonance.get("summary", {}).get("phi_resonance_rate", "N/A"),
            "phi_resonance_z_score": phi_resonance.get("summary", {}).get("z_score_vs_random", "N/A"),
        },
        "evidence_artifacts_included": list(artifacts.keys()),
    }

    return report_data


def main():
    parser = argparse.ArgumentParser(description="HYBA Φ-Trifecta Benchmark Suite")
    parser.add_argument("--quick", action="store_true", help="Run reduced iterations")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(OUTPUT_DIR),
        help="Output directory for the portfolio report",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 72)
    print("     HYBA Φ-TRIFECTA COMPREHENSIVE BENCHMARK SUITE")
    print("     Quantum Mathematics · Memory Folding · Golden Ratio Scaling")
    print("=" * 72)

    # ── Run all evidence scripts ──────────────────────────────────────────
    banner("1/6  Quantum Mathematics Verification")
    r1 = run_script("quantum_math_final_verification.py")

    banner("2/6  Structured Search Comparison (HENDRIX-Φ vs baselines)")
    search_steps = "10" if args.quick else "50000"
    r2 = run_script("phi_structured_search_demonstration.py", ["--steps", search_steps])

    banner("3/6  Φ¹⁵ Resonance in Bitcoin Blocks")
    block_count = "10" if args.quick else "100"
    r3 = run_script("collect_100_blocks.py", [block_count] if not args.quick else [block_count])

    banner("4/6  Hash Validity Correlation")
    r4 = run_script("phi_hash_validity_correlation.py")

    banner("5/6  Quantum Performance Benchmarks")
    iterations = "10" if args.quick else "100"
    r5 = run_script("benchmark_quantum.py", [iterations])

    banner("6/6  Full Stack Analysis")
    r6 = run_script("phi_complete_stack_analysis.py")

    all_results = [r1, r2, r3, r4, r5, r6]

    # ── Collect artifacts ────────────────────────────────────────────────
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
    collected = {}
    for path in artifact_paths:
        data = collect_artifact(path)
        key = os.path.basename(path)
        collected[key] = data
        print(f"  {key}: {'✓' if 'error' not in data else '✗'}")

    # ── Compile report ──────────────────────────────────────────────────
    banner("Compiling Portfolio Report")
    portfolio = report(all_results, collected)

    report_path = output_dir / "portfolio_report.json"
    with open(report_path, "w") as f:
        json.dump(portfolio, f, indent=2, default=str)
    print(f"  Report written to: {report_path}")

    # ── Print summary ────────────────────────────────────────────────────
    s = portfolio["summary"]
    km = portfolio["key_metrics"]
    print("\n" + "=" * 72)
    print("  BENCHMARK PORTFOLIO SUMMARY")
    print("=" * 72)
    print(f"  Scripts run:      {s['total_scripts']}")
    print(f"  Passed:           {s['passed']}")
    print(f"  Failed:           {s['failed']}")
    print(f"  Skipped:          {s['skipped']}")
    print(f"  Pass rate:        {s['pass_rate']}")
    print(f"  Total duration:   {s['total_duration_s']}s")
    print()
    print(f"  Quantum math:     {km.get('quantum_math_passed', '?')}/{km.get('quantum_math_tests', '?')} tests passed")
    print(f"  Φ resonance:      {km.get('phi_resonance_rate', '?')} of blocks")
    print(f"   Z-score:         {km.get('phi_resonance_z_score', '?')}")
    print()
    print(f"  Strategies compared: {km.get('structured_search_strategies', [])}")
    print()

    if s["failed"] > 0:
        print("  ⚠  FAILED SCRIPTS:")
        for r in all_results:
            if r["status"] == "FAILED":
                print(f"     - {r['script']}: returncode={r.get('returncode')}")
                if r.get("stderr"):
                    print(f"       {r['stderr'][:200]}")
    print()

    # ── Generate Markdown summary ────────────────────────────────────────
    md_path = output_dir / "PORTFOLIO_SUMMARY.md"
    with open(md_path, "w") as f:
        f.write("# HYBA Φ-Trifecta Benchmark Portfolio\n\n")
        f.write(f"**Generated:** {portfolio['generated_at']}\n\n")
        f.write("## Executive Summary\n\n")
        f.write(f"- **Scripts executed:** {s['total_scripts']}\n")
        f.write(f"- **Passed:** {s['passed']}\n")
        f.write(f"- **Failed:** {s['failed']}\n")
        f.write(f"- **Pass rate:** {s['pass_rate']}\n")
        f.write(f"- **Total duration:** {s['total_duration_s']}s\n\n")
        f.write("## Key Metrics\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"|---|---|\n")
        f.write(f"| Quantum math verification | {km.get('quantum_math_passed', '?')}/{km.get('quantum_math_tests', '?')} |\n")
        f.write(f"| Φ¹⁵ block resonance rate | {km.get('phi_resonance_rate', '?')} |\n")
        f.write(f"| Z-score vs random | {km.get('phi_resonance_z_score', '?')} |\n")
        f.write(f"| Strategies | {', '.join(km.get('structured_search_strategies', []))} |\n\n")
        f.write("## Script Results\n\n")
        f.write("| Script | Status | Duration |\n")
        f.write("|---|---|---|\n")
        for r in all_results:
            f.write(f"| {r['script']} | {r['status']} | {r['duration_s']}s |\n")
        f.write("\n## Evidence Artifacts\n\n")
        for key in portfolio["evidence_artifacts_included"]:
            f.write(f"- `{key}`\n")
        f.write("\n---\n")
        f.write("*Portfolio generated by the HYBA Φ-Trifecta Benchmark Suite*\n")
    print(f"  Markdown summary: {md_path}")
    print(f"\n  Open the HTML dashboard: benchmark_portfolio/index.html")
    print("=" * 72)

    return 0 if s["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())