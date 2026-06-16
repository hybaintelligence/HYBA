#!/usr/bin/env python3
"""
HYBA Φ-Trifecta Comprehensive Benchmark Suite

Runs evidence-collection scripts and compiles the results into a single
benchmark portfolio report.

<<<<<<< Updated upstream
Evidence-first guardrail: this runner fails before executing long or networked
benchmarks when the active Python interpreter is missing required packages. Run
it through the project virtual environment or npm gate, not the system Python.
=======
  1. Quantum Mathematics Verification (quantum_math_final_verification.py)
  2. Structured Search Comparison (phi_structured_search_demonstration.py)
  3. Φ Resonance in Bitcoin Blocks (collect_100_blocks.py)
  4. Hash Validity Correlation (phi_hash_validity_correlation.py)
  5. Quantum Performance Benchmarks (benchmark_quantum.py)
  6. Full Stack Analysis (phi_complete_stack_analysis.py)
  7. H₄ 600-cell Topological Benchmark (benchmark_h4_600cell.py) — EXPERIMENTAL

Usage:
  # Activate the project virtual environment FIRST:
  source venv/bin/activate
  python benchmark_portfolio/run_benchmarks.py [--quick] [--output-dir PATH]

Flags:
  --quick         Run reduced iterations
  --output-dir    Output directory for the portfolio report
>>>>>>> Stashed changes
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

# Scripts that require numpy (and thus the project venv)
NUMPY_REQUIRED = [
    "quantum_math_final_verification.py",
    "benchmark_quantum.py",
    "phi_complete_stack_analysis.py",
    "phi_structured_search_demonstration.py",
    "benchmark_h4_600cell.py",
]

# Scripts that are pure-stdlib (no numpy needed)
STDLIB_SCRIPTS = [
    "collect_100_blocks.py",
    "phi_hash_validity_correlation.py",
]


def check_environment() -> dict:
    """Check whether the required Python environment is active.

    Returns:
        dict with keys:
          - ok: bool — True if numpy is importable
          - python: str — the Python interpreter path
          - venv_active: bool — True if running inside a venv
          - numpy_version: str or None
          - error: str or None
    """
    result = {
        "ok": False,
        "python": sys.executable,
        "venv_active": hasattr(sys, "real_prefix") or (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        ),
        "numpy_version": None,
        "error": None,
        "venv_hint": str(ROOT / "venv" / "bin" / "python3"),
    }

    try:
        import numpy
        result["numpy_version"] = numpy.__version__
        result["ok"] = True
    except ImportError:
        # Try the project venv specifically
        venv_python = ROOT / "venv" / "bin" / "python3"
        if venv_python.exists():
            result["error"] = (
                "numpy is not available in the current Python interpreter.\n"
                f"  Current: {sys.executable}\n"
                f"  Project venv exists at: {venv_python}\n"
                f"  Activate it with: source venv/bin/activate\n"
                f"  Then re-run: python benchmark_portfolio/run_benchmarks.py"
            )
        else:
            result["error"] = (
                "numpy is not installed and no project venv was found.\n"
                "  To set up the environment: see README.md or run: pip install numpy\n"
                "  Or use the project's install script: ./setup_env.sh"
            )

    return result


def banner(text: str) -> None:
    line = "━" * 72
    print(f"\n{line}")
    print(f"  {text}")
    print(f"{line}\n")


<<<<<<< Updated upstream
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
=======
def run_script(script_name: str, extra_args: list = None, timeout: int = 600,
               requires_numpy: bool = False) -> dict:
    """Run a Python script and capture its output and exit code."""
>>>>>>> Stashed changes
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

    # Use the same Python interpreter that is running this script
    python = sys.executable

    cmd = [python, str(script_path)]
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
            # Show last 3 lines of stderr for context
            err_lines = result.stderr.strip().split("\n")
            print(f"  Error: {' | '.join(err_lines[-3:])}")
        return {
            "script": script_name,
            "status": status,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration_s": round(duration, 2),
            "requires_numpy": requires_numpy,
        }
    except subprocess.TimeoutExpired:
        return {
            "script": script_name,
            "status": "TIMEOUT",
            "error": f"Exceeded {timeout}s timeout",
            "stdout": "",
            "stderr": "",
            "duration_s": timeout,
            "requires_numpy": requires_numpy,
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


<<<<<<< Updated upstream
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
=======
def report(results: list, artifacts: dict, env_status: dict,
           h4_enabled: bool = False) -> dict:
    """Compile the final portfolio report with evidence-status labels."""
    passed = sum(1 for r in results if r["status"] == "PASSED")
    failed = sum(1 for r in results if r["status"] == "FAILED")
    skipped = sum(1 for r in results if r["status"] == "SKIPPED")
    blocked = sum(1 for r in results if r.get("requires_numpy") and r["status"] == "FAILED")
    total_time = sum(r["duration_s"] for r in results)
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
        "run_mode": run_mode,
        "benchmark_environment": environment_status(),
=======
        "environment": {
            "python": env_status["python"],
            "venv_active": env_status["venv_active"],
            "numpy_version": env_status["numpy_version"],
            "environment_ok": env_status["ok"],
        },
>>>>>>> Stashed changes
        "scripts_results": results,
        "summary": {
            "total_scripts": len(results),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "blocked_by_environment": blocked,
            "total_duration_s": round(total_time, 2),
<<<<<<< Updated upstream
            "pass_rate": f"{passed / max(len(results) - skipped, 1) * 100:.1f}%",
            "all_scripts_passed": failed == 0 and timed_out == 0 and skipped == 0,
=======
            "pass_rate": f"{passed / max(len(results) - skipped - blocked, 1) * 100:.1f}%",
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
        "evidence_boundary": {
            "partial_reports_are_not_acceptance_evidence": True,
            "failed_scripts_block_portfolio_gate": True,
            "quick_mode_is_smoke_evidence_only": run_mode == "quick_smoke",
=======
        "h4_600cell_experimental": {
            "enabled": h4_enabled,
            "status": "EXPERIMENTAL — topological upgrade from M32 to 600-cell",
            "link": "benchmark_portfolio/run_output/h4_600cell_benchmark.json",
>>>>>>> Stashed changes
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


<<<<<<< Updated upstream
def main() -> int:
    parser = argparse.ArgumentParser(description="HYBA Φ-Trifecta Benchmark Suite")
    parser.add_argument("--quick", action="store_true", help="Run reduced iterations")
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_DIR), help="Output directory")
=======
def main():
    parser = argparse.ArgumentParser(
        description="HYBA Φ-Trifecta Benchmark Suite",
        epilog="NOTE: Activate the project venv first: source venv/bin/activate",
    )
    parser.add_argument("--quick", action="store_true", help="Run reduced iterations")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(OUTPUT_DIR),
        help="Output directory for the portfolio report",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Run benchmarks even if environment check fails (for debugging)",
    )
>>>>>>> Stashed changes
    args = parser.parse_args()

    fail_fast_environment()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_mode = "quick_smoke" if args.quick else "full"

    # ── Environment Check ────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("     HYBA Φ-TRIFECTA COMPREHENSIVE BENCHMARK SUITE")
    print("     Quantum Mathematics · Memory Folding · Golden Ratio Scaling")
    print("=" * 72)

<<<<<<< Updated upstream
=======
    env_status = check_environment()
    print(f"\n  Environment check:")
    print(f"    Python:     {env_status['python']}")
    print(f"    Venv:       {'active' if env_status['venv_active'] else 'inactive'}")
    print(f"    NumPy:      {env_status['numpy_version'] or 'MISSING'}")
    print(f"    Status:     {'✓ OK' if env_status['ok'] else '✗ BLOCKED'}")

    if not env_status["ok"] and not args.force:
        print(f"\n  {env_status['error']}")
        print(f"\n  Tip: Run with --force to execute stdlib-only scripts only")
        print(f"  (numpy-dependent scripts will be skipped/blocked)\n")
        # Generate a minimal report with just the environment issue
        minimal_report = {
            "portfolio_title": "HYBA Φ-Trifecta Benchmark Portfolio",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_repository": "HYBA_FULLSTACK",
            "environment": {
                "python": env_status["python"],
                "venv_active": env_status["venv_active"],
                "numpy_version": env_status["numpy_version"],
                "environment_ok": False,
                "error": env_status["error"],
            },
            "scripts_results": [],
            "summary": {
                "total_scripts": 0,
                "passed": 0,
                "failed": 0,
                "blocked_by_environment": len(NUMPY_REQUIRED),
                "error": "Environment not configured — activate project venv first",
            },
            "key_metrics": {},
            "evidence_artifacts_included": [],
            "h4_600cell_experimental": {
                "enabled": False,
                "status": "BLOCKED — requires numpy (project venv)",
            },
        }
        report_path = output_dir / "portfolio_report.json"
        with open(report_path, "w") as f:
            json.dump(minimal_report, f, indent=2, default=str)
        print(f"  Minimal report written to: {report_path}")
        print("=" * 72)
        return 1

    # ── Run standard evidence scripts ─────────────────────────────────
>>>>>>> Stashed changes
    banner("1/6  Quantum Mathematics Verification")
    r1 = run_script("quantum_math_final_verification.py", requires_numpy=True)

    banner("2/6  Structured Search Comparison (HENDRIX-Φ vs baselines)")
<<<<<<< Updated upstream
    r2 = run_script("phi_structured_search_demonstration.py", ["--steps", "10" if args.quick else "50000"])
=======
    search_steps = "10" if args.quick else "50000"
    r2 = run_script("phi_structured_search_demonstration.py",
                    ["--steps", search_steps], requires_numpy=True)
>>>>>>> Stashed changes

    banner("3/6  Φ¹⁵ Resonance in Bitcoin Blocks")
    r3 = run_script("collect_100_blocks.py", ["10" if args.quick else "100"])

    banner("4/6  Hash Validity Correlation")
    r4 = run_script("phi_hash_validity_correlation.py")

    banner("5/6  Quantum Performance Benchmarks")
<<<<<<< Updated upstream
    r5 = run_script("benchmark_quantum.py", ["10" if args.quick else "100"])
=======
    iterations = "10" if args.quick else "100"
    r5 = run_script("benchmark_quantum.py", [iterations], requires_numpy=True)
>>>>>>> Stashed changes

    banner("6/6  Full Stack Analysis")
    r6 = run_script("phi_complete_stack_analysis.py", requires_numpy=True)

    all_results = [r1, r2, r3, r4, r5, r6]

<<<<<<< Updated upstream
=======
    # ── Run H₄ experimental benchmark ────────────────────────────────
    h4_enabled = False
    if env_status["ok"]:
        banner("EXPERIMENTAL: H₄ 600-cell Topological Benchmark")
        h4_r = run_script("benchmark_h4_600cell.py", ["--quick"], requires_numpy=True)
        all_results.append(h4_r)
        h4_enabled = h4_r["status"] in ("PASSED", "FAILED")

    # ── Collect artifacts ──────────────────────────────────────────────
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
    banner("Compiling Portfolio Report")
    portfolio = portfolio_report(all_results, collected, run_mode=run_mode)
=======
    # ── Compile report ──────────────────────────────────────────────
    banner("Compiling Portfolio Report")
    portfolio = report(all_results, collected, env_status, h4_enabled=h4_enabled)
>>>>>>> Stashed changes

    report_path = output_dir / "portfolio_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(portfolio, f, indent=2, default=str)
    print(f"  Report written to: {report_path}")

<<<<<<< Updated upstream
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
=======
    # ── Print summary ────────────────────────────────────────────────
    s = portfolio["summary"]
    km = portfolio["key_metrics"]
    h4 = portfolio["h4_600cell_experimental"]

    print("\n" + "=" * 72)
    print("  BENCHMARK PORTFOLIO SUMMARY")
    print("=" * 72)
    print(f"  Scripts run:      {s['total_scripts']}")
    print(f"  Passed:           {s['passed']}")
    print(f"  Failed:           {s['failed']}")
    print(f"  Skipped:          {s['skipped']}")
    print(f"  Blocked (env):    {s['blocked_by_environment']}")
    print(f"  Pass rate:        {s['pass_rate']}")
    print(f"  Total duration:   {s['total_duration_s']}s")
    print(f"  Python:           {env_status['python']}")
    print(f"  Venv active:      {env_status['venv_active']}")
    print(f"  NumPy version:    {env_status['numpy_version'] or 'N/A'}")
    print()
    print(f"  Key Metrics:")
    print(f"    Quantum math:     {km.get('quantum_math_passed', '?')}/{km.get('quantum_math_tests', '?')} tests passed")
    print(f"    Φ resonance:      {km.get('phi_resonance_rate', '?')} of blocks")
    print(f"    Z-score:          {km.get('phi_resonance_z_score', '?')}")
    print(f"    Strategies:       {km.get('structured_search_strategies', [])}")
    print()
    print(f"  H₄ 600-cell:      {h4['status']}")
>>>>>>> Stashed changes
    print()
    print(f"  Strategies compared: {metrics.get('structured_search_strategies', [])}")

<<<<<<< Updated upstream
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
=======
    if s["failed"] > 0:
        print("  ⚠  FAILED SCRIPTS:")
        for r in all_results:
            if r["status"] == "FAILED":
                label = " [NUMPY] " if r.get("requires_numpy") else " [STDLIB] "
                print(f"     {label}{r['script']}: returncode={r.get('returncode')}")
                if r.get("stderr"):
                    err_lines = r["stderr"].strip().split("\n")[-2:]
                    for ln in err_lines:
                        print(f"       {ln}")
    print()

    # ── Generate Markdown summary ────────────────────────────────────
    md_path = output_dir / "PORTFOLIO_SUMMARY.md"
    with open(md_path, "w") as f:
        f.write("# HYBA Φ-Trifecta Benchmark Portfolio\n\n")
        f.write(f"**Generated:** {portfolio['generated_at']}\n\n")
        f.write("## Environment\n\n")
        f.write(f"- **Python:** {env_status['python']}\n")
        f.write(f"- **Venv active:** {env_status['venv_active']}\n")
        f.write(f"- **NumPy:** {env_status['numpy_version'] or 'MISSING'}\n")
        f.write(f"- **Environment OK:** {env_status['ok']}\n\n")
        f.write("## Executive Summary\n\n")
        f.write(f"- **Scripts executed:** {s['total_scripts']}\n")
        f.write(f"- **Passed:** {s['passed']}\n")
        f.write(f"- **Failed:** {s['failed']}\n")
        f.write(f"- **Blocked by env:** {s['blocked_by_environment']}\n")
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
        f.write("| Script | Status | Duration | NumPy? |\n")
        f.write("|---|---|---:|---|\n")
        for r in all_results:
            np_tag = "✓" if r.get("requires_numpy") else "—"
            f.write(f"| {r['script']} | {r['status']} | {r['duration_s']}s | {np_tag} |\n")
        f.write("\n## H₄ 600-cell Experimental\n\n")
        f.write(f"- **Status:** {h4['status']}\n")
        f.write("- **Scheduled for full qualification after M32 baseline is clean.**\n\n")
        f.write("## Evidence Artifacts\n\n")
        for key in portfolio["evidence_artifacts_included"]:
            f.write(f"- `{key}`\n")
        f.write("\n---\n")
        f.write("*Portfolio generated by the HYBA Φ-Trifecta Benchmark Suite*\n")
        f.write("*Requires project venv: `source venv/bin/activate && python benchmark_portfolio/run_benchmarks.py`*\n")
    print(f"  Markdown summary: {md_path}")
    print(f"\n  Open the HTML dashboard: benchmark_portfolio/index.html")
>>>>>>> Stashed changes
    print("=" * 72)

    return 0 if summary["all_scripts_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
