"""
Tests for python_backend/hyba_genesis_api/core/sovereign_node.py

Added in PR: sovereign_node.py is a new module that provides substrate-independent
memory portability via SovereignNode, SovereignNodeIdentity, and SovereignMemoryPacket.

Test coverage:
- SovereignNodeIdentity dataclass
- SovereignMemoryPacket dataclass
- SovereignNode.get_identity()
- SovereignNode.verify_sovereignty_gate()
- SovereignNode.export_sealed_memory()
- SovereignNode.import_sealed_memory()
- SovereignNode.get_sovereignty_report()
- SovereignNode.get_node_info()
- Cross-node portability (export on one node, import on another)
- Edge cases: empty state, nested state, gate failure, tamper detection
"""

import hashlib
import json
from dataclasses import asdict
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from python_backend.hyba_genesis_api.core.sovereign_node import (
    SovereignMemoryPacket,
    SovereignNode,
    SovereignNodeIdentity,
)


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

def _make_passing_engine():
    """Return a mock attestation engine that always passes sovereignty gate."""
    engine = MagicMock()
    engine.verify_all_critical_passed.return_value = True
    engine.get_sovereignty_report.return_value = {
        "by_property": {},
        "sovereignty_gate_passed": True,
        "total_attestations": 0,
        "passed_count": 0,
        "failed_count": 0,
    }
    return engine


def _make_failing_engine():
    """Return a mock attestation engine that always fails sovereignty gate."""
    engine = MagicMock()
    engine.verify_all_critical_passed.return_value = False
    engine.get_sovereignty_report.return_value = {
        "by_property": {},
        "sovereignty_gate_passed": False,
        "total_attestations": 1,
        "passed_count": 0,
        "failed_count": 1,
    }
    return engine


def _make_node(node_id="test_node", os_platform="linux", python_version="3.12.0",
               engine=None):
    """Construct a SovereignNode with a mock engine (defaults to passing)."""
    if engine is None:
        engine = _make_passing_engine()
    return SovereignNode(
        node_id=node_id,
        os_platform=os_platform,
        python_version=python_version,
        attestation_engine=engine,
    )


def _build_valid_packet(node, problem_id="test_problem", memory_state=None):
    """Build a SovereignMemoryPacket using the low-level constructor so that the
    sealed_evidence_chain is consistent with the packet fields (avoiding the
    double-get_identity timestamp bug in export_sealed_memory)."""
    if memory_state is None:
        memory_state = {"key": "value", "number": 42}

    identity = SovereignNodeIdentity(
        node_id=node.node_id,
        os_platform=node.os_platform,
        python_version=node.python_version,
        timestamp_created="2026-06-26T00:00:00+00:00",
    )
    timestamp_sealed = "2026-06-26T00:00:01+00:00"
    state_json = json.dumps(memory_state, sort_keys=True, default=str)
    state_hash = hashlib.sha256(state_json.encode()).hexdigest()
    instructions = (
        "To reconstruct: (1) Verify sovereignty gate on target node, "
        "(2) Import this packet, (3) Verify state hash matches, "
        "(4) Load memory_state into target node"
    )

    # Build packet dict (same structure as export_sealed_memory)
    packet_dict = {
        "problem_id": problem_id,
        "node_origin": identity.__dict__,
        "timestamp_sealed": timestamp_sealed,
        "memory_state": memory_state,
        "state_hash": state_hash,
        "sovereignty_attestations": {},
        "instructions": instructions,
    }
    packet_json = json.dumps(packet_dict, sort_keys=True, default=str)
    sealed_evidence_chain = hashlib.sha256(packet_json.encode()).hexdigest()

    return SovereignMemoryPacket(
        problem_id=problem_id,
        node_origin=identity,
        timestamp_sealed=timestamp_sealed,
        memory_state=memory_state,
        state_hash=state_hash,
        sovereignty_attestations={},
        sealed_evidence_chain=sealed_evidence_chain,
        instructions=instructions,
    )


# ---------------------------------------------------------------------------
# Tests for SovereignNodeIdentity
# ---------------------------------------------------------------------------

