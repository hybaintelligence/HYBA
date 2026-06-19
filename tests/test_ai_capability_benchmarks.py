"""AI capability benchmarks beyond mining.

These tests benchmark deterministic emergent-AI support surfaces without making
claims about sentience, consciousness, quantum hardware, or external model
performance. The goal is to keep HYBA's intelligence stack measurable across:

1. substrate routing and explanation latency,
2. counterfactual/governance coverage,
3. deterministic replay under repeated contexts,
4. manifold causal/topological/geometric scoring, and
5. thermal-cost telemetry boundedness.

Run with:
    PYTHONPATH=python_backend python -m pytest tests/test_ai_capability_benchmarks.py -q -s
"""

from __future__ import annotations

import math
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean, stdev
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from hyba_genesis_api.core.intelligence_fabric import explain  # noqa: E402
from hyba_genesis_api.core.intelligence_manifold import IntelligenceManifold  # noqa: E402
from hyba_genesis_api.core.thermal_intelligence import ThermalEnvelope  # noqa: E402


@dataclass(frozen=True)
class CapabilityBenchmark:
    name: str
    metric: str
    value: float
    unit: str
    threshold: float
    passed: bool
    samples: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)


class AICapabilityBenchmarkSuite:
    def __init__(self) -> None:
        self.results: list[CapabilityBenchmark] = []

    def add(self, result: CapabilityBenchmark) -> None:
        self.results.append(result)

    def passed(self) -> bool:
        return all(result.passed for result in self.results)

    def summary(self) -> str:
        lines = ["\nAI CAPABILITY BENCHMARKS (NON-MINING)", "=" * 44]
        for result in self.results:
            status = "✅" if result.passed else "❌"
            lines.append(
                f"{status} {result.name}: {result.value:.6f} {result.unit} "
                f"({result.metric}; threshold={result.threshold})"
            )
            if result.metadata:
                lines.append(f"   metadata={result.metadata}")
        return "\n".join(lines)


def _benchmark_explanation_latency(sample_count: int = 64) -> CapabilityBenchmark:
    contexts = [
        {
            "problem": "semantic counterfactual explanation for stability policy",
            "difficulty": (index % 17) / 17,
            "signals": ["policy", "counterfactual", "stability", index],
        }
        for index in range(sample_count)
    ]
    latencies_ms: list[float] = []
    route_counts: dict[str, int] = {}

    for context in contexts:
        start = time.perf_counter()
        envelope = explain(context)
        latencies_ms.append((time.perf_counter() - start) * 1000)
        route_counts[envelope["selected_substrate"]] = (
            route_counts.get(envelope["selected_substrate"], 0) + 1
        )

    avg = mean(latencies_ms)
    p95 = sorted(latencies_ms)[int(len(latencies_ms) * 0.95)]
    return CapabilityBenchmark(
        name="intelligence fabric explanation latency",
        metric="mean_latency_ms",
        value=avg,
        unit="ms",
        threshold=5.0,
        passed=avg < 5.0 and p95 < 15.0,
        samples=sample_count,
        metadata={"p95_ms": round(p95, 6), "routes": route_counts},
    )


def _benchmark_counterfactual_governance_coverage(sample_count: int = 24) -> CapabilityBenchmark:
    required_governance = {"hardware_agnostic_math", "no_quantum_speedup_claim"}
    coverage_scores: list[float] = []
    minimum_counterfactuals = math.inf

    for index in range(sample_count):
        envelope = explain(
            {
                "task": "integrated cause effect semantic counterfactual thermal stability",
                "index": index,
                "operator_intent": "capability benchmark not mining",
            }
        )
        governance = set(envelope["governance"])
        counterfactual_count = len(envelope["counterfactuals"])
        minimum_counterfactuals = min(minimum_counterfactuals, counterfactual_count)
        coverage_scores.append(len(required_governance & governance) / len(required_governance))

    coverage = mean(coverage_scores)
    return CapabilityBenchmark(
        name="counterfactual and claim-boundary coverage",
        metric="coverage_ratio",
        value=coverage,
        unit="ratio",
        threshold=1.0,
        passed=coverage == 1.0 and minimum_counterfactuals >= 2,
        samples=sample_count,
        metadata={"minimum_counterfactuals": int(minimum_counterfactuals)},
    )


