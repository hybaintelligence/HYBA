"""Production-readiness tests for the PULVINI operator/verifier façades.

The tests intentionally exercise mathematical invariants rather than only API
shape: density states must stay Hermitian/PSD/trace-one, binary passports must
round-trip in network byte order, topology tampering must fail closed, and the
autonomic manifold must preserve coverage during live-cut and thermal cascades.
"""

from __future__ import annotations

import dataclasses
import struct
import sys
import time
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.consciousness_engine import ConsciousnessConfig, ConsciousnessEngine  # noqa: E402
from pythia_mining.pulvini_autonomics import (  # noqa: E402
    NodeTelemetry,
    PulviniAutonomicsEngine,
    ReducedDensityMatrix,
    ThermalGovernor,
)
from pythia_mining.pulvini_operator import (  # noqa: E402
    CoherenceClassification,
    ManifoldConfig,
    ManifoldOperator,
    ManifoldState,
)
from pythia_mining.pulvini_overlay import PulviniOverlayConcentrator  # noqa: E402
from pythia_mining.pulvini_topology import ADJACENCY_MAP, MAX_UINT32_NONCE, NUM_NODES  # noqa: E402
from pythia_mining.pulvini_verifier import (  # noqa: E402
    IntegrityStatus,
    PULVINI_BINARY_HEADER_SIZE,
    PULVINI_BINARY_MAGIC,
    SubstateBinaryHeader,
    SubstatePassport,
    SubstateVerifier,
)


@pytest.fixture()
def operator() -> ManifoldOperator:
    return ManifoldOperator()


@pytest.fixture()
def verifier(operator: ManifoldOperator) -> SubstateVerifier:
    return SubstateVerifier(operator=operator)


@pytest.fixture()
def identity_rho() -> np.ndarray:
    return np.eye(NUM_NODES, dtype=np.complex128) / NUM_NODES


def assert_density_state(rho: np.ndarray, *, places: int = 12) -> None:
    assert rho.shape == (NUM_NODES, NUM_NODES)
    assert np.all(np.isfinite(rho))
    assert np.allclose(rho, rho.conj().T, atol=10 ** -places)
    assert np.trace(rho).real == pytest.approx(1.0, abs=10 ** -places)
    assert np.min(np.linalg.eigvalsh(rho).real) >= -(10 ** -places)


# ---------------------------------------------------------------------------
# Tier 1: ManifoldOperator unit verification
# ---------------------------------------------------------------------------


def test_apply_choi_map_repairs_non_hermitian_negative_and_bad_trace(operator: ManifoldOperator) -> None:
    bad_rho = np.eye(NUM_NODES, dtype=np.complex128) * 5.0
    bad_rho[0, 1] = 3.0 + 7.0j
    bad_rho[1, 0] = -2.0j
    bad_rho[2, 2] = -10.0

    repaired = operator.apply_choi_map(bad_rho)

    assert_density_state(repaired)
    assert repaired[0, 1] == pytest.approx(repaired[1, 0].conjugate())


def test_density_repair_handles_zero_spectrum_and_near_zero_values(operator: ManifoldOperator) -> None:
    zero_repaired = operator.apply_choi_map(np.zeros((NUM_NODES, NUM_NODES), dtype=np.complex128))
    tiny_repaired = operator.apply_choi_map(np.eye(NUM_NODES, dtype=np.complex128) * 1e-18)

    assert_density_state(zero_repaired)
    assert_density_state(tiny_repaired)
    assert np.allclose(np.diag(zero_repaired).real, np.ones(NUM_NODES) / NUM_NODES)
    assert np.allclose(np.diag(tiny_repaired).real, np.ones(NUM_NODES) / NUM_NODES)


@pytest.mark.parametrize("poison", [np.nan, np.inf, -np.inf])
def test_density_repair_rejects_nan_and_inf_without_crashing(operator: ManifoldOperator, poison: float) -> None:
    chaos = np.eye(NUM_NODES, dtype=np.complex128) / NUM_NODES
    chaos[5, 5] = poison

    with pytest.raises(ValueError, match="NaN|infinite"):
        operator.apply_choi_map(chaos)