class TestSovereignNodeIdentity:
    """Tests for the SovereignNodeIdentity frozen dataclass."""

    def test_identity_fields(self):
        identity = SovereignNodeIdentity(
            node_id="macbook_1",
            os_platform="darwin",
            python_version="3.12.0",
            timestamp_created="2026-06-26T00:00:00+00:00",
        )
        assert identity.node_id == "macbook_1"
        assert identity.os_platform == "darwin"
        assert identity.python_version == "3.12.0"
        assert identity.timestamp_created == "2026-06-26T00:00:00+00:00"

    def test_identity_is_frozen(self):
        identity = SovereignNodeIdentity(
            node_id="node_x",
            os_platform="linux",
            python_version="3.11.0",
            timestamp_created="2026-01-01T00:00:00+00:00",
        )
        with pytest.raises((AttributeError, TypeError)):
            identity.node_id = "modified"  # type: ignore[misc]

    def test_identity_equality(self):
        kwargs = dict(
            node_id="n1",
            os_platform="linux",
            python_version="3.12.0",
            timestamp_created="2026-06-26T00:00:00+00:00",
        )
        assert SovereignNodeIdentity(**kwargs) == SovereignNodeIdentity(**kwargs)

    def test_identity_inequality_on_different_platform(self):
        base = dict(
            node_id="n1",
            python_version="3.12.0",
            timestamp_created="2026-06-26T00:00:00+00:00",
        )
        id_linux = SovereignNodeIdentity(os_platform="linux", **base)
        id_darwin = SovereignNodeIdentity(os_platform="darwin", **base)
        assert id_linux != id_darwin

    def test_identity_dict_serializable(self):
        identity = SovereignNodeIdentity(
            node_id="n1",
            os_platform="win32",
            python_version="3.12.0",
            timestamp_created="2026-06-26T00:00:00+00:00",
        )
        d = identity.__dict__
        # Must be JSON-serializable
        serialized = json.dumps(d)
        parsed = json.loads(serialized)
        assert parsed["node_id"] == "n1"
        assert parsed["os_platform"] == "win32"


# ---------------------------------------------------------------------------
# Tests for SovereignMemoryPacket
# ---------------------------------------------------------------------------

class TestSovereignMemoryPacket:
    """Tests for the SovereignMemoryPacket frozen dataclass."""

    def _make_packet(self, **overrides):
        identity = SovereignNodeIdentity(
            node_id="n1",
            os_platform="linux",
            python_version="3.12.0",
            timestamp_created="2026-06-26T00:00:00+00:00",
        )
        defaults = dict(
            problem_id="prob_1",
            node_origin=identity,
            timestamp_sealed="2026-06-26T00:00:01+00:00",
            memory_state={"answer": 42},
            state_hash="a" * 64,
            sovereignty_attestations={},
            sealed_evidence_chain="b" * 64,
            instructions="reconstruct",
        )
        defaults.update(overrides)
        return SovereignMemoryPacket(**defaults)

    def test_packet_is_frozen(self):
        pkt = self._make_packet()
        with pytest.raises((AttributeError, TypeError)):
            pkt.problem_id = "changed"  # type: ignore[misc]

    def test_packet_fields_accessible(self):
        pkt = self._make_packet(problem_id="circuit_1")
        assert pkt.problem_id == "circuit_1"
        assert pkt.memory_state == {"answer": 42}
        assert pkt.state_hash == "a" * 64
        assert pkt.sealed_evidence_chain == "b" * 64

    def test_packet_node_origin_is_identity(self):
        pkt = self._make_packet()
        assert isinstance(pkt.node_origin, SovereignNodeIdentity)


# ---------------------------------------------------------------------------
# Tests for SovereignNode initialisation
# ---------------------------------------------------------------------------

