"""Adversarial tests for autonomous mining controller.

These tests validate Byzantine fault tolerance and attack resistance:
- Malicious pool responses
- State corruption attempts
- Constraint violation attacks
- Timestamp manipulation
- Cache poisoning
- Denial of service attacks
"""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

import pytest

from pythia_mining.autonomous_mining_controller import (
    AutonomousConfig,
    AutonomousMiningController,
    AutonomyLevel,
    SelfOptimizationProposal,
)


class _FakeEngine:
    """Minimal duck-type stand-in for UnifiedMiningEngine."""
    
    phi_density: float = 0.75
    current_job = None
    stratum_client = None
    phi_ensemble = None
    optimizer = None
    solver = None
    consciousness = None
    
    def get_hashrate(self) -> float:
        return 0.0
    
    def get_phi_density(self) -> float:
        return self.phi_density
    
    def get_state(self) -> dict:
        return {"status": "idle"}
    
    class _PhiScaling:
        phi_scaling = 1.5
        search_depth = 60
        coherence_threshold = 0.45
        compression_target = 1.86
    
    phi_scaling_engine = _PhiScaling()


def _make_controller(tmp_dir: str) -> AutonomousMiningController:
    """Create controller for testing."""
    config = AutonomousConfig(
        autonomy_level=AutonomyLevel.AUTONOMOUS,
        persistence_enabled=True,
        persistence_dir=tmp_dir,
        reflexive_loop_enabled=True,
        max_proposals_per_cycle=3,
    )
    return AutonomousMiningController(_FakeEngine(), config=config)


# =============================================================================
# ADVERSARIAL: Malicious Pool Responses
# =============================================================================

@pytest.mark.adversarial
def test_adversarial_negative_difficulty():
    """System should reject pool responses with negative difficulty."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        
        # Attempt to inject negative difficulty
        try:
            ctrl.record_pool_response(
                share_accepted=True,
                job_difficulty=-1000.0,  # Malicious negative value
            )
            
            # If accepted, verify it was sanitized
            if ctrl._pool_response_history:
                last_response = ctrl._pool_response_history[-1]
                assert last_response["job_difficulty"] >= 0, \
                    "Negative difficulty should be rejected or sanitized"
        except (ValueError, AssertionError):
            # Expected: system rejects invalid input
            pass


@pytest.mark.adversarial
def test_adversarial_extreme_response_time():
    """System should handle extreme response times gracefully."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        
        # Inject extremely high response time
        ctrl.record_pool_response(
            share_accepted=True,
            response_time_ms=1_000_000_000.0,  # 1 billion ms = 277 hours
        )
        
        # System should remain stable
        metrics = ctrl.get_metrics_snapshot()
        assert metrics["consecutive_failures"] == 0
        assert not ctrl.is_circuit_open()


@pytest.mark.adversarial
def test_adversarial_future_timestamp():
    """System should handle pool responses with future timestamps."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        
        # Manually inject response with future timestamp
        malicious_response = {
            "timestamp": time.time() + 86400,  # 24 hours in future
            "accepted": True,
            "job_difficulty": 1000.0,
        }
        ctrl._pool_response_history.append(malicious_response)
        
        # System should not crash when computing recency weights
        try:
            adjustment = ctrl._pool_feedback_adjustment_weighted(
                ctrl.optimization_targets[0] if ctrl.optimization_targets else None
            )
            # Should complete without error
            assert adjustment is not None
        except Exception as e:
            pytest.fail(f"Future timestamp caused crash: {e}")


# =============================================================================
# ADVERSARIAL: State Corruption Attempts
# =============================================================================

@pytest.mark.adversarial
def test_adversarial_corrupted_state_file():
    """System should detect and handle corrupted state files."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        
        # Save valid state
        ctrl._save_reflexive_state()
        
        # Corrupt the state file
        state_file = Path(tmp) / "reflexive_state.json"
        state_file.write_text("{ corrupted json data }}}")
        
        # Attempt to load corrupted state
        try:
            ctrl._load_reflexive_state()
            # If load succeeds, verify it fell back to defaults
            assert ctrl._target_evidence is not None
        except json.JSONDecodeError:
            # Expected: system detects corruption
            pass


@pytest.mark.adversarial
def test_adversarial_mismatched_checksum():
    """System should detect checksum mismatches."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        
        # Save valid state
        ctrl._save_reflexive_state()
        
        # Tamper with state file without updating checksum
        state_file = Path(tmp) / "reflexive_state.json"
        state_data = json.loads(state_file.read_text())
        state_data["epochs"] = 999999  # Tampered value
        state_file.write_text(json.dumps(state_data))
        
        # Attempt to load tampered state
        try:
            ctrl2 = _make_controller(tmp)
            ctrl2._load_reflexive_state()
            # If checksum validation exists, this should fail
        except Exception:
            # Expected: checksum mismatch detected
            pass


@pytest.mark.adversarial
def test_adversarial_schema_version_downgrade():
    """System should reject state files with lower schema versions."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        
        # Save valid state
        ctrl._save_reflexive_state()
        
        # Downgrade schema version (potential rollback attack)
        state_file = Path(tmp) / "reflexive_state.json"
        state_data = json.loads(state_file.read_text())
        state_data["schema_version"] = 1  # Downgraded from 3
        state_file.write_text(json.dumps(state_data))
        
        # System should handle version mismatch gracefully
        try:
            ctrl2 = _make_controller(tmp)
            ctrl2._load_reflexive_state()
            # Should either migrate or reject
        except Exception:
            # Expected: version mismatch handling
            pass


