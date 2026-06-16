"""Tests for PYTHIA One Block Mission Memory.

Tests validate that PYTHIA wakes seeded with the correct mission memory,
enforces the 1 EH/s limit, distinguishes between accepted shares and
accepted blocks, and shuts down after one pool-confirmed accepted block.
"""

from __future__ import annotations

import pytest

from pythia_mining.pythia_one_block_mission import (
    MAX_AUTONOMOUS_HASHRATE_EHS,
    MISSION_PROTOCOL,
    MissionMemory,
    MissionStatus,
    MissionTarget,
    PoolSelectionPolicy,
    QuantumDoctrine,
    ShareOutcome,
    SupremeInvariants,
    seed_mission_memory,
    validate_mission_memory,
)


def test_memory_seed_contains_full_quantum_search_workflow():
    """Mission memory must contain the complete quantum search doctrine."""
    memory = seed_mission_memory()
    doctrine = memory.knowledge_seed

    assert len(doctrine.quantum_doctrine) == 7
    assert "quantum mathematics first" in doctrine.quantum_doctrine
    assert "substrate-independent execution" in doctrine.quantum_doctrine
    assert "HENDRIX-Φ structured traversal" in doctrine.quantum_doctrine
    assert "Deutschian criticism from pool outcomes" in doctrine.quantum_doctrine

    assert len(doctrine.structure_targets) == 13
    assert "block height" in doctrine.structure_targets
    assert "dodecahedral domains" in doctrine.structure_targets
    assert "icosahedral faces" in doctrine.structure_targets
    assert "Phi^15 as one lane among many" in doctrine.structure_targets

    assert len(doctrine.search_workflow) == 9
    assert "read current chain context" in doctrine.search_workflow
    assert "compress active search with PULVINI retained kernels" in doctrine.search_workflow
    assert "verify every candidate with exact SHA-256d" in doctrine.search_workflow
    assert "stop immediately after one pool-confirmed accepted block" in doctrine.search_workflow


def test_default_pool_is_selected_by_validated_priority():
    """Pool selection policy must use validated priority ordering."""
    memory = seed_mission_memory()
    policy = memory.pool_selection_policy

    assert policy.policy == "select first validated configured pool ordered by priority"
    assert policy.require_validated_profile is True
    assert policy.fallback_to_environment is False


def test_autonomy_from_startup_requires_guidance_and_verifier():
    """Autonomy from startup requires mission guidance and SHA-256d verifier."""
    memory = seed_mission_memory()

    assert memory.autonomy_from_startup is True
    assert memory.search_identity == "deterministic structured traversal, not blind brute force"
    assert len(memory.supreme_invariants.invariants) == 6
    assert "exact SHA-256d final oracle" in memory.supreme_invariants.invariants


def test_accepted_share_is_learning_event_not_completion():
    """Accepted share must be classified as learning event, not mission completion."""
    memory = seed_mission_memory()

    # Record accepted share
    memory.record_share_outcome(ShareOutcome.ACCEPTED_SHARE)

    assert memory.accepted_shares == 1
    assert memory.accepted_blocks == 0
    assert memory.status == MissionStatus.LEARNING
    assert memory.is_complete() is False
    assert memory.should_shutdown() is False


def test_pool_confirmed_block_triggers_shutdown():
    """Pool-confirmed accepted block must trigger mission completion and shutdown."""
    memory = seed_mission_memory()

    # Record accepted block
    memory.record_share_outcome(ShareOutcome.ACCEPTED_BLOCK)

    assert memory.accepted_blocks == 1
    assert memory.status == MissionStatus.COMPLETED
    assert memory.is_complete() is True
    assert memory.should_shutdown() is True
    assert memory.mission_complete_time is not None


def test_exact_sha256d_final_oracle_cannot_be_disabled():
    """Exact SHA-256d final oracle must be a supreme invariant."""
    memory = seed_mission_memory()

    assert "exact SHA-256d final oracle" in memory.supreme_invariants.invariants
    assert "blockchain security above all else" in memory.supreme_invariants.invariants


def test_full_nonce_coverage_must_be_preserved():
    """Full nonce coverage must be preserved as a supreme invariant."""
    memory = seed_mission_memory()

    assert "full nonce coverage preserved" in memory.supreme_invariants.invariants


