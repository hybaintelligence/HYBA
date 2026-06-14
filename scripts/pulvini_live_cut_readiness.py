#!/usr/bin/env python3
"""PULVINI live-cut readiness and post-cut invariant checker.

This tool does not disconnect hardware. It verifies that the exported PYTHIA
state satisfies the HYBA Command Center live-cut criteria before and after an
operator-initiated node disconnect / thermal sacrifice.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

DEFAULT_STATE_PATH = Path("python_backend/pythia_state.json")


@dataclass(frozen=True)
class CheckResult:
    code: str
    passed: bool
    message: str
    observed: Any = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LiveCutReport:
    mode: str
    status: str
    passed: bool
    state_path: str
    manifold_purity: float | None = None
    checks: list[CheckResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["checks"] = [check.to_dict() for check in self.checks]
        return payload


def _get_path(payload: dict[str, Any], path: Iterable[str], default: Any = None) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def _bool_value(value: Any) -> bool:
    return bool(value) if value is not None else False


def _rebalanced_nodes(autonomics: dict[str, Any]) -> set[int]:
    nodes: set[int] = set()
    for event in autonomics.get("rebalances") or []:
        for node_id in event.get("failed_nodes") or []:
            try:
                nodes.add(int(node_id))
            except (TypeError, ValueError):
                continue
    return nodes


def _healing_route_sources(overlay: dict[str, Any]) -> set[int]:
    sources: set[int] = set()
    for route in overlay.get("healing_routes") or []:
        try:
            sources.add(int(route.get("failed_node")))
        except (TypeError, ValueError):
            continue
    return sources


def _numeric_path(payload: dict[str, Any], path: Iterable[str]) -> float | None:
    value = _get_path(payload, path)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _check_trace(autonomics: dict[str, Any], *, tolerance: float) -> CheckResult:
    trace = _get_path(autonomics, ["rho", "trace"])
    try:
        value = float(trace)
    except (TypeError, ValueError):
        return CheckResult("rho_trace_present", False, "rho.trace is missing or non-numeric", trace)
    return CheckResult(
        "rho_trace_unit",
        math.isclose(value, 1.0, rel_tol=0.0, abs_tol=tolerance),
        f"rho.trace must remain 1.0 ± {tolerance}",
        value,
    )


def _check_purity(autonomics: dict[str, Any], *, min_purity: float) -> CheckResult:
    value = _numeric_path(autonomics, ["rho", "purity"])
    if value is None:
        return CheckResult(
            "rho_purity_present",
            False,
            "rho.purity is missing or non-numeric",
            _get_path(autonomics, ["rho", "purity"]),
        )
    return CheckResult(
        "rho_purity_minimum",
        value >= min_purity,
        f"rho.purity must be >= {min_purity}",
        value,
    )


def _parse_node_list(value: str | None) -> set[int]:
    if value in (None, ""):
        return set()
    nodes: set[int] = set()
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        nodes.add(int(item))
    return nodes


def evaluate_live_cut_state(
    state: dict[str, Any],
    *,
    mode: str = "preflight",
    tolerance: float = 1e-9,
    min_purity: float = 0.9,
    expected_severed_nodes: Iterable[int] = (),
    state_path: str = "<memory>",
) -> LiveCutReport:
    """Evaluate exported PYTHIA state against live-cut invariants."""

    overlay = state.get("pulvini_overlay") or {}
    autonomics = state.get("pulvini_autonomics") or {}
    checks: list[CheckResult] = []

    checks.append(
        CheckResult(
            "autonomics_available",
            bool(autonomics) and autonomics.get("status") == "ok",
            "pulvini_autonomics.status must be ok",
            autonomics.get("status"),
        )
    )
    checks.append(_check_trace(autonomics, tolerance=tolerance))
    checks.append(_check_purity(autonomics, min_purity=min_purity))
    checks.append(
        CheckResult(
            "pool_identity_one",
            int(state.get("pool_visible_workers") or overlay.get("pool_visible_workers") or 0) == 1,
            "pool-visible worker count must remain one",
            state.get("pool_visible_workers") or overlay.get("pool_visible_workers"),
        )
    )
    checks.append(
        CheckResult(
            "active_job_locked",
            bool(
                state.get("current_job_id")
                or overlay.get("active_job_id")
                or state.get("current_job")
            ),
            "active job id must be present before and after live cut",
            state.get("current_job_id") or overlay.get("active_job_id") or state.get("current_job"),
        )
    )
    checks.append(
        CheckResult(
            "healing_ranges_overlap_free",
            _bool_value(overlay.get("healing_ranges_overlap_free", True)),
            "healing ranges must not overlap recipient native ranges or each other",
            overlay.get("healing_ranges_overlap_free"),
        )
    )

    sacrificed = {int(node_id) for node_id in autonomics.get("sacrificed_nodes") or []}
    rebalanced = _rebalanced_nodes(autonomics)
    routed = _healing_route_sources(overlay)
    missing_rebalance = sorted(sacrificed - rebalanced)
    missing_routes = sorted(sacrificed - routed)
    expected = {int(node_id) for node_id in expected_severed_nodes}

    checks.append(
        CheckResult(
            "sacrificed_nodes_rebalanced",
            not missing_rebalance,
            "every sacrificed node must have a corresponding rebalance event",
            {"sacrificed": sorted(sacrificed), "missing_rebalance": missing_rebalance},
        )
    )
    checks.append(
        CheckResult(
            "sacrificed_nodes_have_healing_routes",
            not missing_routes,
            "every sacrificed node must have exported healing routes",
            {"sacrificed": sorted(sacrificed), "missing_routes": missing_routes},
        )
    )

    if expected:
        checks.append(
            CheckResult(
                "expected_severed_nodes_observed",
                expected.issubset(sacrificed | rebalanced | routed),
                "all expected severed nodes must appear in sacrificed nodes, rebalances, or healing routes",
                {
                    "expected": sorted(expected),
                    "sacrificed": sorted(sacrificed),
                    "rebalanced": sorted(rebalanced),
                    "routed": sorted(routed),
                },
            )
        )

    if mode == "postcut":
        checks.append(
            CheckResult(
                "postcut_healing_observed",
                bool(sacrificed or overlay.get("healing_routes")),
                "post-cut state must include a sacrificed node or healing route",
                {
                    "sacrificed": sorted(sacrificed),
                    "healing_routes": len(overlay.get("healing_routes") or []),
                },
            )
        )

    passed = all(check.passed for check in checks)
    if passed:
        status = "ready" if mode == "preflight" else "postcut_verified"
    else:
        status = "blocked"
    return LiveCutReport(
        mode=mode,
        status=status,
        passed=passed,
        state_path=state_path,
        manifold_purity=_numeric_path(autonomics, ["rho", "purity"]),
        checks=checks,
    )


def load_state(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _print_human(report: LiveCutReport) -> None:
    symbol = "✅" if report.passed else "❌"
    print(f"{symbol} PULVINI live-cut {report.mode}: {report.status}")
    print(f"state_path={report.state_path}")
    print(f"manifold_purity={report.manifold_purity!r}")
    for check in report.checks:
        marker = "✅" if check.passed else "❌"
        print(f"{marker} {check.code}: {check.message} observed={check.observed!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate PULVINI live-cut readiness/post-cut invariants"
    )
    parser.add_argument(
        "--state",
        type=Path,
        default=DEFAULT_STATE_PATH,
        help="Path to exported pythia_state.json",
    )
    parser.add_argument("--mode", choices=("preflight", "postcut"), default="preflight")
    parser.add_argument(
        "--tolerance",
        type=float,
        default=1e-9,
        help="Absolute tolerance for rho.trace == 1",
    )
    parser.add_argument(
        "--min-purity", type=float, default=0.9, help="Minimum acceptable rho.purity"
    )
    parser.add_argument(
        "--expected-severed-nodes",
        default="",
        help="Comma-separated node ids expected to be severed/healed, e.g. 0,1,2",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)

    try:
        state = load_state(args.state)
        report = evaluate_live_cut_state(
            state,
            mode=args.mode,
            tolerance=args.tolerance,
            min_purity=args.min_purity,
            expected_severed_nodes=_parse_node_list(args.expected_severed_nodes),
            state_path=str(args.state),
        )
    except Exception as exc:  # noqa: BLE001 - CLI must emit a concise operator error.
        report = LiveCutReport(
            mode=args.mode,
            status="error",
            passed=False,
            state_path=str(args.state),
            manifold_purity=None,
            checks=[CheckResult("state_load", False, str(exc))],
        )

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        _print_human(report)
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