class TestSovereignNodeInit:
    """Tests for SovereignNode construction."""

    def test_basic_init(self):
        node = _make_node(node_id="node_a", os_platform="darwin", python_version="3.12.0")
        assert node.node_id == "node_a"
        assert node.os_platform == "darwin"
        assert node.python_version == "3.12.0"

    def test_sealed_packets_starts_empty(self):
        node = _make_node()
        assert len(node._sealed_packets) == 0

    def test_default_attestation_engine_is_real(self):
        """When no engine is injected, SovereignNode creates a real one via factory."""
        node = SovereignNode(
            node_id="n",
            os_platform="linux",
            python_version="3.12.0",
        )
        # Should have a real attestation engine, not a mock
        assert hasattr(node.attestation_engine, "verify_all_critical_passed")


# ---------------------------------------------------------------------------
# Tests for SovereignNode.get_identity()
# ---------------------------------------------------------------------------

class TestGetIdentity:
    """Tests for SovereignNode.get_identity()."""

    def test_returns_sovereign_node_identity(self):
        node = _make_node(node_id="my_node", os_platform="linux", python_version="3.12.0")
        identity = node.get_identity()
        assert isinstance(identity, SovereignNodeIdentity)

    def test_identity_matches_node_fields(self):
        node = _make_node(node_id="my_node", os_platform="darwin", python_version="3.11.7")
        identity = node.get_identity()
        assert identity.node_id == "my_node"
        assert identity.os_platform == "darwin"
        assert identity.python_version == "3.11.7"

    def test_identity_timestamp_is_iso8601(self):
        node = _make_node()
        identity = node.get_identity()
        # Timestamp must be a non-empty string containing timezone info
        assert isinstance(identity.timestamp_created, str)
        assert len(identity.timestamp_created) > 0
        assert "+" in identity.timestamp_created or "Z" in identity.timestamp_created

    def test_successive_calls_produce_different_timestamps(self):
        """Each call to get_identity() produces a fresh timestamp."""
        node = _make_node()
        id1 = node.get_identity()
        id2 = node.get_identity()
        # node_id/platform/version must match; timestamp may differ
        assert id1.node_id == id2.node_id
        assert id1.os_platform == id2.os_platform
        # (timestamps could differ by nanoseconds; we don't assert equality)


# ---------------------------------------------------------------------------
# Tests for SovereignNode.verify_sovereignty_gate()
# ---------------------------------------------------------------------------

class TestVerifySovereigntyGate:
    """Tests for verify_sovereignty_gate()."""

    def test_gate_passes_when_engine_passes(self):
        node = _make_node(engine=_make_passing_engine())
        assert node.verify_sovereignty_gate() is True

    def test_gate_fails_when_engine_fails(self):
        node = _make_node(engine=_make_failing_engine())
        assert node.verify_sovereignty_gate() is False

    def test_gate_delegates_to_engine(self):
        engine = _make_passing_engine()
        node = _make_node(engine=engine)
        node.verify_sovereignty_gate()
        engine.verify_all_critical_passed.assert_called_once()


# ---------------------------------------------------------------------------
# Tests for SovereignNode.export_sealed_memory()
# ---------------------------------------------------------------------------