def test_density_repair_promotes_vectors_and_rejects_invalid_shapes(operator: ManifoldOperator) -> None:
    vector = np.ones(NUM_NODES, dtype=np.complex128)
    repaired = operator.ensure_density_state(vector)

    assert_density_state(repaired)
    assert operator.compute_coherence(repaired) > 0.0
    with pytest.raises(ValueError, match="dimension"):
        operator.ensure_density_state(np.ones(NUM_NODES - 1, dtype=np.complex128))
    with pytest.raises(ValueError, match="norm"):
        operator.ensure_density_state(np.zeros(NUM_NODES, dtype=np.complex128))
    with pytest.raises(ValueError, match="shape"):
        operator.ensure_density_state(np.eye(NUM_NODES - 1, dtype=np.complex128))
    with pytest.raises(ValueError, match="vector or square"):
        operator.ensure_density_state(np.zeros((2, 2, 2), dtype=np.complex128))


def test_uhlmann_fidelity_and_bures_geometry_axioms(operator: ManifoldOperator) -> None:
    rho_a = np.zeros((NUM_NODES, NUM_NODES), dtype=np.complex128)
    rho_b = np.zeros((NUM_NODES, NUM_NODES), dtype=np.complex128)
    rho_a[0, 0] = 1.0
    rho_b[1, 1] = 1.0

    assert operator.compute_uhlmann_fidelity(rho_a, rho_a) == pytest.approx(1.0, abs=1e-12)
    assert operator.compute_bures_distance(rho_a, rho_a) == pytest.approx(0.0, abs=1e-12)
    assert operator.compute_uhlmann_fidelity(rho_a, rho_b) == pytest.approx(0.0, abs=1e-12)
    assert operator.compute_uhlmann_fidelity(rho_a, rho_b) == pytest.approx(
        operator.compute_uhlmann_fidelity(rho_b, rho_a), abs=1e-12
    )
    assert operator.compute_bures_distance(rho_a, rho_b) == pytest.approx(np.sqrt(2.0), abs=1e-12)


def test_state_classification_and_dashboard_coherence_mapping(operator: ManifoldOperator, identity_rho: np.ndarray) -> None:
    coherent_vector = np.ones(NUM_NODES, dtype=np.complex128)
    coherent = operator.ensure_density_state(coherent_vector)
    pure_basis = np.zeros((NUM_NODES, NUM_NODES), dtype=np.complex128)
    pure_basis[0, 0] = 1.0

    assert operator.classify_state(coherent) is ManifoldState.COHERENT
    assert operator.classify_state(identity_rho) is ManifoldState.MIXED
    assert operator.classify_state(pure_basis) is ManifoldState.DECOHERENT

    green = operator.get_coherence_metrics(coherent, coherent)
    red = operator.get_coherence_metrics(pure_basis, coherent)
    assert green["classification"] is CoherenceClassification.COHERENT
    assert green["ui_state"] == "green"
    assert red["classification"] is CoherenceClassification.DECOHERENT
    assert red["ui_state"] == "red"
    assert red["bures_distance"] > 0.75


def test_operator_evolution_channel_gamma_and_snapshot(operator: ManifoldOperator) -> None:
    state = np.exp(1j * np.arange(NUM_NODES, dtype=np.float64))
    target = np.eye(NUM_NODES, dtype=np.complex128)[0]

    evolution = operator.evolve(state, target=target)
    gamma_before = operator.gamma_ledger.estimate(0).gamma
    gamma_after = operator.record_gamma(0, nack=True).gamma
    jumps = operator.jump_operators_for_node(0)
    channel = operator.certify_channel(np.eye(NUM_NODES, dtype=np.complex128))
    choi = operator.choi_matrix(np.eye(NUM_NODES, dtype=np.complex128))
    topology_first = operator.verify_topology()
    topology_second = operator.verify_topology()
    snapshot = operator.snapshot()

    assert_density_state(evolution.state)
    assert evolution.to_dict()["topology_verified"] is True
    assert evolution.bures_distance_to_target is not None
    assert gamma_after > gamma_before
    assert jumps and all(jump.shape == (NUM_NODES, NUM_NODES) for jump in jumps)
    assert channel.positive_semidefinite is True
    assert choi.shape == (NUM_NODES * NUM_NODES, NUM_NODES * NUM_NODES)
    assert topology_first["group_order"] == 120
    assert topology_second["adjacency_map_sha256"] == topology_first["adjacency_map_sha256"]
    assert snapshot["state_count"] == 1
    assert operator.state_history[-1].shape == (NUM_NODES, NUM_NODES)
    assert operator.coherence_trend


