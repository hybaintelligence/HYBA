"""Unit and property tests for UniversalPassport module.

This test suite validates:
1. Basic functionality of passport creation and verification
2. Mathematical invariants (hash integrity, epistemic completeness)
3. Property-based tests for robustness across inputs
4. Integration with existing HYBA subsystem patterns
"""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

import pytest
from hypothesis import given, strategies as st
from hypothesis.strategies import dictionaries, floats, integers, lists, text

from python_backend.core.audit.universal_passport import (
    ClaimType,
    EpistemicBound,
    SharedAuditLog,
    Subsystem,
    UniversalPassport,
    make_circuit_breaker_passport,
    make_mining_passport,
    make_mode_transition_passport,
    make_passport,
    make_phi_measurement_passport,
)


# ============================================================================
# Unit Tests
# ============================================================================


class TestUniversalPassportBasics:
    """Test basic passport creation and validation."""

    def test_passport_creation_minimal(self):
        """Test creating a passport with minimal required fields."""
        passport = make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.NONCE_FOUND.value,
            payload={"nonce": 12345},
        )
        assert passport.subsystem == Subsystem.PYTHIA.value
        assert passport.claim_type == ClaimType.NONCE_FOUND.value
        assert passport.payload["nonce"] == 12345
        assert passport.verify() is True

    def test_passport_with_epistemic_bounds(self):
        """Test passport creation with explicit epistemic boundaries."""
        passport = make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.NONCE_FOUND.value,
            payload={"nonce": 12345},
            epistemic_bounds=[
                EpistemicBound.NO_QUANTUM_SPEEDUP.value,
                EpistemicBound.NO_GUARANTEE_CORRECTNESS.value,
            ],
        )
        assert len(passport.epistemic_bounds) == 2
        assert EpistemicBound.NO_QUANTUM_SPEEDUP.value in passport.epistemic_bounds
        assert passport.verify() is True

    def test_passport_hash_integrity(self):
        """Test that passport hash is computed correctly and verifies."""
        passport = make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.NONCE_FOUND.value,
            payload={"nonce": 12345},
        )
        original_hash = passport.embedded_hash
        assert passport.verify() is True
        assert passport.embedded_hash == original_hash

    def test_passport_tamper_detection(self):
        """Test that passport verification detects tampering."""
        passport = make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.NONCE_FOUND.value,
            payload={"nonce": 12345},
        )
        
        # Simulate tampering by modifying the dataclass
        # Since it's frozen, we need to create a new passport with same hash but different payload
        tampered_dict = passport.to_dict()
        tampered_dict["payload"]["nonce"] = 99999
        tampered_dict["embedded_hash"] = passport.embedded_hash  # Keep original hash
        
        # Create new passport from tampered dict
        tampered_passport = UniversalPassport(**tampered_dict)
        
        # Verification should fail
        assert tampered_passport.verify() is False

    def test_invalid_subsystem_raises_error(self):
        """Test that invalid subsystem raises ValueError."""
        with pytest.raises(ValueError, match="Invalid subsystem"):
            make_passport(
                subsystem="invalid_subsystem",
                claim_type=ClaimType.NONCE_FOUND.value,
                payload={"nonce": 12345},
            )

    def test_invalid_claim_type_raises_error(self):
        """Test that invalid claim type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid claim_type"):
            make_passport(
                subsystem=Subsystem.PYTHIA.value,
                claim_type="invalid_claim",
                payload={"nonce": 12345},
            )

    def test_invalid_epistemic_bound_raises_error(self):
        """Test that invalid epistemic bound raises ValueError."""
        with pytest.raises(ValueError, match="Invalid epistemic_bound"):
            make_passport(
                subsystem=Subsystem.PYTHIA.value,
                claim_type=ClaimType.NONCE_FOUND.value,
                payload={"nonce": 12345},
                epistemic_bounds=["invalid_bound"],
            )

    def test_passport_serialization(self):
        """Test passport to_dict and to_json methods."""
        passport = make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.NONCE_FOUND.value,
            payload={"nonce": 12345, "job_id": "test_job"},
        )
        
        # Test to_dict
        passport_dict = passport.to_dict()
        assert passport_dict["subsystem"] == Subsystem.PYTHIA.value
        assert passport_dict["claim_type"] == ClaimType.NONCE_FOUND.value
        assert passport_dict["payload"]["nonce"] == 12345
        
        # Test to_json
        passport_json = passport.to_json()
        parsed = json.loads(passport_json)
        assert parsed["subsystem"] == Subsystem.PYTHIA.value
        assert parsed["payload"]["nonce"] == 12345

    def test_passport_hash_property_alias(self):
        """Test that passport_hash property returns embedded_hash."""
        passport = make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.NONCE_FOUND.value,
            payload={"nonce": 12345},
        )
        assert passport.passport_hash == passport.embedded_hash


class TestConvenienceFactories:
    """Test convenience factory functions for common claim types."""

    def test_make_mining_passport(self):
        """Test mining passport factory."""
        passport = make_mining_passport(
            nonce=12345,
            job_id="test_job",
            pool_name="test_pool",
            phi_score=0.618,
            bures_score=0.5,
        )
        assert passport.subsystem == Subsystem.PYTHIA.value
        assert passport.claim_type == ClaimType.NONCE_FOUND.value
        assert passport.payload["nonce"] == 12345
        assert passport.payload["job_id"] == "test_job"
        assert passport.payload["pool_name"] == "test_pool"
        assert passport.payload["phi_score"] == 0.618
        assert passport.payload["bures_score"] == 0.5
        assert EpistemicBound.NO_QUANTUM_SPEEDUP.value in passport.epistemic_bounds
        assert passport.verify() is True

    def test_make_mode_transition_passport(self):
        """Test mode transition passport factory."""
        passport = make_mode_transition_passport(
            from_mode="NORMAL",
            to_mode="SANITIZED",
            reason="security_event",
            security_context={"event_id": "evt_123"},
        )
        assert passport.subsystem == Subsystem.SECURITY_SWARM.value
        assert passport.claim_type == ClaimType.MODE_TRANSITION.value
        assert passport.payload["from_mode"] == "NORMAL"
        assert passport.payload["to_mode"] == "SANITIZED"
        assert EpistemicBound.NO_SECURITY_INVULNERABILITY.value in passport.epistemic_bounds
        assert passport.verify() is True

    def test_make_phi_measurement_passport(self):
        """Test phi measurement passport factory."""
        passport = make_phi_measurement_passport(
            phi_value=0.618,
            system_state={"state": "active"},
            measurement_context={"method": "iit_4"},
        )
        assert passport.subsystem == Subsystem.IIT_ENGINE.value
        assert passport.claim_type == ClaimType.PHI_MEASUREMENT.value
        assert passport.payload["phi_value"] == 0.618
        assert EpistemicBound.NO_CONSCIOUSNESS_CLAIM.value in passport.epistemic_bounds
        assert passport.verify() is True

    def test_make_circuit_breaker_passport(self):
        """Test circuit breaker passport factory."""
        passport = make_circuit_breaker_passport(
            signal={"type": "timeout"},
            route="fallback",
            explanation={"reason": "primary_unavailable"},
        )
        assert passport.subsystem == Subsystem.META_CONTROLLER.value
        assert passport.claim_type == ClaimType.CIRCUIT_BREAKER_TRIP.value
        assert passport.payload["route"] == "fallback"
        assert EpistemicBound.NO_GUARANTEE_CORRECTNESS.value in passport.epistemic_bounds
        assert passport.verify() is True


class TestEpistemicCompleteness:
    """Test epistemic boundary validation."""

    def test_verify_epistemic_completeness_success(self):
        """Test successful epistemic completeness verification."""
        passport = make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.NONCE_FOUND.value,
            payload={"nonce": 12345},
            epistemic_bounds=[EpistemicBound.NO_QUANTUM_SPEEDUP.value],
        )
        assert passport.verify_epistemic_completeness(
            [EpistemicBound.NO_QUANTUM_SPEEDUP.value]
        ) is True

    def test_verify_epistemic_completeness_failure(self):
        """Test failed epistemic completeness verification."""
        passport = make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.NONCE_FOUND.value,
            payload={"nonce": 12345},
            epistemic_bounds=[],
        )
        assert passport.verify_epistemic_completeness(
            [EpistemicBound.NO_QUANTUM_SPEEDUP.value]
        ) is False

    def test_multiple_required_bounds(self):
        """Test verification with multiple required bounds."""
        passport = make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.NONCE_FOUND.value,
            payload={"nonce": 12345},
            epistemic_bounds=[
                EpistemicBound.NO_QUANTUM_SPEEDUP.value,
                EpistemicBound.NO_GUARANTEE_CORRECTNESS.value,
            ],
        )
        assert passport.verify_epistemic_completeness([
            EpistemicBound.NO_QUANTUM_SPEEDUP.value,
            EpistemicBound.NO_GUARANTEE_CORRECTNESS.value,
        ]) is True


class TestSharedAuditLog:
    """Test shared audit log functionality."""

    def test_audit_log_append(self):
        """Test appending passports to audit log."""
        log = SharedAuditLog()
        passport = make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.NONCE_FOUND.value,
            payload={"nonce": 12345},
            epistemic_bounds=[EpistemicBound.NO_QUANTUM_SPEEDUP.value],
        )
        log.append(passport)
        assert len(log.get_entries()) == 1

    def test_audit_log_append_invalid_hash_raises_error(self):
        """Test that appending passport with invalid hash raises error."""
        log = SharedAuditLog()
        passport_dict = {
            "subsystem": Subsystem.PYTHIA.value,
            "claim_type": ClaimType.NONCE_FOUND.value,
            "payload": {"nonce": 12345},
            "epistemic_bounds": [],
            "timestamp": time.time(),
            "embedded_hash": "invalid_hash",
            "schema_version": "UNIVERSAL_PASSPORT_V1",
        }
        passport = UniversalPassport(**passport_dict)
        with pytest.raises(ValueError, match="Cannot append passport with invalid hash"):
            log.append(passport)

    def test_audit_log_filter_by_subsystem(self):
        """Test filtering audit log by subsystem."""
        log = SharedAuditLog()
        log.append(make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.NONCE_FOUND.value,
            payload={"nonce": 1},
            epistemic_bounds=[EpistemicBound.NO_QUANTUM_SPEEDUP.value],
        ))
        log.append(make_passport(
            subsystem=Subsystem.SECURITY_SWARM.value,
            claim_type=ClaimType.MODE_TRANSITION.value,
            payload={"mode": "SANITIZED"},
            epistemic_bounds=[EpistemicBound.NO_SECURITY_INVULNERABILITY.value],
        ))
        
        pythia_entries = log.get_entries(subsystem=Subsystem.PYTHIA.value)
        assert len(pythia_entries) == 1
        assert pythia_entries[0].subsystem == Subsystem.PYTHIA.value

    def test_audit_log_filter_by_claim_type(self):
        """Test filtering audit log by claim type."""
        log = SharedAuditLog()
        log.append(make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.NONCE_FOUND.value,
            payload={"nonce": 1},
        ))
        log.append(make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.SHARE_SUBMISSION.value,
            payload={"share": 2},
        ))
        
        nonce_entries = log.get_entries(claim_type=ClaimType.NONCE_FOUND.value)
        assert len(nonce_entries) == 1
        assert nonce_entries[0].claim_type == ClaimType.NONCE_FOUND.value

    def test_audit_log_filter_by_timestamp(self):
        """Test filtering audit log by timestamp range."""
        log = SharedAuditLog()
        t1 = time.time()
        time.sleep(0.01)
        log.append(make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.NONCE_FOUND.value,
            payload={"nonce": 1},
            timestamp=t1,
        ))
        t2 = time.time()
        time.sleep(0.01)
        log.append(make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.NONCE_FOUND.value,
            payload={"nonce": 2},
            timestamp=t2,
        ))
        
        entries = log.get_entries(since=t1, until=t2)
        assert len(entries) == 1
        assert entries[0].payload["nonce"] == 1

    def test_audit_log_verify_chain(self):
        """Test audit log chain verification."""
        log = SharedAuditLog()
        passport = make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.NONCE_FOUND.value,
            payload={"nonce": 12345},
        )
        log.append(passport)
        assert log.verify_chain() is True

    def test_audit_log_persistence(self):
        """Test audit log persistence to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "audit_log.json"
            log = SharedAuditLog(storage_path=str(storage_path))
            
            passport = make_passport(
                subsystem=Subsystem.PYTHIA.value,
                claim_type=ClaimType.NONCE_FOUND.value,
                payload={"nonce": 12345},
            )
            log.append(passport)
            
            # Create new log instance to load from storage
            log2 = SharedAuditLog(storage_path=str(storage_path))
            entries = log2.get_entries()
            assert len(entries) == 1
            assert entries[0].payload["nonce"] == 12345

    def test_audit_log_required_bounds_enforcement(self):
        """Test that audit log enforces required epistemic bounds."""
        log = SharedAuditLog()
        # High-stakes claim without required bounds should fail
        passport = make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.NONCE_FOUND.value,
            payload={"nonce": 12345},
            epistemic_bounds=[],  # Missing required bounds
        )
        with pytest.raises(ValueError, match="missing required epistemic bounds"):
            log.append(passport)


