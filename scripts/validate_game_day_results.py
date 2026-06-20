#!/usr/bin/env python3
"""Validate command-room game-day JSON evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _scenario_items(results: Any) -> list[tuple[str, dict[str, Any]]]:
    if isinstance(results, dict) and "scenarios" in results and isinstance(results["scenarios"], list):
        return [(item.get("scenario", f"scenario_{i}"), item) for i, item in enumerate(results["scenarios"])]
    if isinstance(results, list):
        return [(item.get("scenario", f"scenario_{i}"), item) for i, item in enumerate(results)]
    if isinstance(results, dict):
        if "passed" in results:
            return [(results.get("scenario", "default"), results)]
        return [(name, value) for name, value in results.items() if isinstance(value, dict)]
    return []


def validate_game_day(results_file: Path) -> int:
    results = json.loads(results_file.read_text(encoding="utf-8"))
    failures: list[str] = []
    items = _scenario_items(results)
    if not items:
        failures.append("no scenario results found")
    for scenario, result in items:
        passed = bool(result.get("passed", result.get("success", False)))
        if not passed:
            failures.append(f"{scenario}: {result.get('reason', result.get('error', 'unknown'))}")
    if failures:
        print("❌ Game day FAILED:")
        for failure in failures:
            print(f"   - {failure}")
        return 1
    print("✅ Game day PASSED: All scenarios successful")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: validate_game_day_results.py <results.json>", file=sys.stderr)
        sys.exit(2)
    sys.exit(validate_game_day(Path(sys.argv[1])))
