"""
SOVEREIGN NODE INTEGRATION LAYER

Provides substrate-independent recall and memory portability for PYTHIA.

A SovereignNode is a computational substrate that:
1. Passes all sovereignty attestations (precision, supply chain, air-gap, symmetry)
2. Can export sealed memory states reproducibly
3. Can import sealed memory on different hardware/OS
4. Verifies all invariants before recall

This enables "2 laptops = same intelligence" deployments: memory sealed on Laptop A
can be unsealed and run on Laptop B with full verifiability.

Design:
- SovereignNode wraps the attestation engine
- export_sealed_memory() serializes state with seals
- import_sealed_memory() reconstructs state on target node
- verify_sovereignty_gate() checks all critical conditions
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .sovereign_attestation import (
    AttestationResult,
    get_attestation_engine,
)
from .sovereign_memory import SovereignMemoryValidator

UTC = timezone.utc


@dataclass(frozen=True)
class SovereignNodeIdentity:
    """Unique identity of a sovereign computational node."""

    node_id: str  # Unique identifier (hostname, UUID, etc.)
    os_platform: str  # Platform identifier (darwin, linux, win32, etc.)
    python_version: str  # Python version
    timestamp_created: str  # When this node identity was established


@dataclass(frozen=True)
class SovereignMemoryPacket:
    """A sealed, portable memory state for substrate-independent recall."""

    problem_id: str
    node_origin: SovereignNodeIdentity
    timestamp_sealed: str
    memory_state: Dict[str, Any]  # Serialized memory state
    state_hash: str  # Hash of memory_state (for integrity)
    sovereignty_attestations: Dict[str, str]  # Evidence hashes from attestation
    sealed_evidence_chain: str  # Cryptographic seal over entire packet
    instructions: str  # How to reconstruct this memory


@dataclass
class SovereignNode:
    """A computational substrate that enforces sovereignty at runtime."""

    node_id: str  # Unique identifier
    os_platform: str  # Platform (darwin, linux, win32)
    python_version: str  # Python version
    attestation_engine: Any = field(default_factory=get_attestation_engine)
    memory_validator: SovereignMemoryValidator = field(
        default_factory=SovereignMemoryValidator
    )
    _sealed_packets: Dict[str, SovereignMemoryPacket] = field(default_factory=dict)

    def get_identity(self) -> SovereignNodeIdentity:
        """Return this node's identity."""
        return SovereignNodeIdentity(
            node_id=self.node_id,
            os_platform=self.os_platform,
            python_version=self.python_version,
            timestamp_created=datetime.now(UTC).isoformat(),
        )

    def verify_sovereignty_gate(self) -> bool:
        """Verify all critical sovereignty conditions are met.

        Returns:
            True if node passes all sovereignty checks, False otherwise.
        """
        # Check that all critical attestations passed
        if not self.attestation_engine.verify_all_critical_passed():
            return False

        # All checks passed
        return True

    def export_sealed_memory(
        self,
        *,
        problem_id: str,
        memory_state: Dict[str, Any],
    ) -> SovereignMemoryPacket:
        """Export memory state as a sealed, portable packet.

        The packet includes:
        - Memory state (serialized)
        - State integrity hash
        - Sovereignty attestations (evidence of compliance)
        - Sealed evidence chain
        - Instructions for reconstruction

        Args:
            problem_id: Identifier for this problem/computation
            memory_state: State dictionary to seal

        Returns:
            SovereignMemoryPacket that can be transported and imported elsewhere
        """
        # Verify node passes sovereignty gate
        if not self.verify_sovereignty_gate():
            raise RuntimeError("Node does not pass sovereignty gate; cannot export memory")

        # Capture identity ONCE to ensure seal verification works
        # (timestamp must match between packet_dict and SovereignMemoryPacket)
        node_identity = self.get_identity()
        timestamp_sealed = datetime.now(UTC).isoformat()

        # Serialize memory state
        state_json = json.dumps(memory_state, sort_keys=True, default=str)
        state_hash = hashlib.sha256(state_json.encode()).hexdigest()

        # Capture current attestation evidence (preserve all attestations per property)
        attestation_report = self.attestation_engine.get_sovereignty_report()
        attestation_evidence = {}
        for prop, atts in attestation_report.get("by_property", {}).items():
            att_list = atts if isinstance(atts, list) else [atts]
            attestation_evidence[prop] = [
                att["evidence_hash"] if isinstance(att, dict) else att.evidence_hash
                for att in att_list
            ]

        # Build packet
        packet_dict = {
            "problem_id": problem_id,
            "node_origin": node_identity.__dict__,
            "timestamp_sealed": timestamp_sealed,
            "memory_state": memory_state,
            "state_hash": state_hash,
            "sovereignty_attestations": attestation_evidence,
            "instructions": (
                f"To reconstruct: (1) Verify sovereignty gate on target node, "
                f"(2) Import this packet, (3) Verify state hash matches, "
                f"(4) Load memory_state into target node"
            ),
        }

        # Seal the entire packet
        packet_json = json.dumps(packet_dict, sort_keys=True, default=str)
        sealed_evidence_chain = hashlib.sha256(packet_json.encode()).hexdigest()

        packet_dict["sealed_evidence_chain"] = sealed_evidence_chain

        packet = SovereignMemoryPacket(
            problem_id=problem_id,
            node_origin=node_identity,
            timestamp_sealed=timestamp_sealed,
            memory_state=memory_state,
            state_hash=state_hash,
            sovereignty_attestations=attestation_evidence,
            sealed_evidence_chain=sealed_evidence_chain,
            instructions=packet_dict["instructions"],
        )

        # Cache for import verification
        self._sealed_packets[problem_id] = packet

        return packet

    def import_sealed_memory(
        self,
        packet: SovereignMemoryPacket,
    ) -> Dict[str, Any]:
        """Import a sealed memory packet from another node.

        Verifies:
        1. This node passes sovereignty gate
        2. Sealed evidence chain is valid
        3. State hash is consistent
        4. Memory state can be loaded

        Args:
            packet: SovereignMemoryPacket from export_sealed_memory

        Returns:
            The reconstructed memory_state dict

        Raises:
            RuntimeError if sovereignty checks fail or packet is invalid
        """
        # Verify node passes sovereignty gate
        if not self.verify_sovereignty_gate():
            raise RuntimeError("Target node does not pass sovereignty gate; cannot import memory")

        # Verify sealed evidence chain
        # Reconstruct the packet dict WITHOUT the sealed_evidence_chain field
        packet_dict_for_verification = {
            "problem_id": packet.problem_id,
            "node_origin": packet.node_origin.__dict__,
            "timestamp_sealed": packet.timestamp_sealed,
            "memory_state": packet.memory_state,
            "state_hash": packet.state_hash,
            "sovereignty_attestations": packet.sovereignty_attestations,
            "instructions": packet.instructions,
        }
        packet_json = json.dumps(
            packet_dict_for_verification, sort_keys=True, default=str
        )
        expected_seal = hashlib.sha256(packet_json.encode()).hexdigest()

        if expected_seal != packet.sealed_evidence_chain:
            raise RuntimeError(
                f"Sealed evidence chain mismatch: expected {expected_seal}, "
                f"got {packet.sealed_evidence_chain}"
            )

        # Verify state hash
        state_json = json.dumps(packet.memory_state, sort_keys=True, default=str)
        computed_state_hash = hashlib.sha256(state_json.encode()).hexdigest()

        if computed_state_hash != packet.state_hash:
            raise RuntimeError(
                f"State hash mismatch: expected {packet.state_hash}, "
                f"got {computed_state_hash}"
            )

        # Memory is valid and can be reconstructed
        return packet.memory_state

    def get_sovereignty_report(self) -> Dict[str, Any]:
        """Get current sovereignty compliance report."""
        return self.attestation_engine.get_sovereignty_report()

    def get_node_info(self) -> Dict[str, Any]:
        """Get information about this node."""
        return {
            "node_id": self.node_id,
            "os_platform": self.os_platform,
            "python_version": self.python_version,
            "sovereignty_gate_passed": self.verify_sovereignty_gate(),
            "sealed_packets_count": len(self._sealed_packets),
            "identity": self.get_identity().__dict__,
        }


__all__ = [
    "SovereignNode",
    "SovereignNodeIdentity",
    "SovereignMemoryPacket",
]