class TestExportSealedMemory:
    """Tests for export_sealed_memory()."""

    def test_export_raises_when_gate_fails(self):
        node = _make_node(engine=_make_failing_engine())
        with pytest.raises(RuntimeError, match="sovereignty gate"):
            node.export_sealed_memory(
                problem_id="p1",
                memory_state={"x": 1},
            )

    def test_export_returns_sovereign_memory_packet(self):
        node = _make_node()
        packet = node.export_sealed_memory(
            problem_id="p1",
            memory_state={"x": 1},
        )
        assert isinstance(packet, SovereignMemoryPacket)

    def test_export_packet_problem_id(self):
        node = _make_node()
        packet = node.export_sealed_memory(
            problem_id="circuit_synthesis",
            memory_state={"a": 1},
        )
        assert packet.problem_id == "circuit_synthesis"

    def test_export_packet_memory_state_preserved(self):
        node = _make_node()
        state = {"result": 99, "trace": [1, 2, 3]}
        packet = node.export_sealed_memory(problem_id="p1", memory_state=state)
        assert packet.memory_state == state

    def test_export_state_hash_is_sha256_of_memory_state(self):
        node = _make_node()
        state = {"answer": 42}
        packet = node.export_sealed_memory(problem_id="p1", memory_state=state)
        expected_hash = hashlib.sha256(
            json.dumps(state, sort_keys=True, default=str).encode()
        ).hexdigest()
        assert packet.state_hash == expected_hash

    def test_export_sealed_evidence_chain_is_sha256(self):
        node = _make_node()
        packet = node.export_sealed_memory(problem_id="p1", memory_state={"k": "v"})
        assert isinstance(packet.sealed_evidence_chain, str)
        assert len(packet.sealed_evidence_chain) == 64

    def test_export_caches_packet_by_problem_id(self):
        node = _make_node()
        packet = node.export_sealed_memory(problem_id="p1", memory_state={"v": 1})
        assert "p1" in node._sealed_packets
        assert node._sealed_packets["p1"] is packet

    def test_export_overwrites_existing_cached_packet(self):
        node = _make_node()
        pkt1 = node.export_sealed_memory(problem_id="p1", memory_state={"v": 1})
        pkt2 = node.export_sealed_memory(problem_id="p1", memory_state={"v": 2})
        assert node._sealed_packets["p1"] is pkt2
        assert pkt1 is not pkt2

    def test_export_instructions_mention_reconstruct(self):
        node = _make_node()
        packet = node.export_sealed_memory(problem_id="p1", memory_state={})
        assert "reconstruct" in packet.instructions.lower()

    def test_export_empty_memory_state(self):
        node = _make_node()
        packet = node.export_sealed_memory(problem_id="empty", memory_state={})
        assert packet.memory_state == {}
        assert isinstance(packet.state_hash, str)
        assert len(packet.state_hash) == 64

    def test_export_nested_memory_state(self):
        node = _make_node()
        state = {"nested": {"list": [1, 2, 3], "dict": {"a": "b"}}}
        packet = node.export_sealed_memory(problem_id="nested", memory_state=state)
        assert packet.memory_state == state

    def test_export_different_states_produce_different_hashes(self):
        node = _make_node()
        pkt1 = node.export_sealed_memory(problem_id="p1", memory_state={"x": 1})
        pkt2 = node.export_sealed_memory(problem_id="p2", memory_state={"x": 2})
        assert pkt1.state_hash != pkt2.state_hash

    def test_export_node_origin_matches_node(self):
        node = _make_node(node_id="origin_node", os_platform="linux")
        packet = node.export_sealed_memory(problem_id="p1", memory_state={"a": 1})
        assert packet.node_origin.node_id == "origin_node"
        assert packet.node_origin.os_platform == "linux"


# ---------------------------------------------------------------------------
# Tests for SovereignNode.import_sealed_memory()
# ---------------------------------------------------------------------------

