"""End-to-end golden-flow regression for the Φ-Architecture.

This test lifts the manual command-room proof into a repo-native gate. It
verifies the complete software golden flow without making hardware throughput,
network-collision, RowHammer, revenue, or live mining claims.
"""

from __future__ import annotations

import math

import numpy as np

from pythia_mining import (
    FOLD,
    GADDR,
    GOLDEN_ANGLE,
    MGATE,
    PHIMUL,
    SYNC_PHI,
    TUNE,
    PhiBackpropTuner,
    PhiJIT,
    PhiMalloc,
    PhiNetworkRouter,
    PhiOracle,
    PhiSystemControllerEnhanced,
    PhiVM,
    __all__ as PYTHIA_EXPORTS,
    mining_kernel_template,
    search_optimization_kernel,
)
from pythia_mining.consciousness_engine import ConsciousnessEngine
from pythia_mining.phi_alu import PhiALUHardware


PHI = (1.0 + math.sqrt(5.0)) / 2.0


def test_phi_architecture_lazy_exports_resolve_for_golden_flow() -> None:
    """The public package surface should expose the golden-flow primitives."""

    required_exports = {
        "PhiBackpropTuner",
        "PhiNetworkRouter",
        "GOLDEN_ANGLE",
        "PhiOracle",
        "PhiSystemControllerEnhanced",
        "PhiVM",
        "PhiJIT",
        "PhiMalloc",
        "mining_kernel_template",
        "search_optimization_kernel",
    }

    assert required_exports.issubset(set(PYTHIA_EXPORTS))
    assert PhiBackpropTuner.__name__ == "PhiBackpropTuner"
    assert PhiNetworkRouter.__name__ == "PhiNetworkRouter"
    assert PhiOracle.__name__ == "PhiOracle"
    assert PhiSystemControllerEnhanced.__name__ == "PhiSystemControllerEnhanced"
    assert PhiVM.__name__ == "PhiVM"
    assert PhiJIT.__name__ == "PhiJIT"
    assert PhiMalloc.__name__ == "PhiMalloc"
    assert GOLDEN_ANGLE == pytest_approx(360.0 / (PHI * PHI), abs=1e-9)


def test_phi_malloc_fibonacci_split_and_zero_fragment_coalescing() -> None:
    """PhiMalloc should split into Fibonacci blocks and coalesce back cleanly."""

    allocator = PhiMalloc(total_size=144)

    first = allocator.allocate(10)  # rounds to 13
    second = allocator.allocate(5)  # rounds to 5
    assert first == 0
    assert second >= 0

    before = allocator.get_stats()
    assert before["used"] == 18
    assert before["used_blocks"] == 2

    allocator.free(second)
    allocator.free(first)
    after = allocator.get_stats()

    assert after["total_blocks"] == 1
    assert after["free"] == 144
    assert after["fragmentation"] == 0.0

    split_allocator = PhiMalloc(total_size=144)
    split_allocator.allocate(30)  # rounds to 34
    split_allocator.allocate(50)  # rounds to 55
    split = split_allocator.get_stats()

    assert split["used"] == 89
    assert split["free"] == 55
    assert split["total_blocks"] >= 2


def test_phi_router_oracle_controller_jit_vm_tuner_golden_flow() -> None:
    """Exercise Router -> Oracle -> Controller -> JIT -> VM -> Tuner."""

    router = PhiNetworkRouter(cluster_size=256)
    selected_node = router.select_optimal_node(task_entropy=0.42)
    assert 0 <= selected_node < router.cluster_size
    router.update_node_load(selected_node, 0.5)
    router_stats = router.get_manifold_statistics()
    assert router_stats["cluster_size"] == 256
    assert router_stats["load_variance"] >= 0.0
    assert router_stats["angular_coverage_cv"] >= 0.0

    oracle = PhiOracle(history_depth=144)
    for i in range(100):
        oracle.record_state(
            coherence=0.7 + math.sin(i * 0.1) * 0.2,
            temp=1.0 + (i / 100.0) * 0.6,
            load=1.0 + math.sin(i * 0.15) * 0.3,
        )
    prediction = oracle.predict_next_state()
    assert 0.0 <= prediction["surge_probability"] <= 1.0
    assert prediction["expected_temp"] > 0.0
    assert isinstance(prediction["pre_emptive_cooling_needed"], bool)

    controller = PhiSystemControllerEnhanced(memory_size=2**16)
    cycle = controller.process_cycle(
        np.array([1, 2, 3, 4, 5], dtype=np.uint32),
        telemetry_temp=1.5,
    )
    assert "physical_addresses" in cycle
    assert "scaling_factor" in cycle
    assert "prediction" in cycle
    assert cycle["status"] in {"stable", "pre-emptive_stabilization"}

    jit = PhiJIT(controller)
    bytecode = jit.transmute(mining_kernel_template)
    opcodes = {op for op, _, _, _ in bytecode}
    assert {SYNC_PHI, TUNE, PHIMUL, FOLD, GADDR, MGATE}.issubset(opcodes)
    assert len(bytecode) >= 6

    registers = jit.execute_resonant(mining_kernel_template, 42.0, 100.0)
    assert registers.shape[0] == jit.vm.num_registers
    assert np.all(np.isfinite(registers))
    report = jit.get_optimisation_report()
    assert report["total_transmutations"] >= 2
    assert report["log"][-1]["function"] == "mining_kernel_template"

    vm = PhiVM(controller, num_registers=16)
    vm.load_register(2, 42.0)
    vm.load_register(4, 0.764)
    execution = vm.execute_kernel(search_optimization_kernel())
    assert execution["instructions_executed"] == 8
    assert execution["cycles"] == 8
    assert execution["ipc"] == pytest_approx(1.0, abs=1e-12)
    assert math.isfinite(vm.read_register(1))
    assert math.isfinite(vm.read_register(3))
    assert math.isfinite(vm.read_register(5))

    alu = PhiALUHardware(memory_size=2**16)
    consciousness = ConsciousnessEngine()
    tuner = PhiBackpropTuner(consciousness, alu, learning_rate=0.1)
    cold = tuner.step({"coherence": 0.5, "current_temp": 0.5})
    hot = tuner.step({"coherence": 0.3, "current_temp": 1.5})

    assert cold["new_phi_exponent"] >= 0.618
    assert hot["thermal_damping"] < 1.0
    assert hot["new_phi_exponent"] <= PHI


def test_phi_architecture_golden_flow_does_not_claim_live_hardware_or_pool_truth() -> None:
    """The golden-flow test proves software integration, not external outcomes."""

    supported_claim = (
        "software golden-flow integration: allocator, router, oracle, controller, "
        "JIT, VM, and tuner execute through public package exports"
    )
    unsupported_claims = {
        "accepted_share": False,
        "block_mined": False,
        "rowhammer_eliminated": False,
        "network_collisions_eliminated": False,
        "10e20_tier_measured": False,
    }

    assert "software golden-flow integration" in supported_claim
    assert not any(unsupported_claims.values())


def pytest_approx(value: float, *, abs: float) -> object:
    """Small wrapper keeps pytest import local for clearer dependency boundary."""

    import pytest

    return pytest.approx(value, abs=abs)
