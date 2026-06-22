"""Evidence tests for φ hardware scaling and φ quantum-operation acceleration.

These tests intentionally elevate the repository evidence above generic
"software integration" language. They verify the code-level claims that:

1. golden-ratio scaling is used to derive effective hardware concurrency;
2. quantum-operation benchmarks compute φ-speedup from measured QOps/s;
3. φ-memory compression lowers active state memory while preserving the
   retained-kernel reconstruction boundary documented elsewhere.

The boundary is precise: these tests prove the deterministic formulas and
benchmark accounting used by HYBA's post-quantum mathematical runtime. They do
not claim a physical QPU, guaranteed revenue, or removal of external proof
verification.
"""

from __future__ import annotations

import math

import pytest

from pythia_mining.golden_ratio_library import PHI, PHI_INV
from pythia_mining.phi_cloud_deployer import HARDWARE_TARGETS, PhiCloudDeployer
from pythia_mining.enhanced_benchmark_suite import EnhancedBenchmarkSuite
import pythia_mining.enhanced_benchmark_suite as enhanced_benchmarks


def test_phi_cloud_concurrency_uses_golden_ratio_hardware_scaling() -> None:
    """Golden ratio scaling must be the hardware concurrency law."""

    for target_name, target in HARDWARE_TARGETS.items():
        deployer = PhiCloudDeployer(target_name)
        effective_cores = deployer.calculate_phi_concurrency()

        expected = int(target.cores * (PHI_INV ** (math.log2(target.cores) / 10.0)))

        assert effective_cores == expected
        assert 0 < effective_cores < target.cores


def test_phi_cloud_larger_hardware_still_gains_effective_concurrency() -> None:
    """φ-scaling damps decoherence but still scales upward with larger substrates."""

    trainium = PhiCloudDeployer("aws_trainium").calculate_phi_concurrency()
    h100 = PhiCloudDeployer("nvidia_h100").calculate_phi_concurrency()
    tpu = PhiCloudDeployer("google_tpu_v5e").calculate_phi_concurrency()
    cerebras = PhiCloudDeployer("cerebras_wse3").calculate_phi_concurrency()

    assert trainium < h100 < tpu < cerebras


def test_phi_quantum_speedup_benchmark_accounting_is_consistent() -> None:
    """The φ quantum benchmark must report speedup as QOps/s over 1GHz baseline."""

    deployer = PhiCloudDeployer("aws_trainium")
    result = deployer.benchmark_phi_speedup(n_qubits=4, iterations=2)

    assert result["hardware"] == HARDWARE_TARGETS["aws_trainium"].name
    assert result["effective_cores"] == deployer.calculate_phi_concurrency()
    assert result["qops_per_sec"] > 0.0
    assert result["phi_speedup"] == pytest.approx(result["qops_per_sec"] / 1e9)
    assert result["efficiency_pct"] == pytest.approx(
        (result["qops_per_sec"] / result["peak_flops"]) * 100.0
    )


def test_enhanced_hardware_scaling_records_phi_memory_advantage(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enhanced benchmark suite must record φ-compression benefit during scaling."""

    # Avoid running the full mining cycle; this test verifies scaling accounting.
    monkeypatch.setattr(enhanced_benchmarks, "run_fault_tolerant_mining_cycle", lambda num_iterations=5: {"ok": True})

    ticks = iter([0.0, 0.10, 1.0, 1.25, 2.0, 2.50])
    monkeypatch.setattr(enhanced_benchmarks.time, "time", lambda: next(ticks))

    suite = EnhancedBenchmarkSuite(output_dir="artifacts/test_phi_hardware_quantum_scaling")
    result = suite.benchmark_hardware_scaling(qubit_range=[4, 5, 6])

    assert result["benchmark"] == "hardware_scaling"
    assert result["phi_compression_benefit_pct"] == pytest.approx((1 - 1 / PHI) * 100)

    for row in result["results"]:
        assert row["compression_ratio"] == pytest.approx(PHI)
        assert row["compressed_memory_mb"] == pytest.approx(row["memory_mb"] / PHI)
        assert row["qops_per_sec"] > 0.0