def test_operator_constructor_rejects_invalid_configurations() -> None:
    with pytest.raises(ValueError, match="dimension"):
        ManifoldOperator(config=ManifoldConfig(dimension=NUM_NODES - 1))
    with pytest.raises(ValueError, match="positive"):
        ManifoldOperator(config=ManifoldConfig(gamma_normalization=0.0))


# ---------------------------------------------------------------------------
# Tier 2: SubstateVerifier contract verification
# ---------------------------------------------------------------------------


def test_passport_binary_header_round_trip_and_big_endian(verifier: SubstateVerifier) -> None:
    pure = np.zeros((NUM_NODES, NUM_NODES), dtype=np.complex128)
    pure[0, 0] = 1.0
    signature = b"HYBA_SIG_" + (b"0" * 35)
    passport = verifier.generate_passport(rho=pure, timestamp_ns=123_456_789, use_cache=False)

    header_bytes = passport.to_binary_header(signature=signature)
    unpacked_tuple = struct.unpack(">4sQ32sII32s44s", header_bytes)
    parsed = SubstateBinaryHeader.from_bytes(header_bytes)
    audit = verifier.verify_binary_header(header_bytes, signature=signature)

    assert len(header_bytes) == PULVINI_BINARY_HEADER_SIZE == 128
    assert unpacked_tuple[0] == PULVINI_BINARY_MAGIC == b"PULV"
    assert unpacked_tuple[1] == 123_456_789
    assert unpacked_tuple[3] == 1_000_000_000
    assert unpacked_tuple[4] == 1_000_000_000
    assert parsed.signature == signature
    assert passport.verify_binary_header(header_bytes, signature=signature) is True
    assert audit["verified"] is True
    assert audit["timestamp_ns"] == 123_456_789
    assert audit["purity"] == pytest.approx(passport.purity, abs=1e-9)
    assert audit["fidelity"] == pytest.approx(passport.fidelity, abs=1e-9)


def test_binary_header_fail_closed_cases(verifier: SubstateVerifier, identity_rho: np.ndarray) -> None:
    passport = verifier.generate_passport(rho=identity_rho, timestamp_ns=987_654_321, use_cache=False)
    header = passport.to_binary_header()
    tampered_magic = b"FAIL" + header[4:]
    tampered_signature = header[:-1] + b"x"

    assert verifier.verify_binary_header(header[:-1])["verified"] is False
    assert verifier.verify_binary_header(tampered_magic)["verified"] is False
    assert verifier.verify_binary_header(tampered_signature)["verified"] is False
    assert passport.verify_binary_header(tampered_signature) is False
    with pytest.raises(ValueError, match="44 bytes"):
        passport.to_binary_header(signature=b"short")
    with pytest.raises(ValueError, match="rho_hash"):
        SubstateBinaryHeader(timestamp_ns=1, rho_hash=b"bad", purity_fixed=0, fidelity_fixed=0, topology_hash=b"0" * 32)
    with pytest.raises(ValueError, match="purity_fixed"):
        SubstateBinaryHeader(
            timestamp_ns=1,
            rho_hash=b"0" * 32,
            purity_fixed=1_000_000_001,
            fidelity_fixed=0,
            topology_hash=b"0" * 32,
        )


def test_passport_hashing_cache_and_command_payload(verifier: SubstateVerifier, identity_rho: np.ndarray) -> None:
    ts = 1_686_528_000_000_000_000
    passport_a = verifier.generate_passport(target=0x1D00FFFF, rho=identity_rho, timestamp_ns=ts)
    passport_b = verifier.generate_passport(target=0x1D00FFFF, rho=identity_rho, timestamp_ns=ts)
    payload = verifier.command_center_payload(passport_a)
    blob = passport_a.to_blob()

    assert passport_a is passport_b
    assert passport_a.rho_hash == passport_b.rho_hash
    assert passport_a.passport_hash == passport_b.passport_hash
    assert passport_a.verify(passport_b) is True
    assert verifier.verify_passport(passport_a) is True
    assert blob.startswith(b"{") and b"passport_hash" in blob
    assert payload["binary_header_size"] == 128
    assert payload["purity"] == pytest.approx(passport_a.purity, abs=1e-9)
    assert payload["fidelity"] == pytest.approx(passport_a.fidelity, abs=1e-9)
    assert passport_a.grover_scope == pytest.approx(1.0)