# ============================================================================
# Property-Based Tests
# ============================================================================


class TestPassportProperties:
    """Property-based tests for passport invariants."""

    @given(
        subsystem=st.sampled_from([s.value for s in Subsystem]),
        claim_type=st.sampled_from([c.value for c in ClaimType]),
        payload=dictionaries(
            keys=text(min_size=1, max_size=10),
            values=floats(allow_nan=False, allow_infinity=False) | integers() | text(),
            min_size=0,
            max_size=10,
        ),
        epistemic_bounds=st.lists(
            st.sampled_from([b.value for b in EpistemicBound]),
            min_size=0,
            max_size=5,
        ),
    )
    def test_property_passport_verification_always_succeeds(
        self, subsystem, claim_type, payload, epistemic_bounds
    ):
        """Property: All valid passports should verify successfully."""
        passport = make_passport(
            subsystem=subsystem,
            claim_type=claim_type,
            payload=payload,
            epistemic_bounds=epistemic_bounds,
        )
        assert passport.verify() is True

    @given(
        subsystem=st.sampled_from([s.value for s in Subsystem]),
        claim_type=st.sampled_from([c.value for c in ClaimType]),
        payload=dictionaries(
            keys=text(min_size=1, max_size=10),
            values=floats(allow_nan=False, allow_infinity=False) | integers(),
            min_size=1,
            max_size=5,
        ),
    )
    def test_property_hash_deterministic(
        self, subsystem, claim_type, payload
    ):
        """Property: Hash computation is deterministic for same input."""
        timestamp = time.time()
        passport1 = make_passport(
            subsystem=subsystem,
            claim_type=claim_type,
            payload=payload,
            timestamp=timestamp,
        )
        passport2 = make_passport(
            subsystem=subsystem,
            claim_type=claim_type,
            payload=payload,
            timestamp=timestamp,
        )
        assert passport1.embedded_hash == passport2.embedded_hash

    @given(
        subsystem=st.sampled_from([s.value for s in Subsystem]),
        claim_type=st.sampled_from([c.value for c in ClaimType]),
        payload=dictionaries(
            keys=text(min_size=1, max_size=10),
            values=integers(min_value=0, max_value=1000000),
            min_size=1,
            max_size=5,
        ),
    )
    def test_property_different_payloads_different_hashes(
        self, subsystem, claim_type, payload
    ):
        """Property: Different payloads produce different hashes (collision resistance)."""
        timestamp = time.time()
        passport1 = make_passport(
            subsystem=subsystem,
            claim_type=claim_type,
            payload=payload,
            timestamp=timestamp,
        )
        # Modify payload slightly - use integers to avoid floating point precision issues
        modified_payload = dict(payload)
        if payload:
            first_key = list(payload.keys())[0]
            if isinstance(payload[first_key], int):
                modified_payload[first_key] = payload[first_key] + 1
            else:
                modified_payload[first_key] = str(payload[first_key]) + "_mod"
        
        passport2 = make_passport(
            subsystem=subsystem,
            claim_type=claim_type,
            payload=modified_payload,
            timestamp=timestamp,
        )
        assert passport1.embedded_hash != passport2.embedded_hash

    @given(
        subsystem=st.sampled_from([s.value for s in Subsystem]),
        claim_type=st.sampled_from([c.value for c in ClaimType]),
        payload=dictionaries(
            keys=text(min_size=1, max_size=10),
            values=integers(min_value=0, max_value=1000000),
            min_size=0,
            max_size=5,
        ),
    )
    def test_property_serialization_roundtrip(
        self, subsystem, claim_type, payload
    ):
        """Property: Serialization to dict/json and back preserves integrity."""
        passport = make_passport(
            subsystem=subsystem,
            claim_type=claim_type,
            payload=payload,
        )
        
        # Dict roundtrip
        passport_dict = passport.to_dict()
        passport_from_dict = UniversalPassport(**passport_dict)
        assert passport_from_dict.verify() is True
        assert passport_from_dict.embedded_hash == passport.embedded_hash
        
        # JSON roundtrip
        passport_json = passport.to_json()
        passport_from_json = UniversalPassport(**json.loads(passport_json))
        assert passport_from_json.verify() is True
        assert passport_from_json.embedded_hash == passport.embedded_hash