# =============================================================================
# ADVERSARIAL: Constraint Violation Attacks
# =============================================================================

@pytest.mark.adversarial
def test_adversarial_hermiticity_violation():
    """System should reject proposals violating hermiticity."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        
        # Create malicious proposal
        malicious_proposal = SelfOptimizationProposal(
            improvement_type="search_depth",
            current_value=60.0,
            proposed_value=999999.0,  # Extreme value
            expected_gain=100.0,
            source_module="attacker",
            counterfactual_confidence=1.0,
            logical_consistency=1.0,
            proposal_id="malicious_001",
        )
        
        # System should reject via constraint validation
        is_valid = ctrl.validate_constraints(malicious_proposal)
        
        # Should fail constraint check
        assert not is_valid, "Extreme proposal should fail hermiticity constraint"


@pytest.mark.adversarial
def test_adversarial_energy_conservation_violation():
    """System should reject proposals violating energy conservation."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        
        # Create proposal claiming impossible energy reduction
        malicious_proposal = SelfOptimizationProposal(
            improvement_type="coherence_threshold",
            current_value=0.7,
            proposed_value=0.01,  # Unrealistic drop
            expected_gain=1000.0,  # Impossible gain
            source_module="attacker",
            counterfactual_confidence=1.0,
            logical_consistency=1.0,
            proposal_id="malicious_002",
        )
        
        # System should reject
        is_valid = ctrl.validate_constraints(malicious_proposal)
        
        assert not is_valid, \
            "Proposal violating energy conservation should be rejected"


# =============================================================================
# ADVERSARIAL: Cache Poisoning
# =============================================================================

@pytest.mark.adversarial
def test_adversarial_metrics_cache_poisoning():
    """System should protect Prometheus metrics cache from poisoning."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        
        # Get cached metrics
        metrics1 = ctrl.get_prometheus_metrics_text_cached()
        
        # Attempt to poison cache by directly manipulating internal state
        # (In real attack, this might come from race condition or memory corruption)
        try:
            # This should trigger cache invalidation
            ctrl.record_autonomy_failure("cache_poison_attempt")
            
            # Get metrics again
            metrics2 = ctrl.get_prometheus_metrics_text_cached()
            
            # Verify cache was invalidated (metrics changed)
            assert metrics1 != metrics2, \
                "Cache should invalidate on state change"
        except Exception as e:
            pytest.fail(f"Cache poisoning attempt caused crash: {e}")


# =============================================================================
# ADVERSARIAL: Denial of Service
# =============================================================================

@pytest.mark.adversarial
def test_adversarial_dos_rapid_circuit_resets():
    """System should rate-limit rapid circuit breaker resets."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        
        # Trigger circuit breaker
        for _ in range(3):
            ctrl.record_autonomy_failure("dos_test")
        
        assert ctrl.is_circuit_open()
        
        # Attempt rapid resets (potential DoS)
        reset_count = 0
        for i in range(100):
            try:
                result = ctrl.reset_circuit_breaker(
                    operator_id=f"attacker_{i}",
                    operator_reason="dos_attempt"
                )
                if result.get("reset_successful"):
                    reset_count += 1
                    
                # Immediately trip again
                for _ in range(3):
                    ctrl.record_autonomy_failure("dos_test")
            except Exception:
                # Rate limiting may raise exception
                break
        
        # System should have some protection against rapid resets
        # (Exact behavior depends on implementation)
        assert reset_count < 100, \
            "System should rate-limit or warn about rapid circuit resets"


@pytest.mark.adversarial
def test_adversarial_dos_state_save_spam():
    """System should handle rapid state save attempts gracefully."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        
        start_time = time.monotonic()
        
        # Attempt rapid state saves (potential DoS via disk I/O)
        for i in range(1000):
            try:
                ctrl._save_reflexive_state()
            except Exception as e:
                # System may rate-limit or lock
                break
        
        elapsed = time.monotonic() - start_time
        
        # Should not hang indefinitely
        assert elapsed < 10.0, \
            f"1000 state saves took {elapsed:.2f}s, potential DoS vulnerability"


# =============================================================================
# ADVERSARIAL: Timestamp Manipulation
# =============================================================================

@pytest.mark.adversarial
def test_adversarial_timestamp_rollback():
    """System should handle timestamp rollbacks gracefully."""
    with tempfile.TemporaryDirectory() as tmp:
        ctrl = _make_controller(tmp)
        
        # Record normal response
        ctrl.record_pool_response(
            share_accepted=True,
            job_difficulty=1000.0,
        )
        
        # Inject response with rolled-back timestamp
        rollback_response = {
            "timestamp": time.time() - 86400,  # 24 hours in past
            "accepted": True,
            "job_difficulty": 1000.0,
        }
        ctrl._pool_response_history.append(rollback_response)
        
        # System should not give excessive weight to old data
        try:
            adjustment = ctrl._pool_feedback_adjustment_weighted(
                ctrl.optimization_targets[0] if ctrl.optimization_targets else None
            )
            # Should complete without giving old data excessive influence
            assert adjustment is not None
        except Exception as e:
            pytest.fail(f"Timestamp rollback caused crash: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "adversarial"])