def _benchmark_deterministic_replay(sample_count: int = 32) -> CapabilityBenchmark:
    mismatches = 0
    for index in range(sample_count):
        context = {
            "problem": "replay-safe emergent-ai substrate selection",
            "index": index,
            "nested": {"b": [3, 2, 1], "a": "stable"},
        }
        first = explain(context)
        second = explain(
            {
                "nested": {"a": "stable", "b": [3, 2, 1]},
                "index": index,
                "problem": context["problem"],
            }
        )
        if (
            first["context_digest"] != second["context_digest"]
            or first["selected_substrate"] != second["selected_substrate"]
            or first["raw_metrics"] != second["raw_metrics"]
        ):
            mismatches += 1

    replay_match = 1.0 - (mismatches / sample_count)
    return CapabilityBenchmark(
        name="deterministic replay reproducibility",
        metric="match_ratio",
        value=replay_match,
        unit="ratio",
        threshold=1.0,
        passed=replay_match == 1.0,
        samples=sample_count,
        metadata={"mismatches": mismatches},
    )


def _benchmark_manifold_capability() -> list[CapabilityBenchmark]:
    manifold = IntelligenceManifold()
    manifold.update_causal_graph(
        [
            ("router", "fabric"),
            ("router", "governance"),
            ("fabric", "substrate"),
            ("substrate", "counterfactuals"),
            ("governance", "claim_boundary"),
        ]
    )
    telemetry = manifold.synthesize(
        nodes=6,
        edges=5,
        weights=[0.2, 0.34, 0.55, 0.89, 1.44],
        current_logic="abcdefgpolicycounterfactual",
        target_transformation="policy",
        observed_phi=0.62,
        predicted_phi=0.58,
    )
    critical = manifold.identify_critical_functions(limit=2)
    return [
        CapabilityBenchmark(
            name="manifold bounded geometric stability",
            metric="geometric_stability",
            value=telemetry.geometric_stability,
            unit="ratio",
            threshold=0.0,
            passed=0.0 <= telemetry.geometric_stability <= 1.0,
            metadata={"fisher_curvature": telemetry.fisher_curvature},
        ),
        CapabilityBenchmark(
            name="manifold causal hotspot ranking",
            metric="top_causal_impact",
            value=critical[0]["causal_impact"],
            unit="impact",
            threshold=0.0,
            passed=critical[0]["node_id"] == "router"
            and critical[0]["causal_impact"] > critical[1]["causal_impact"],
            metadata={"critical": critical},
        ),
    ]


def _benchmark_thermal_envelope(sample_count: int = 20) -> CapabilityBenchmark:
    costs: list[float] = []
    for index in range(sample_count):
        envelope = ThermalEnvelope()
        envelope.start_cognition()
        _ = sum(math.sqrt(value + index) for value in range(64))
        snapshot = envelope.snapshot(phi=0.5 + (index / (sample_count * 4)))
        costs.append(snapshot["thermal_cost_phi_per_second"])

    finite_ratio = sum(math.isfinite(value) and value > 0 for value in costs) / len(costs)
    return CapabilityBenchmark(
        name="thermal cognition cost telemetry",
        metric="finite_positive_ratio",
        value=finite_ratio,
        unit="ratio",
        threshold=1.0,
        passed=finite_ratio == 1.0,
        samples=sample_count,
        metadata={"mean_cost": round(mean(costs), 6), "std_cost": round(stdev(costs), 6)},
    )


@pytest.mark.benchmark
def test_ai_capability_benchmark_suite() -> None:
    suite = AICapabilityBenchmarkSuite()
    suite.add(_benchmark_explanation_latency())
    suite.add(_benchmark_counterfactual_governance_coverage())
    suite.add(_benchmark_deterministic_replay())
    for result in _benchmark_manifold_capability():
        suite.add(result)
    suite.add(_benchmark_thermal_envelope())

    print(suite.summary())
    assert suite.passed(), suite.summary()