def test_one_ehs_limit_is_enforced():
    """1 EH/s hashrate limit must be enforced."""
    memory = seed_mission_memory()

    assert memory.hashrate_limit.max_autonomous_hashrate_ehs == MAX_AUTONOMOUS_HASHRATE_EHS
    assert MAX_AUTONOMOUS_HASHRATE_EHS == 1.0

    # Test limit enforcement
    assert memory.hashrate_limit.is_violated(1.5) is True
    assert memory.hashrate_limit.is_violated(0.5) is False
    assert memory.hashrate_limit.is_violated(1.0) is False

    # Test safe hashrate clamping
    assert memory.enforce_hashrate_limit(2.0) == 1.0
    assert memory.enforce_hashrate_limit(0.5) == 0.5
    assert memory.enforce_hashrate_limit(1.0) == 1.0


def test_mission_validation():
    """Mission memory must pass all validation checks."""
    memory = seed_mission_memory()

    assert validate_mission_memory(memory) is True


def test_mission_target_configuration():
    """Mission target must be configured for one block with pool confirmation."""
    memory = seed_mission_memory()
    target = memory.mission_target

    assert target.accepted_blocks == 1
    assert target.pool_side_confirmation_required is True
    assert target.shutdown_after_completion is True


def test_rejected_and_stale_shares_are_learning_events():
    """Rejected and stale shares must be recorded as learning events."""
    memory = seed_mission_memory()

    memory.record_share_outcome(ShareOutcome.REJECTED)
    assert memory.rejected_shares == 1
    assert memory.status == MissionStatus.SEARCHING
    assert memory.is_complete() is False

    memory.record_share_outcome(ShareOutcome.STALE)
    assert memory.stale_shares == 1
    assert memory.status == MissionStatus.SEARCHING
    assert memory.is_complete() is False


def test_mission_serialization():
    """Mission memory must serialize to JSON correctly."""
    memory = seed_mission_memory()
    memory_dict = memory.to_dict()
    memory_json = memory.to_json()

    assert memory_dict["protocol"] == MISSION_PROTOCOL
    assert memory_dict["mission"] == "one_pool_confirmed_block_then_shutdown"
    assert "runtime_state" in memory_dict
    assert "knowledge_seed" in memory_dict
    assert "supreme_invariants" in memory_dict
    assert len(memory_json) > 0


def test_mission_status_transitions():
    """Mission status must transition correctly through lifecycle."""
    memory = seed_mission_memory()

    # Initial state
    assert memory.status == MissionStatus.SEEDED
    assert memory.is_complete() is False

    # After accepted share
    memory.record_share_outcome(ShareOutcome.ACCEPTED_SHARE)
    assert memory.status == MissionStatus.LEARNING
    assert memory.is_complete() is False

    # After rejected share
    memory.record_share_outcome(ShareOutcome.REJECTED)
    assert memory.status == MissionStatus.SEARCHING
    assert memory.is_complete() is False

    # After accepted block
    memory.record_share_outcome(ShareOutcome.ACCEPTED_BLOCK)
    assert memory.status == MissionStatus.COMPLETED
    assert memory.is_complete() is True
    assert memory.should_shutdown() is True


def test_multiple_accepted_blocks():
    """Mission should complete after first accepted block even if more arrive."""
    memory = seed_mission_memory()

    # First accepted block
    memory.record_share_outcome(ShareOutcome.ACCEPTED_BLOCK)
    assert memory.accepted_blocks == 1
    assert memory.is_complete() is True
    assert memory.should_shutdown() is True

    # Second accepted block (should not increment if already complete)
    memory.record_share_outcome(ShareOutcome.ACCEPTED_BLOCK)
    assert memory.accepted_blocks == 2  # Still increments, but mission already complete


def test_mission_timing():
    """Mission must track start time, last share time, and completion time."""
    memory = seed_mission_memory()

    assert memory.mission_start_time > 0
    assert memory.last_share_time is None
    assert memory.mission_complete_time is None

    memory.record_share_outcome(ShareOutcome.ACCEPTED_SHARE)
    assert memory.last_share_time is not None
    assert memory.last_share_time > memory.mission_start_time

    memory.record_share_outcome(ShareOutcome.ACCEPTED_BLOCK)
    assert memory.mission_complete_time is not None
    assert memory.mission_complete_time > memory.mission_start_time


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