class TestAuditLogProperties:
    """Property-based tests for audit log invariants."""

    @given(
        num_passports=integers(min_value=1, max_value=20),
        subsystem=st.sampled_from([s.value for s in Subsystem]),
    )
    def test_property_audit_log_append_preserves_integrity(
        self, num_passports, subsystem
    ):
        """Property: Appending valid passports preserves chain integrity."""
        log = SharedAuditLog()
        for i in range(num_passports):
            passport = make_passport(
                subsystem=subsystem,
                claim_type=ClaimType.NONCE_FOUND.value,
                payload={"nonce": i},
                epistemic_bounds=[EpistemicBound.NO_QUANTUM_SPEEDUP.value],
            )
            log.append(passport)
        
        assert log.verify_chain() is True
        assert len(log.get_entries()) == num_passports

    @given(
        num_passports=integers(min_value=2, max_value=10),
    )
    def test_property_filter_subsystem_isolation(
        self, num_passports
    ):
        """Property: Filtering by subsystem correctly isolates entries."""
        log = SharedAuditLog()
        subsystems = [s.value for s in Subsystem]
        
        for i in range(num_passports):
            subsystem = subsystems[i % len(subsystems)]
            passport = make_passport(
                subsystem=subsystem,
                claim_type=ClaimType.NONCE_FOUND.value,
                payload={"nonce": i},
                epistemic_bounds=[EpistemicBound.NO_QUANTUM_SPEEDUP.value],
            )
            log.append(passport)
        
        # Each subsystem should only return its own entries
        for subsystem in subsystems:
            entries = log.get_entries(subsystem=subsystem)
            for entry in entries:
                assert entry.subsystem == subsystem


