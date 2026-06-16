"""Tests for the consolidated PULVINI quantum operating-system façades."""

from __future__ import annotations

import asyncio

import pytest

try:
    import numpy as np
except ModuleNotFoundError:  # pragma: no cover - exercised only in minimal containers
    np = None

pytestmark = pytest.mark.skipif(
    np is None,
    reason="numpy is required for PULVINI numerical tests",
)


def _quantum_os_exports():
    from pythia_mining import (
        PULVINI_BINARY_HEADER_SIZE,
        PULVINI_BINARY_MAGIC,
        ConsciousnessEngine,
        ManifoldOperator,
        SubstateBinaryHeader,
        SubstateVerifier,
    )
    from pythia_mining.pulvini_topology import NUM_NODES

    return {
        "ConsciousnessEngine": ConsciousnessEngine,
        "ManifoldOperator": ManifoldOperator,
        "PULVINI_BINARY_HEADER_SIZE": PULVINI_BINARY_HEADER_SIZE,
        "PULVINI_BINARY_MAGIC": PULVINI_BINARY_MAGIC,
        "SubstateBinaryHeader": SubstateBinaryHeader,
        "SubstateVerifier": SubstateVerifier,
        "NUM_NODES": NUM_NODES,
    }


def test_manifold_operator_repairs_vectors_and_verifies_topology() -> None:
    exports = _quantum_os_exports()
    operator = exports["ManifoldOperator"]()
    NUM_NODES = exports["NUM_NODES"]
    state = np.ones(NUM_NODES, dtype=np.complex128)

    result = operator.evolve(state)

    assert result.state.shape == (NUM_NODES, NUM_NODES)
    assert np.allclose(result.state, result.state.conj().T)
    assert np.isclose(np.trace(result.state).real, 1.0)
    assert np.min(np.linalg.eigvalsh(result.state).real) >= -1e-10
    assert result.topology_verified is True
    assert operator.verify_topology()["group_order"] == 120


def test_manifold_operator_bures_distance_and_channel_certificate() -> None:
    exports = _quantum_os_exports()
    operator = exports["ManifoldOperator"]()
    NUM_NODES = exports["NUM_NODES"]
    basis_a = np.eye(NUM_NODES, dtype=np.complex128)[0]
    basis_b = np.eye(NUM_NODES, dtype=np.complex128)[1]
    hamiltonian = np.eye(NUM_NODES, dtype=np.complex128)

    same_distance = operator.compute_bures_distance(basis_a, basis_a)
    different_distance = operator.compute_bures_distance(basis_a, basis_b)
    cert = operator.certify_channel(hamiltonian)

    assert same_distance < 1e-6
    assert different_distance > same_distance
    assert cert.positive_semidefinite is True
    assert cert.trace_preservation_error < 1e-8


def test_consciousness_engine_orchestrates_operational_phi_proxy() -> None:
    exports = _quantum_os_exports()
    operator = exports["ManifoldOperator"]()
    engine = exports["ConsciousnessEngine"](operator=operator)
    NUM_NODES = exports["NUM_NODES"]
    history = []
    for phase in np.linspace(0.0, np.pi, 4):
        vector = np.exp(1j * phase * np.arange(NUM_NODES, dtype=np.float64))
        history.append(operator.ensure_density_state(vector))

    payload = engine.orchestrate(history[-1], history[:-1])

    assert 0.0 <= payload["coherence_meter"] <= 1.0
    assert payload["phi_metrics"]["source"] == "density_state_operational_proxy"
    assert payload["integration_regime"] in {
        "singular_agent_proxy",
        "distributed",
        "fragmented",
        "critical",
    }


def test_consciousness_engine_preserves_legacy_async_health_api() -> None:
    exports = _quantum_os_exports()
    engine = exports["ConsciousnessEngine"]()
    engine.update_component_health("quantum_solver", True)
    engine.update_component_health("stratum_client", True)

    level = asyncio.run(engine.get_consciousness_level())
    metrics = engine.get_metrics()

    assert level is not None
    assert metrics["active_components"] == 2
    assert metrics["source"] == "component_health_operational_proxy"


def test_substate_verifier_generates_hash_verified_passport() -> None:
    exports = _quantum_os_exports()
    verifier = exports["SubstateVerifier"]()
    NUM_NODES = exports["NUM_NODES"]
    rho = np.eye(NUM_NODES, dtype=np.complex128) / NUM_NODES

    passport = verifier.generate_passport(
        target=0x1D00FFFF,
        rho=rho,
        timestamp_ns=123456789,
    )
    payload = verifier.command_center_payload(passport)

    assert passport.verify_hash() is True
    assert verifier.verify_passport(passport) is True
    assert passport.topology_verified is True
    assert passport.coverage_verified is True
    assert passport.grover_scope_verified is True
    assert passport.quantum_speedup_claimed is False
    assert payload["status"] == "verified"


def test_substate_passport_binary_header_is_fixed_width() -> None:
    exports = _quantum_os_exports()
    verifier = exports["SubstateVerifier"]()
    NUM_NODES = exports["NUM_NODES"]
    rho = np.eye(NUM_NODES, dtype=np.complex128) / NUM_NODES
    signature = bytes(range(44))

    passport = verifier.generate_passport(
        target=0x1D00FFFF,
        rho=rho,
        timestamp_ns=123456789,
    )
    header_bytes = passport.to_binary_header(signature=signature)
    header = exports["SubstateBinaryHeader"].from_bytes(header_bytes)

    assert len(header_bytes) == exports["PULVINI_BINARY_HEADER_SIZE"] == 128
    assert header.magic == exports["PULVINI_BINARY_MAGIC"] == b"PULV"
    assert header.timestamp_ns == 123456789
    assert header.rho_hash.hex() == passport.rho_hash
    assert header.topology_hash.hex() == passport.structural_hash
    assert header.purity_fixed == passport.purity_fixed
    assert header.fidelity_fixed == passport.fidelity_fixed
    assert passport.verify_binary_header(header_bytes, signature=signature) is True
