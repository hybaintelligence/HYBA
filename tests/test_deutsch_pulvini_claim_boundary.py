from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from scripts import benchmark_deutsch_exponential_wall as deutsch_wall  # noqa: E402
from scripts import benchmark_deutsch_with_pulvini as deutsch_pulvini  # noqa: E402


def test_deutsch_memory_scaling_records_exponential_state_size() -> None:
    results = deutsch_wall.benchmark_state_vector_memory_scaling()
    state_sizes = [row["state_size"] for row in results]

    assert state_sizes == sorted(state_sizes)
    assert state_sizes[-1] / state_sizes[0] == 2 ** (14 - 4)


def test_tensor_network_efficiency_is_structured_state_evidence_only() -> None:
    results = deutsch_wall.benchmark_tensor_network_efficiency()

    assert results[-1]["num_qubits"] == 1000
    assert results[-1]["memory_mb"] < 16.0
    assert results[-1]["max_bond"] == 16
    assert results[-1]["compression_ratio"] > results[0]["compression_ratio"]


def test_deutsch_prediction_separates_structured_from_unstructured_states() -> None:
    [result] = deutsch_wall.benchmark_deutsch_prediction_unstructured()

    assert result["unstructured_params"] > result["structured_params"]
    assert result["param_ratio"] > 100.0
    assert result["unstructured_entropy"] > result["structured_entropy"]


def test_pulvini_phi_folding_is_lossless_but_not_exponential() -> None:
    results = deutsch_pulvini.benchmark_pulvini_phi_folding_compression()

    assert all(row["lossless"] for row in results)
    assert all(row["reconstruction_error"] < 1e-10 for row in results)
    assert max(row["compression_ratio"] for row in results) <= 4.0


def test_pulvini_plus_tensor_network_is_low_entanglement_structured_compression() -> None:
    results = deutsch_pulvini.benchmark_pulvini_tensor_integration()

    assert all(row["reversible"] for row in results)
    assert all(row["total_compression_ratio"] > 1.0 for row in results)
    assert all(row["pulvini_compression_ratio"] <= 4.0 for row in results)


def test_pulvini_does_not_eliminate_deutsch_wall_for_unstructured_states() -> None:
    [result] = deutsch_pulvini.benchmark_deutsch_prediction_with_pulvini()

    assert result["unstructured_params"] > result["structured_params"]
    assert result["param_ratio"] > 100.0
    assert result["structured_pulvini_ratio"] >= result["unstructured_pulvini_ratio"]
    assert result["unstructured_pulvini_ratio"] <= 4.0