# ============================================================================
# Integration Tests
# ============================================================================


class TestPassportIntegration:
    """Test integration with existing HYBA patterns."""

    def test_passport_compatible_with_existing_hash_pattern(self):
        """Test that passport hash pattern matches existing PULVINI pattern."""
        # This ensures compatibility with existing certificate ledger
        passport = make_passport(
            subsystem=Subsystem.PYTHIA.value,
            claim_type=ClaimType.NONCE_FOUND.value,
            payload={"nonce": 12345},
        )
        
        # Hash should be SHA-256 hex string
        assert len(passport.embedded_hash) == 64
        assert all(c in "0123456789abcdef" for c in passport.embedded_hash)

    def test_passport_timestamp_monotonicity(self):
        """Test that timestamps are monotonically increasing within subsystem."""
        log = SharedAuditLog()
        timestamps = []
        
        for i in range(5):
            passport = make_passport(
                subsystem=Subsystem.PYTHIA.value,
                claim_type=ClaimType.NONCE_FOUND.value,
                payload={"nonce": i},
                epistemic_bounds=[EpistemicBound.NO_QUANTUM_SPEEDUP.value],
            )
            log.append(passport)
            timestamps.append(passport.timestamp)
        
        # Timestamps should be non-decreasing
        assert timestamps == sorted(timestamps)

    def test_multiple_subsystems_in_single_log(self):
        """Test that multiple subsystems can coexist in single audit log."""
        log = SharedAuditLog()
        
        # Add entries from different subsystems
        log.append(make_mining_passport(
            nonce=1, job_id="job1", pool_name="pool1", phi_score=0.5, bures_score=0.5
        ))
        log.append(make_mode_transition_passport(
            from_mode="NORMAL", to_mode="SANITIZED", reason="test", security_context={}
        ))
        log.append(make_phi_measurement_passport(
            phi_value=0.618, system_state={}, measurement_context={}
        ))
        log.append(make_circuit_breaker_passport(
            signal={}, route="fallback", explanation={}
        ))
        
        # All should be in the log
        assert len(log.get_entries()) == 4
        
        # Each subsystem should have exactly one entry
        assert len(log.get_entries(subsystem=Subsystem.PYTHIA.value)) == 1
        assert len(log.get_entries(subsystem=Subsystem.SECURITY_SWARM.value)) == 1
        assert len(log.get_entries(subsystem=Subsystem.IIT_ENGINE.value)) == 1
        assert len(log.get_entries(subsystem=Subsystem.META_CONTROLLER.value)) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