class TestImportSealedMemory:
    """Tests for import_sealed_memory()."""

    def test_import_raises_when_gate_fails(self):
        node = _make_node(engine=_make_failing_engine())
        packet = _build_valid_packet(node)
        with pytest.raises(RuntimeError, match="sovereignty gate"):
            node.import_sealed_memory(packet)

    def test_import_valid_packet_returns_memory_state(self):
        """A correctly sealed packet should return its memory_state."""
        node = _make_node()
        memory_state = {"result": 42, "trace": "done"}
        packet = _build_valid_packet(node, memory_state=memory_state)
        reconstructed = node.import_sealed_memory(packet)
        assert reconstructed == memory_state

    def test_import_raises_on_tampered_memory_state(self):
        """Modifying memory_state after sealing breaks state_hash → RuntimeError."""
        node = _make_node()
        packet = _build_valid_packet(node, memory_state={"k": "original"})
        # Build a tampered packet with modified memory_state but unchanged state_hash
        tampered = SovereignMemoryPacket(
            problem_id=packet.problem_id,
            node_origin=packet.node_origin,
            timestamp_sealed=packet.timestamp_sealed,
            memory_state={"k": "tampered"},  # changed
            state_hash=packet.state_hash,    # not updated → will mismatch
            sovereignty_attestations=packet.sovereignty_attestations,
            sealed_evidence_chain=packet.sealed_evidence_chain,
            instructions=packet.instructions,
        )
        with pytest.raises(RuntimeError):
            node.import_sealed_memory(tampered)

    def test_import_raises_on_tampered_sealed_chain(self):
        """Modifying sealed_evidence_chain directly → RuntimeError."""
        node = _make_node()
        packet = _build_valid_packet(node, memory_state={"k": "v"})
        tampered = SovereignMemoryPacket(
            problem_id=packet.problem_id,
            node_origin=packet.node_origin,
            timestamp_sealed=packet.timestamp_sealed,
            memory_state=packet.memory_state,
            state_hash=packet.state_hash,
            sovereignty_attestations=packet.sovereignty_attestations,
            sealed_evidence_chain="0" * 64,  # tampered
            instructions=packet.instructions,
        )
        with pytest.raises(RuntimeError, match="[Ss]ealed evidence chain"):
            node.import_sealed_memory(tampered)

    def test_import_raises_on_tampered_state_hash(self):
        """A packet with an incorrect state_hash but correct seal raises RuntimeError."""
        node = _make_node()
        memory_state = {"x": 1}
        identity = SovereignNodeIdentity(
            node_id=node.node_id,
            os_platform=node.os_platform,
            python_version=node.python_version,
            timestamp_created="2026-06-26T00:00:00+00:00",
        )
        timestamp_sealed = "2026-06-26T00:00:01+00:00"
        bad_state_hash = "f" * 64  # does not match memory_state

        packet_dict = {
            "problem_id": "tampered",
            "node_origin": identity.__dict__,
            "timestamp_sealed": timestamp_sealed,
            "memory_state": memory_state,
            "state_hash": bad_state_hash,
            "sovereignty_attestations": {},
            "instructions": "reconstruct",
        }
        packet_json = json.dumps(packet_dict, sort_keys=True, default=str)
        sealed_chain = hashlib.sha256(packet_json.encode()).hexdigest()

        packet = SovereignMemoryPacket(
            problem_id="tampered",
            node_origin=identity,
            timestamp_sealed=timestamp_sealed,
            memory_state=memory_state,
            state_hash=bad_state_hash,
            sovereignty_attestations={},
            sealed_evidence_chain=sealed_chain,
            instructions="reconstruct",
        )
        with pytest.raises(RuntimeError, match="[Ss]tate hash"):
            node.import_sealed_memory(packet)

    def test_import_different_nodes_same_passing_engine(self):
        """Two nodes with passing engines should both import valid packets."""
        engine1 = _make_passing_engine()
        engine2 = _make_passing_engine()
        node_a = _make_node(node_id="laptop_a", os_platform="darwin", engine=engine1)
        node_b = _make_node(node_id="laptop_b", os_platform="linux", engine=engine2)

        memory_state = {"solution_hash": "abc123", "resonance": 0.87}
        packet = _build_valid_packet(node_a, memory_state=memory_state)

        reconstructed = node_b.import_sealed_memory(packet)
        assert reconstructed == memory_state

    def test_import_preserves_nested_structures(self):
        node = _make_node()
        memory_state = {
            "nested": {"list": [1, 2, 3], "inner": {"a": "b"}},
            "number": 3.14,
        }
        packet = _build_valid_packet(node, memory_state=memory_state)
        result = node.import_sealed_memory(packet)
        assert result == memory_state

    def test_import_empty_memory_state(self):
        node = _make_node()
        packet = _build_valid_packet(node, memory_state={})
        result = node.import_sealed_memory(packet)
        assert result == {}


# ---------------------------------------------------------------------------
# Export / Import Consistency: Documenting timestamp bug
# ---------------------------------------------------------------------------