def test_passport_detects_digest_status_and_speedup_tampering(verifier: SubstateVerifier, identity_rho: np.ndarray) -> None:
    passport = verifier.generate_passport(rho=identity_rho, timestamp_ns=42, use_cache=False)
    bad_status = dataclasses.replace(passport, status=IntegrityStatus.FAILED.value)
    bad_speedup = dataclasses.replace(passport, quantum_speedup_claimed=True)
    bad_digest = dataclasses.replace(passport, structural_hash="f" * 64)

    assert bad_status.verify_hash() is False
    assert verifier.verify_passport(bad_status) is False
    assert verifier.verify_passport(bad_speedup) is False
    assert bad_digest.verify_hash() is False
    assert bad_digest.verify(passport) is False


def test_topology_tampering_blocks_passport_generation(verifier: SubstateVerifier, identity_rho: np.ndarray) -> None:
    tampered_31_nodes = {node: dict(edges) for node, edges in ADJACENCY_MAP.items() if node != NUM_NODES - 1}
    tampered_non_di = {node: {kind: list(values) for kind, values in edges.items()} for node, edges in ADJACENCY_MAP.items()}
    tampered_non_di[0]["D"] = sorted(set(tampered_non_di[0].get("D", [])) | {1})

    assert verifier.verify_topology(identity_rho) is True
    assert verifier.verify_topology_map(tampered_31_nodes) is False
    assert verifier.verify_topology_map(tampered_non_di) is False

    broken_operator = ManifoldOperator(adjacency_map=tampered_non_di)
    broken_verifier = SubstateVerifier(operator=broken_operator)
    passport = broken_verifier.generate_passport(rho=identity_rho, timestamp_ns=101, use_cache=False)
    assert passport.topology_verified is False
    assert passport.status == IntegrityStatus.FAILED.value
    assert broken_verifier.verify_passport(passport) is False


def test_passport_choi_and_bures_contracts(verifier: SubstateVerifier, identity_rho: np.ndarray) -> None:
    hamiltonian = np.eye(NUM_NODES, dtype=np.complex128)
    reference = np.zeros((NUM_NODES, NUM_NODES), dtype=np.complex128)
    reference[0, 0] = 1.0

    passport = verifier.generate_passport(
        target=0x1D00FFFF,
        rho=identity_rho,
        reference_rho=reference,
        entropy_rate=0.0,
        hamiltonian=hamiltonian,
        nonce_ranges=[(0, MAX_UINT32_NONCE)],
        timestamp_ns=202,
        use_cache=False,
    )

    assert passport.choi_verified is True
    assert passport.bures_closed is True
    assert passport.topology_verified is True
    assert passport.coverage_verified is True
    assert passport.grover_scope_verified is True
    assert passport.quantum_speedup_claimed is False
    assert passport.information_content == pytest.approx(np.log2(NUM_NODES), abs=1e-9)
    assert 0.0 <= passport.fidelity <= 1.0


# ---------------------------------------------------------------------------
# Tier 3: ConsciousnessEngine integration verification
# ---------------------------------------------------------------------------


def test_disconnected_node_phi_dip_triggers_autonomic_reflex_within_100ms(operator: ManifoldOperator) -> None:
    engine = ConsciousnessEngine(
        operator=operator,
        config=ConsciousnessConfig(heal_trigger_threshold=0.30, measurement_window=10),
    )
    healthy = operator.ensure_density_state(np.ones(NUM_NODES, dtype=np.complex128))
    disconnected = np.zeros((NUM_NODES, NUM_NODES), dtype=np.complex128)
    disconnected[0, 0] = 1.0

    start = time.perf_counter()
    payload = engine.orchestrate(disconnected, [healthy, healthy])
    elapsed_ms = (time.perf_counter() - start) * 1_000.0

    assert payload["phi_metrics"]["phi_integrated"] < 0.30
    assert payload["autonomic_action"] == "healing_triggered"
    assert payload["integration_regime"] == "critical"
    assert engine.needs_healing is True
    assert engine.get_metrics()["autonomic_events"][-1]["type"] == "AUTONOMIC_HEAL"
    assert elapsed_ms < 100.0


