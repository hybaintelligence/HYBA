#!/usr/bin/env python3
"""HYBA Φ-Trifecta benchmark portfolio runner.

Evidence-first rule: a portfolio is acceptance-grade only when every configured
script passes. Skipped, failed, timed-out, or wrong-interpreter runs are smoke
or diagnostic evidence only.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
OUTPUT_DIR = ROOT / "benchmark_portfolio" / "run_output"
REQUIRED_IMPORTS = ("numpy",)
NUMPY_REQUIRED = {
    "quantum_math_final_verification.py",
    "benchmark_quantum.py",
    "phi_complete_stack_analysis.py",
    "phi_structured_search_demonstration.py",
    "benchmark_h4_600cell.py",
}


def environment_status() -> dict[str, Any]:
    missing = [
        name for name in REQUIRED_IMPORTS if importlib.util.find_spec(name) is None
    ]
    return {
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "venv_active": hasattr(sys, "real_prefix")
        or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix),
        "required_imports": list(REQUIRED_IMPORTS),
        "missing_imports": missing,
        "status": "ready" if not missing else "blocked",
    }


def banner(text: str) -> None:
    print(f"\n{'━' * 72}\n  {text}\n{'━' * 72}\n")


def run_script(
    script_name: str, args: list[str] | None = None, *, timeout: int = 600
) -> dict[str, Any]:
    script_path = SCRIPTS / script_name
    needs_numpy = script_name in NUMPY_REQUIRED
    if not script_path.exists():
        return {
            "script": script_name,
            "status": "SKIPPED",
            "duration_s": 0.0,
            "requires_numpy": needs_numpy,
            "error": f"missing: {script_path}",
        }

    cmd = [sys.executable, str(script_path), *(args or [])]
    print(f"  Running: {' '.join(cmd)}")
    start = time.time()
    try:
        completed = subprocess.run(
            cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return {
            "script": script_name,
            "status": "TIMEOUT",
            "duration_s": float(timeout),
            "requires_numpy": needs_numpy,
            "stderr": "timeout",
        }

    duration = round(time.time() - start, 2)
    status = "PASSED" if completed.returncode == 0 else "FAILED"
    print(f"  Status: {status} ({duration:.2f}s)")
    return {
        "script": script_name,
        "status": status,
        "returncode": completed.returncode,
        "duration_s": duration,
        "requires_numpy": needs_numpy,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def collect_artifact(path: str) -> dict[str, Any]:
    full_path = ROOT / path
    if not full_path.exists():
        return {"error": f"not_found: {path}"}
    try:
        return json.loads(full_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"error": str(exc)}


def artifact_key(path: str) -> str:
    return path.replace("artifacts/", "").replace("/", "__")


def first_artifact(artifacts: dict[str, Any], suffix: str) -> dict[str, Any]:
    for key, value in artifacts.items():
        if key.endswith(suffix) and isinstance(value, dict) and "error" not in value:
            return value
    return {}


def build_report(
    results: list[dict[str, Any]],
    artifacts: dict[str, Any],
    env: dict[str, Any],
    run_mode: str,
    h4_enabled: bool,
) -> dict[str, Any]:
    passed = sum(1 for item in results if item["status"] == "PASSED")
    failed = sum(1 for item in results if item["status"] == "FAILED")
    skipped = sum(1 for item in results if item["status"] == "SKIPPED")
    timed_out = sum(1 for item in results if item["status"] == "TIMEOUT")
    all_passed = failed == 0 and skipped == 0 and timed_out == 0

    quantum_math = first_artifact(
        artifacts, "quantum_mathematics_final_verification.json"
    )
    structured_search = first_artifact(artifacts, "structured_search_comparison.json")
    phi_resonance = first_artifact(artifacts, "phi_resonance_summary.json")
    hash_validity = first_artifact(artifacts, "phi_hash_correlation_summary.json")
    stack = first_artifact(artifacts, "complete_stack_analysis.json")
    resonance_summary = (
        phi_resonance.get("summary", {})
        if isinstance(phi_resonance.get("summary"), dict)
        else phi_resonance
    )
    stack_summary = (
        stack.get("summary", {}) if isinstance(stack.get("summary"), dict) else stack
    )

    return {
        "portfolio_title": "HYBA Φ-Trifecta Benchmark Portfolio",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_repository": "HYBA_FULLSTACK",
        "run_mode": run_mode,
        "benchmark_environment": env,
        "scripts_results": results,
        "summary": {
            "total_scripts": len(results),
            "passed": passed,
            "failed": failed,
            "timed_out": timed_out,
            "skipped": skipped,
            "blocked_by_environment": (
                0 if env["status"] == "ready" else len(NUMPY_REQUIRED)
            ),
            "total_duration_s": round(
                sum(float(item["duration_s"]) for item in results), 2
            ),
            "pass_rate": f"{passed / max(len(results) - skipped, 1) * 100:.1f}%",
            "all_scripts_passed": all_passed,
        },
        "key_metrics": {
            "quantum_math_tests": quantum_math.get("total_tests", "N/A"),
            "quantum_math_passed": quantum_math.get("passed", "N/A"),
            "quantum_math_pass_rate": quantum_math.get("pass_rate", "N/A"),
            "structured_search_strategies": (
                [s["name"] for s in structured_search.get("strategies", [])]
                if "strategies" in structured_search
                else []
            ),
            "phi_resonance_rate": resonance_summary.get(
                "phi_resonance_rate", resonance_summary.get("resonance_rate", "N/A")
            ),
            "phi_resonance_z_score": resonance_summary.get(
                "z_score_vs_random", resonance_summary.get("z_score", "N/A")
            ),
            "hash_validity_correlation": hash_validity.get(
                "correlation", hash_validity.get("r", "N/A")
            ),
            "structured_advantage_over_grover": stack_summary.get(
                "advantage_over_grover", stack_summary.get("grover_advantage", "N/A")
            ),
        },
        "evidence_artifacts_included": list(artifacts.keys()),
        "h4_600cell_experimental": {
            "enabled": h4_enabled,
            "artifact": "benchmark_portfolio/run_output/h4_600cell_benchmark.json",
        },
        "evidence_boundary": {
            "partial_reports_are_not_acceptance_evidence": True,
            "failed_scripts_block_portfolio_gate": True,
            "quick_mode_is_smoke_evidence_only": run_mode == "quick_smoke",
            "acceptance_requires_all_scripts_passed": True,
        },
    }


def write_markdown_summary(path: Path, report: dict[str, Any]) -> None:
    summary = report["summary"]
    metrics = report["key_metrics"]
    lines = [
        "# HYBA Φ-Trifecta Benchmark Portfolio",
        "",
        f"**Generated:** {report['generated_at']}",
        f"**Run mode:** `{report['run_mode']}`",
        "",
        "## Executive Summary",
        "",
        f"- **Passed:** {summary['passed']}",
        f"- **Failed:** {summary['failed']}",
        f"- **Timed out:** {summary['timed_out']}",
        f"- **Skipped:** {summary['skipped']}",
        f"- **All scripts passed:** {summary['all_scripts_passed']}",
        "",
        "## Key Metrics",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Quantum math verification | {metrics.get('quantum_math_passed', '?')}/{metrics.get('quantum_math_tests', '?')} |",
        f"| Φ¹⁵ block resonance rate | {metrics.get('phi_resonance_rate', '?')} |",
        f"| Hash-validity correlation | {metrics.get('hash_validity_correlation', '?')} |",
        "",
        "## Evidence Boundary",
        "",
        "Partial reports are smoke evidence only. Acceptance-grade evidence requires all scripts to pass.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="HYBA Φ-Trifecta Benchmark Suite")
    parser.add_argument("--quick", action="store_true", help="Run reduced iterations")
    parser.add_argument(
        "--output-dir", type=str, default=str(OUTPUT_DIR), help="Output directory"
    )
    parser.add_argument(
        "--force", action="store_true", help="Run even if environment guard is blocked"
    )
    args = parser.parse_args()

    env = environment_status()
    if env["status"] != "ready" and not args.force:
        print(json.dumps({"benchmark_environment": env}, indent=2, sort_keys=True))
        print(
            "\nBenchmark runner blocked before execution. Activate the project virtual environment first."
        )
        return 2

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_mode = "quick_smoke" if args.quick else "full"
    results: list[dict[str, Any]] = []

    plan = [
        (
            "1/6  Quantum Mathematics Verification",
            "quantum_math_final_verification.py",
            [],
        ),
        (
            "2/6  Structured Search Comparison",
            "phi_structured_search_demonstration.py",
            ["--steps", "10" if args.quick else "50000"],
        ),
        (
            "3/6  Φ¹⁵ Resonance in Bitcoin Blocks",
            "collect_100_blocks.py",
            ["10" if args.quick else "100"],
        ),
        ("4/6  Hash Validity Correlation", "phi_hash_validity_correlation.py", []),
        (
            "5/6  Quantum Performance Benchmarks",
            "benchmark_quantum.py",
            ["10" if args.quick else "100"],
        ),
        ("6/6  Full Stack Analysis", "phi_complete_stack_analysis.py", []),
    ]
    for title, script, script_args in plan:
        banner(title)
        results.append(run_script(script, script_args))

    h4_enabled = False
    if env["status"] == "ready":
        banner("EXPERIMENTAL: H₄ 600-cell Topological Benchmark")
        h4_result = run_script("benchmark_h4_600cell.py", ["--quick"])
        results.append(h4_result)
        h4_enabled = h4_result["status"] in {"PASSED", "FAILED", "TIMEOUT"}

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
    artifacts = {artifact_key(path): collect_artifact(path) for path in artifact_paths}
    report = build_report(results, artifacts, env, run_mode, h4_enabled)

    report_path = output_dir / "portfolio_report.json"
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    md_path = output_dir / "PORTFOLIO_SUMMARY.md"
    write_markdown_summary(md_path, report)

    summary = report["summary"]
    print("\n" + "=" * 72)
    print("  BENCHMARK PORTFOLIO SUMMARY")
    print("=" * 72)
    print(f"  Passed:         {summary['passed']}")
    print(f"  Failed:         {summary['failed']}")
    print(f"  Timed out:      {summary['timed_out']}")
    print(f"  Skipped:        {summary['skipped']}")
    print(f"  Acceptance:     {summary['all_scripts_passed']}")
    print(f"  JSON report:    {report_path}")
    print(f"  Markdown:       {md_path}")
    if not summary["all_scripts_passed"]:
        print(
            "\n  This report is smoke/diagnostic evidence only until all scripts pass."
        )
    return 0 if summary["all_scripts_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