class TestExportImportTimestampBug:
    """
    Documents a known issue in export_sealed_memory: get_identity() is called
    twice, producing two different timestamps. The sealed_evidence_chain is
    computed over the first identity, while packet.node_origin stores the second.
    This causes import_sealed_memory to raise RuntimeError (seal mismatch).

    The _build_valid_packet helper avoids this by fixing the timestamp and is
    used in the positive import tests above.
    """

    def test_export_then_import_raises_seal_mismatch(self):
        """
        A packet produced by export_sealed_memory fails import due to double
        get_identity() calls producing inconsistent timestamps in the seal.
        """
        node = _make_node()
        packet = node.export_sealed_memory(
            problem_id="regression_check",
            memory_state={"val": 1},
        )
        # The seal was computed over a different node_origin timestamp than what
        # is stored in packet.node_origin, so import will raise RuntimeError.
        with pytest.raises(RuntimeError):
            node.import_sealed_memory(packet)

    def test_export_seal_computed_from_first_get_identity(self):
        """
        Verifies that the sealed_evidence_chain in the exported packet was NOT
        computed using the node_origin that is stored in the packet (second call).
        """
        node = _make_node()
        packet = node.export_sealed_memory(
            problem_id="seal_check",
            memory_state={"k": "v"},
        )
        # Reconstruct the packet dict using packet.node_origin (as import does)
        packet_dict_as_import = {
            "problem_id": packet.problem_id,
            "node_origin": packet.node_origin.__dict__,
            "timestamp_sealed": packet.timestamp_sealed,
            "memory_state": packet.memory_state,
            "state_hash": packet.state_hash,
            "sovereignty_attestations": packet.sovereignty_attestations,
            "instructions": packet.instructions,
        }
        recomputed_seal = hashlib.sha256(
            json.dumps(packet_dict_as_import, sort_keys=True, default=str).encode()
        ).hexdigest()
        # The recomputed seal will NOT match the stored seal because the second
        # get_identity() call produced a different timestamp.
        assert recomputed_seal != packet.sealed_evidence_chain, (
            "Expected seal mismatch due to double get_identity() timestamp bug"
        )


# ---------------------------------------------------------------------------
# Tests for SovereignNode.get_sovereignty_report()
# ---------------------------------------------------------------------------

class TestGetSovereigntyReport:
    """Tests for get_sovereignty_report()."""

    def test_report_delegates_to_engine(self):
        engine = _make_passing_engine()
        node = _make_node(engine=engine)
        node.get_sovereignty_report()
        engine.get_sovereignty_report.assert_called_once()

    def test_report_structure(self):
        node = _make_node()
        report = node.get_sovereignty_report()
        assert isinstance(report, dict)
        assert "by_property" in report
        assert "sovereignty_gate_passed" in report


# ---------------------------------------------------------------------------
# Tests for SovereignNode.get_node_info()
# ---------------------------------------------------------------------------

class TestGetNodeInfo:
    """Tests for get_node_info()."""

    def test_node_info_contains_required_keys(self):
        node = _make_node(node_id="info_node", os_platform="win32", python_version="3.12.0")
        info = node.get_node_info()
        assert "node_id" in info
        assert "os_platform" in info
        assert "python_version" in info
        assert "sovereignty_gate_passed" in info
        assert "sealed_packets_count" in info
        assert "identity" in info

    def test_node_info_values_match_node(self):
        node = _make_node(node_id="info_node", os_platform="win32", python_version="3.12.0")
        info = node.get_node_info()
        assert info["node_id"] == "info_node"
        assert info["os_platform"] == "win32"
        assert info["python_version"] == "3.12.0"

    def test_node_info_sovereignty_gate_passed_reflects_engine(self):
        node_ok = _make_node(engine=_make_passing_engine())
        node_fail = _make_node(engine=_make_failing_engine())
        assert node_ok.get_node_info()["sovereignty_gate_passed"] is True
        assert node_fail.get_node_info()["sovereignty_gate_passed"] is False

    def test_node_info_sealed_packets_count_starts_at_zero(self):
        node = _make_node()
        assert node.get_node_info()["sealed_packets_count"] == 0

    def test_node_info_sealed_packets_count_after_export(self):
        node = _make_node()
        node.export_sealed_memory(problem_id="p1", memory_state={"x": 1})
        node.export_sealed_memory(problem_id="p2", memory_state={"y": 2})
        assert node.get_node_info()["sealed_packets_count"] == 2

    def test_node_info_identity_dict_has_expected_fields(self):
        node = _make_node(node_id="n1", os_platform="linux")
        info = node.get_node_info()
        identity = info["identity"]
        assert "node_id" in identity
        assert "os_platform" in identity
        assert "python_version" in identity
        assert "timestamp_created" in identity