# ---------------------------------------------------------------------------
# Tier 4: Autonomic stress testing / live-cut drills
# ---------------------------------------------------------------------------


def _telemetry_with_hot_nodes(hot_nodes: set[int], *, hot_entropy: float) -> list[NodeTelemetry]:
    return [
        NodeTelemetry(
            node_id=node_id,
            tres=1.0,
            phi_eff=0.99,
            chi_sync=0.99,
            thermal_entropy=hot_entropy if node_id in hot_nodes else 0.20,
            hash_rate=1_000.0,
        )
        for node_id in range(NUM_NODES)
    ]


def test_n3_wipeout_reassigns_nonce_ranges_with_zero_overlap() -> None:
    engine = PulviniAutonomicsEngine()
    event = engine.rebalancer.rebalance_lattice_topology([0, 1, 2], reason="N=3_live_cut")
    ranges = [tuple(command["nonce_range"]) for command in event.lattice_commands]

    assert event.failed_nodes == [0, 1, 2]
    assert event.coverage_maintained is True
    assert event.rho_trace == pytest.approx(1.0, abs=1e-12)
    assert len(ranges) == len(set(ranges))
    for index, (start, end) in enumerate(ranges):
        assert start <= end, f"range {index} must be non-empty"
        for other_start, other_end in ranges[index + 1 :]:
            assert end < other_start or other_end < start


def test_thermal_cascade_fades_hot_nodes_and_redistributes_amplitude_to_cool_nodes() -> None:
    governor = ThermalGovernor()
    rho = ReducedDensityMatrix()
    hot_nodes = {0, 1, 2, 3, 4}
    telemetry = _telemetry_with_hot_nodes(hot_nodes, hot_entropy=0.90)

    evolved, event = governor.apply_thermal_governance(rho, telemetry)
    before = np.ones(NUM_NODES) / NUM_NODES
    after = np.asarray(event.amplitudes)

    assert_density_state(evolved)
    assert set(event.faded_nodes) == hot_nodes
    assert event.sacrificed_nodes == []
    assert event.redistributed_amplitude > 0.0
    assert after[list(hot_nodes)].sum() < before[list(hot_nodes)].sum()
    assert after[[node for node in range(NUM_NODES) if node not in hot_nodes]].sum() > before[
        [node for node in range(NUM_NODES) if node not in hot_nodes]
    ].sum()


def test_thermal_sacrifice_triggers_rebalance_and_autonomic_snapshot() -> None:
    engine = PulviniAutonomicsEngine()
    hot_nodes = {0, 1, 2, 3, 4}
    telemetry = _telemetry_with_hot_nodes(hot_nodes, hot_entropy=0.99)

    event, rebalance = engine.thermal_tick(telemetry)
    snapshot = engine.snapshot()

    assert set(event.sacrificed_nodes) == hot_nodes
    assert rebalance is not None
    assert rebalance.coverage_maintained is True
    assert set(snapshot["sacrificed_nodes"]) == hot_nodes
    assert snapshot["thermal"][-1]["redistributed_amplitude"] > 0.0
    assert snapshot["rebalances"][-1]["failed_nodes"] == sorted(hot_nodes)


def test_autonomic_ledger_records_healed_state() -> None:
    overlay = PulviniOverlayConcentrator(worker_name="hyba-test-worker")
    overlay.record_autonomic_event(
        {
            "event_type": "Healed",
            "node_id": 0,
            "state": "Healed",
            "reason": "production_facade_validation",
        }
    )
    snapshot = overlay.snapshot()

    assert any(event.get("state") == "Healed" for event in snapshot["autonomic_ledger"])
    assert snapshot["autonomic_ledger"][-1]["event_type"] == "Healed"