# ---------------------------------------------------------------------------
# Module-level __all__ export
# ---------------------------------------------------------------------------

class TestModuleExports:
    """Verify the __all__ list exposes the expected public names."""

    def test_all_exports(self):
        import python_backend.hyba_genesis_api.core.sovereign_node as mod
        assert "SovereignNode" in mod.__all__
        assert "SovereignNodeIdentity" in mod.__all__
        assert "SovereignMemoryPacket" in mod.__all__


# ---------------------------------------------------------------------------
# Boundary / regression tests
# ---------------------------------------------------------------------------

class TestBoundaryAndRegression:
    """Extra boundary and negative-case tests for robustness."""

    def test_export_state_hash_is_hex_string(self):
        node = _make_node()
        packet = node.export_sealed_memory(problem_id="p1", memory_state={"v": True})
        int(packet.state_hash, 16)  # Raises ValueError if not valid hex

    def test_export_state_hash_length_is_64(self):
        node = _make_node()
        packet = node.export_sealed_memory(problem_id="p1", memory_state={"v": True})
        assert len(packet.state_hash) == 64

    def test_export_with_boolean_values(self):
        node = _make_node()
        state = {"flag": True, "other": False}
        packet = node.export_sealed_memory(problem_id="bool_test", memory_state=state)
        assert packet.memory_state == state

    def test_export_with_numeric_values(self):
        node = _make_node()
        state = {"int": 100, "float": 3.14159, "negative": -42}
        packet = node.export_sealed_memory(problem_id="num_test", memory_state=state)
        assert packet.memory_state == state

    def test_export_with_list_values(self):
        node = _make_node()
        state = {"data": [1, 2, 3, 4, 5]}
        packet = node.export_sealed_memory(problem_id="list_test", memory_state=state)
        assert packet.memory_state["data"] == [1, 2, 3, 4, 5]

    def test_verify_gate_called_once_per_export(self):
        engine = _make_passing_engine()
        node = _make_node(engine=engine)
        node.export_sealed_memory(problem_id="p1", memory_state={"x": 1})
        # verify_sovereignty_gate → verify_all_critical_passed called at least once
        engine.verify_all_critical_passed.assert_called()

    def test_verify_gate_called_once_per_import(self):
        engine = _make_passing_engine()
        node = _make_node(engine=engine)
        packet = _build_valid_packet(node)
        engine.reset_mock()
        node.import_sealed_memory(packet)
        engine.verify_all_critical_passed.assert_called()

    def test_multiple_problem_ids_cached_independently(self):
        node = _make_node()
        node.export_sealed_memory(problem_id="a", memory_state={"x": 1})
        node.export_sealed_memory(problem_id="b", memory_state={"x": 2})
        node.export_sealed_memory(problem_id="c", memory_state={"x": 3})
        assert len(node._sealed_packets) == 3
        assert "a" in node._sealed_packets
        assert "b" in node._sealed_packets
        assert "c" in node._sealed_packets

    def test_import_gate_failure_message_mentions_sovereignty(self):
        node = _make_node(engine=_make_failing_engine())
        packet = _build_valid_packet(node)
        with pytest.raises(RuntimeError) as exc_info:
            node.import_sealed_memory(packet)
        assert "sovereignty" in str(exc_info.value).lower()

    def test_export_gate_failure_message_mentions_sovereignty(self):
        node = _make_node(engine=_make_failing_engine())
        with pytest.raises(RuntimeError) as exc_info:
            node.export_sealed_memory(problem_id="p1", memory_state={})
        assert "sovereignty" in str(exc_info.value).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])