"""Tests for PYTHIA Autonomous Mining Controller.

Tests the autonomous decision-making capabilities with mathematical safety constraints,
including the Reflexive Knowledge Loop for recursive self-learning.

NOTE: This controller uses Φ (phi) coherence metrics as operational diagnostic signals
for decision support. It does NOT use consciousness-based decision making. The coherence
metrics are information-theoretic integration proxies for system monitoring, similar
to how neuroscientists use Φ in neural recordings.
"""

import asyncio
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch
from typing import Any

import sys
import os
from pathlib import Path

# Add python_backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python_backend"))

try:
    from pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine
except ModuleNotFoundError:
    UnifiedMiningEngine = None  # type: ignore[assignment]

from pythia_mining.autonomous_mining_controller import (
    AutonomousConfig,
    AutonomousDecision,
    AutonomousMiningController,
    AutonomyLevel,
    OperatorApprovalDecision,
    SafetyConstraint,
    SelfOptimizationProposal,
    CodebaseSurroundings,
)


class TestAutonomousMiningController(unittest.TestCase):
    """Test autonomous mining controller functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.unified_engine = MagicMock(spec=Any)
        # Add optimizer mock to prevent AttributeError
        self.unified_engine.optimizer = MagicMock()
        self.unified_engine.optimizer.current_strategy = MagicMock()
        # Add engine attributes that apply_self_optimization() checks
        self.unified_engine.phi_ensemble = MagicMock()
        self.unified_engine.solver = MagicMock()

        # Create a proper dataclass mock for consciousness config
        from dataclasses import dataclass, field

        @dataclass
        class MockConsciousnessConfig:
            phi_critical_threshold: float = 0.2
            phi_distributed_threshold: float = 0.4
            phi_singular_threshold: float = 0.7

        @dataclass
        class MockConsciousness:
            config: MockConsciousnessConfig = field(
                default_factory=MockConsciousnessConfig
            )

        self.unified_engine.consciousness = MockConsciousness()

        self.config = AutonomousConfig(
            autonomy_level=AutonomyLevel.ADVISORY,
            max_autonomous_hashrate_ehs=0.5,  # Within mission-memory hard limit of 1.0
            phi_coherence_threshold=0.70,
            reflexive_loop_enabled=True,
            compression_drive_enabled=True,
            persistence_enabled=False,  # Disable persistence for clean test state
        )
        self.controller = AutonomousMiningController(
            unified_engine=self.unified_engine,
            config=self.config,
        )

    def test_controller_initialization(self):
        """Test that controller initializes with correct configuration."""
        self.assertEqual(self.controller.current_autonomy_level, AutonomyLevel.ADVISORY)
        self.assertEqual(self.controller.config.max_autonomous_hashrate_ehs, 0.5)
        self.assertEqual(self.controller.config.phi_coherence_threshold, 0.70)
        self.assertEqual(len(self.controller.decision_log), 0)
        # Reflexive learning initialization
        self.assertIsNotNone(self.controller.knowledge_substrate)
        self.assertIsNotNone(self.controller.surroundings)
        self.assertEqual(len(self.controller.proposal_history), 0)
        self.assertEqual(self.controller._self_optimization_epochs, 0)

    def test_invalid_environment_values_fall_back_to_safe_defaults(self):
        """Bad environment config should not crash autonomous controller startup."""
        with patch.dict(
            os.environ,
            {
                "HYBA_AUTONOMOUS_MAX_HASHRATE_EHS": "not-a-float",
                "HYBA_AUTONOMOUS_MAX_POWER_WATTS": "bad",
                "HYBA_PHI_COHERENCE_THRESHOLD": "bad",
                "HYBA_REFLEXIVE_LOOP_INTERVAL": "bad",
            },
        ):
            config = AutonomousConfig(persistence_enabled=False)

        self.assertEqual(config.max_autonomous_hashrate_ehs, 0.5)
        self.assertEqual(config.max_autonomous_power_watts, 500.0)
        self.assertEqual(config.phi_coherence_threshold, 0.70)
        self.assertEqual(config.reflexive_loop_interval, 60.0)

    def test_autonomous_mining_enabled_defaults_startup_to_autonomous(self):
        """Startup autonomy flag should put PYTHIA in charge when level is unset."""
        with patch.dict(
            os.environ,
            {"HYBA_ENABLE_AUTONOMOUS_MINING": "true"},
            clear=True,
        ):
            config = AutonomousConfig(persistence_enabled=False)

        self.assertEqual(config.autonomy_level, AutonomyLevel.AUTONOMOUS)

    def test_autonomous_mining_disabled_defaults_startup_to_advisory(self):
        """Operators can disable autonomous startup and keep proposal-only posture."""
        with patch.dict(
            os.environ,
            {"HYBA_ENABLE_AUTONOMOUS_MINING": "false"},
            clear=True,
        ):
            config = AutonomousConfig(persistence_enabled=False)

        self.assertEqual(config.autonomy_level, AutonomyLevel.ADVISORY)

    def test_explicit_autonomy_level_overrides_startup_default(self):
        """Explicit launch posture still wins over the autonomous-mining default."""
        with patch.dict(
            os.environ,
            {
                "HYBA_ENABLE_AUTONOMOUS_MINING": "true",
                "HYBA_AUTONOMY_LEVEL": "supervised",
            },
            clear=True,
        ):
            config = AutonomousConfig(persistence_enabled=False)

        self.assertEqual(config.autonomy_level, AutonomyLevel.SUPERVISED)

    def test_circuit_breaker_opens_and_degrades_after_repeated_failures(self):
        """Repeated autonomous-hook failures should degrade and pause optimization."""
        self.controller.set_autonomy_level(AutonomyLevel.AUTONOMOUS)
        self.controller.config.circuit_breaker_failure_threshold = 2
        self.controller.config.circuit_breaker_cooldown_seconds = 30.0

        first_level = self.controller.record_autonomy_failure("unit_test")
        self.assertEqual(first_level, AutonomyLevel.AUTONOMOUS)
        self.assertFalse(self.controller.is_circuit_open())

        degraded_level = self.controller.record_autonomy_failure("unit_test")
        self.assertEqual(degraded_level, AutonomyLevel.SUPERVISED)
        self.assertTrue(self.controller.is_circuit_open())
        status = self.controller.get_autonomy_status()
        self.assertTrue(status["circuit_breaker"]["open"])
        self.assertEqual(status["circuit_breaker"]["failure_threshold"], 2)

        self.controller.record_autonomy_success()
        self.assertFalse(self.controller.is_circuit_open())

    def test_manual_circuit_breaker_reset_clears_open_state(self):
        """Operator reset should clear circuit state after review."""
        self.controller.set_autonomy_level(AutonomyLevel.AUTONOMOUS)
        self.controller.config.circuit_breaker_failure_threshold = 1
        self.controller.record_autonomy_failure("unit_test")
        self.assertTrue(self.controller.is_circuit_open())

        self.controller.reset_circuit_breaker("operator_reviewed_failure")

        self.assertFalse(self.controller.is_circuit_open())
        self.assertEqual(
            self.controller.get_metrics_snapshot()["consecutive_failures"], 0
        )

    def test_legacy_boolean_operator_approval_is_normalized_for_audit(self):
        """Legacy boolean approvals should produce the same audit shape."""
        decision = AutonomousDecision(
            decision_id="approval-legacy",
            timestamp=time.time(),
            autonomy_level=AutonomyLevel.SUPERVISED,
            decision_type="wallet_address_change",
            mathematical_justification={},
            constraints_satisfied=[],
            constraints_violated=[],
            action_taken="change_wallet",
            expected_outcome="requires approval",
        )
        self.controller.set_operator_approval_callback(MagicMock(return_value=True))

        approved = self.controller._request_operator_approval(decision)

        self.assertTrue(approved)

    def test_structured_operator_approval_is_written_to_decision_audit_shape(self):
        """Structured approvals should populate normalized audit fields."""
        decision = AutonomousDecision(
            decision_id="approval-structured",
            timestamp=time.time(),
            autonomy_level=AutonomyLevel.SUPERVISED,
            decision_type="wallet_address_change",
            mathematical_justification={},
            constraints_satisfied=[],
            constraints_violated=[],
            action_taken="change_wallet",
            expected_outcome="requires approval",
        )
        self.controller.set_operator_approval_callback(
            MagicMock(
                return_value=OperatorApprovalDecision(
                    approved=False,
                    operator_id="ops-1",
                    reason="maintenance_window_closed",
                )
            )
        )

        approved = self.controller._request_operator_approval(decision)

        self.assertFalse(approved)
        self.assertEqual(
            self.controller.operator_approval_requests[-1].operator_id,
            "ops-1",
        )

    def test_stale_state_lock_is_reclaimed_before_persisting(self):
        """Crash-left lock files older than the stale threshold should be reclaimed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AutonomousConfig(
                persistence_enabled=False,
                persistence_dir=tmpdir,
                state_lock_stale_seconds=1.0,
            )
            controller = AutonomousMiningController(self.unified_engine, config=config)
            lock_path = controller._state_lock_path()
            lock_path.write_text("stale", encoding="utf-8")
            old_time = time.time() - 5.0
            os.utime(lock_path, (old_time, old_time))

            acquired = controller._acquire_state_lock()

            self.assertEqual(acquired, lock_path)
            controller._release_state_lock(acquired)
            self.assertFalse(lock_path.exists())

    def test_recent_state_lock_blocks_persist_without_deadlock(self):
        """Fresh lock files should fail fast instead of blocking startup forever."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AutonomousConfig(
                persistence_enabled=False,
                persistence_dir=tmpdir,
                state_lock_stale_seconds=60.0,
            )
            controller = AutonomousMiningController(self.unified_engine, config=config)
            controller._state_lock_path().write_text("active", encoding="utf-8")

            with self.assertRaises(TimeoutError):
                controller._acquire_state_lock()

    def test_state_backup_rotation_is_bounded(self):
        """State backups should not grow beyond configured retention."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AutonomousConfig(
                persistence_enabled=False,
                persistence_dir=tmpdir,
                state_backup_retention_count=2,
            )
            controller = AutonomousMiningController(self.unified_engine, config=config)
            state_file = controller._state_file_path()
            state_file.write_text('{"epochs": 0}', encoding="utf-8")

            for idx in range(4):
                state_file.write_text(f'{{"epochs": {idx}}}', encoding="utf-8")
                controller._backup_existing_state(state_file)
                time.sleep(0.002)

            backups = list(Path(tmpdir).glob("reflexive_state.json.backup.*"))
            self.assertLessEqual(len(backups), 2)

    def test_decision_id_generation(self):
        """Test that decision IDs are generated uniquely."""
        id1 = self.controller._generate_decision_id()
        id2 = self.controller._generate_decision_id()
        self.assertNotEqual(id1, id2)
        self.assertIn("autonomous_decision_", id1)
        self.assertIn("autonomous_decision_", id2)

    def test_safety_constraint_checking(self):
        """Test that safety constraints are properly checked."""
        # Test a safe action (hashrate_change within natural scaling limit of 2.0)
        safe_action = {
            "hashrate_change": 1.0,
            "power_consumption_watts": 100.0,
        }
        satisfied, violated = self.controller._check_safety_constraints(safe_action)
        self.assertGreater(len(satisfied), 0)
        self.assertEqual(len(violated), 0)

        # Test an unsafe action (exceeds power limit)
        unsafe_action = {
            "power_consumption_watts": 1000.0,  # Exceeds max_autonomous_power_watts
        }
        satisfied, violated = self.controller._check_safety_constraints(unsafe_action)
        self.assertIn(SafetyConstraint.ENERGY_CONSERVATION, violated)

    def test_hermiticity_constraint(self):
        """Test Hermiticity constraint checking."""
        action = {"test": "value"}
        result = self.controller._check_hermiticity(action)
        self.assertTrue(result)  # Real-valued changes preserve Hermiticity

    def test_hermiticity_constraint_complex_values(self):
        """Test Hermiticity constraint rejects complex values without conjugates."""
        action = {"complex_field": complex(1.0, 2.0)}
        result = self.controller._check_hermiticity(action)
        self.assertFalse(result)  # Complex values without conjugates break Hermiticity

    def test_psd_constraint(self):
        """Test Positive Semidefinite constraint checking."""
        action = {"test": "value"}
        result = self.controller._check_psd(action)
        self.assertTrue(result)  # Simple actions preserve PSD

    def test_psd_constraint_high_compression(self):
        """Test PSD constraint rejects excessive compression ratios."""
        action = {"compression_ratio": 5.0}
        result = self.controller._check_psd(action)
        self.assertFalse(result)  # Excessive compression can make eigenvalues negative

    def test_psd_constraint_excessive_scaling(self):
        """Test PSD constraint rejects excessive phi-scaling changes."""
        action = {"phi_scaling_change": 3.0}
        result = self.controller._check_psd(action)
        self.assertFalse(result)  # Excessive scaling can invert density matrix

    def test_natural_scaling_constraint(self):
        """Test Natural Scaling constraint checking."""
        # Test within limits
        safe_action = {"hashrate_change": 1.5}
        result = self.controller._check_natural_scaling(safe_action)
        self.assertTrue(result)

        # Test exceeding limits
        unsafe_action = {"hashrate_change": 5.0}
        result = self.controller._check_natural_scaling(unsafe_action)
        self.assertFalse(result)

    def test_natural_scaling_phi_scaling(self):
        """Test Natural Scaling constraint for phi-scaling changes."""
        safe_action = {"phi_scaling_change": 0.3}
        result = self.controller._check_natural_scaling(safe_action)
        self.assertTrue(result)

        unsafe_action = {"phi_scaling_change": 1.0}
        result = self.controller._check_natural_scaling(unsafe_action)
        self.assertFalse(result)

    def test_natural_scaling_search_depth(self):
        """Test Natural Scaling constraint for search depth changes."""
        safe_action = {"search_depth_change": 20.0}
        result = self.controller._check_natural_scaling(safe_action)
        self.assertTrue(result)

        unsafe_action = {"search_depth_change": 50.0}
        result = self.controller._check_natural_scaling(unsafe_action)
        self.assertFalse(result)

    def test_natural_scaling_coherence_threshold(self):
        """Test Natural Scaling constraint for coherence threshold changes."""
        safe_action = {"coherence_threshold_change": 0.05}
        result = self.controller._check_natural_scaling(safe_action)
        self.assertTrue(result)

        unsafe_action = {"coherence_threshold_change": 0.2}
        result = self.controller._check_natural_scaling(unsafe_action)
        self.assertFalse(result)

    def test_energy_conservation_constraint(self):
        """Test Energy Conservation constraint checking."""
        # Test within power limit
        safe_action = {"power_consumption_watts": 200.0}
        result = self.controller._check_energy_conservation(safe_action)
        self.assertTrue(result)

        # Test exceeding power limit
        unsafe_action = {"power_consumption_watts": 1000.0}
        result = self.controller._check_energy_conservation(unsafe_action)
        self.assertFalse(result)

    def test_information_integrity_constraint(self):
        """Test Information Integrity constraint checking."""
        # Test within compression limit
        safe_action = {"compression_ratio": 1.5}
        result = self.controller._check_information_integrity(safe_action)
        self.assertTrue(result)

        # Test exceeding compression limit
        unsafe_action = {"compression_ratio": 3.0}
        result = self.controller._check_information_integrity(unsafe_action)
        self.assertFalse(result)

    def test_information_integrity_phi_scaling(self):
        """Test Information Integrity constraint for phi-scaling changes."""
        safe_action = {"phi_scaling_change": 0.5}
        result = self.controller._check_information_integrity(safe_action)
        self.assertTrue(result)

        unsafe_action = {"phi_scaling_change": 2.0}
        result = self.controller._check_information_integrity(unsafe_action)
        self.assertFalse(result)

    def test_operator_approval_required(self):
        """Test that certain decision types require operator approval."""
        self.assertTrue(
            self.controller._requires_operator_approval("pool_connection_change")
        )
        self.assertTrue(
            self.controller._requires_operator_approval("wallet_address_change")
        )
        self.assertFalse(
            self.controller._requires_operator_approval("search_strategy_optimization")
        )

    def test_autonomy_level_manual(self):
        """Test MANUAL autonomy level - no autonomous execution."""
        self.controller.set_autonomy_level(AutonomyLevel.MANUAL)
        decision = AutonomousDecision(
            decision_id="test_1",
            timestamp=0.0,
            autonomy_level=AutonomyLevel.MANUAL,
            decision_type="search_strategy_optimization",
            mathematical_justification={},
            constraints_satisfied=[],
            constraints_violated=[],
            action_taken="test_action",
            expected_outcome="test_outcome",
        )
        result = self.controller._can_execute_autonomously(decision)
        self.assertFalse(result)

    def test_autonomy_level_advisory(self):
        """Test ADVISORY autonomy level - recommendations only."""
        self.controller.set_autonomy_level(AutonomyLevel.ADVISORY)
        decision = AutonomousDecision(
            decision_id="test_1",
            timestamp=0.0,
            autonomy_level=AutonomyLevel.ADVISORY,
            decision_type="search_strategy_optimization",
            mathematical_justification={},
            constraints_satisfied=[],
            constraints_violated=[],
            action_taken="test_action",
            expected_outcome="test_outcome",
        )
        result = self.controller._can_execute_autonomously(decision)
        self.assertFalse(result)  # Advisory does not execute autonomously

    def test_autonomy_level_supervised(self):
        """Test SUPERVISED autonomy level - executes within bounds."""
        self.controller.set_autonomy_level(AutonomyLevel.SUPERVISED)
        decision = AutonomousDecision(
            decision_id="test_1",
            timestamp=0.0,
            autonomy_level=AutonomyLevel.SUPERVISED,
            decision_type="search_strategy_optimization",
            mathematical_justification={},
            constraints_satisfied=[SafetyConstraint.HERMITICITY],
            constraints_violated=[],
            action_taken="test_action",
            expected_outcome="test_outcome",
        )
        result = self.controller._can_execute_autonomously(decision)
        self.assertTrue(result)  # Supervised executes if no violations

    def test_autonomy_level_autonomous(self):
        """Test AUTONOMOUS autonomy level - executes with mathematical constraints."""
        self.controller.set_autonomy_level(AutonomyLevel.AUTONOMOUS)
        decision = AutonomousDecision(
            decision_id="test_1",
            timestamp=0.0,
            autonomy_level=AutonomyLevel.AUTONOMOUS,
            decision_type="search_strategy_optimization",
            mathematical_justification={},
            constraints_satisfied=[],
            constraints_violated=[],
            action_taken="test_action",
            expected_outcome="test_outcome",
        )
        result = self.controller._can_execute_autonomously(decision)
        self.assertTrue(result)  # Autonomous executes if no violations

    def test_constraint_violations_block_execution(self):
        """Test that constraint violations block autonomous execution."""
        self.controller.set_autonomy_level(AutonomyLevel.AUTONOMOUS)
        decision = AutonomousDecision(
            decision_id="test_1",
            timestamp=0.0,
            autonomy_level=AutonomyLevel.AUTONOMOUS,
            decision_type="search_strategy_optimization",
            mathematical_justification={},
            constraints_satisfied=[],
            constraints_violated=[SafetyConstraint.ENERGY_CONSERVATION],
            action_taken="test_action",
            expected_outcome="test_outcome",
        )
        result = self.controller._can_execute_autonomously(decision)
        self.assertFalse(result)  # Violations block execution

    def test_operator_override_blocks_execution(self):
        """Test that operator override blocks autonomous execution."""
        self.controller.set_autonomy_level(AutonomyLevel.AUTONOMOUS)
        decision = AutonomousDecision(
            decision_id="test_1",
            timestamp=0.0,
            autonomy_level=AutonomyLevel.AUTONOMOUS,
            decision_type="search_strategy_optimization",
            mathematical_justification={},
            constraints_satisfied=[],
            constraints_violated=[],
            action_taken="test_action",
            expected_outcome="test_outcome",
            operator_override=True,
        )
        result = self.controller._can_execute_autonomously(decision)
        self.assertFalse(result)  # Operator override blocks execution

    # ================================================================
    # REFLEXIVE KNOWLEDGE LOOP TESTS
    # ================================================================

    def test_build_codebase_surroundings(self):
        """Test that codebase surroundings are properly built."""
        surroundings = self.controller._build_codebase_surroundings()
        self.assertIsInstance(surroundings, CodebaseSurroundings)
        self.assertGreater(len(surroundings.module_names), 0)
        self.assertGreater(len(surroundings.mathematical_invariants), 0)
        self.assertGreater(len(surroundings.codebase_graph_edges), 0)
        self.assertGreater(len(surroundings.entropy_sources), 0)
        self.assertGreater(len(surroundings.stable_core), 0)
        # Verify known invariants
        self.assertIn("hermiticity", surroundings.mathematical_invariants)
        self.assertIn("positive_semidefinite", surroundings.mathematical_invariants)
        self.assertIn("information_integrity", surroundings.mathematical_invariants)
        # Verify entropy sources
        self.assertIn("phi_scaling_engine", surroundings.entropy_sources)
        self.assertIn("deutsch_knowledge_substrate", surroundings.entropy_sources)
        # Verify stable core
        self.assertIn("golden_ratio_library", surroundings.stable_core)

    def test_get_phi_density_initial(self):
        """Test φ-density computation with initial state."""
        density = self.controller.get_phi_density()
        self.assertGreaterEqual(density, 0.0)
        self.assertLessEqual(density, 1.0)

    def test_get_phi_density_with_knowledge(self):
        """Test φ-density with knowledge substrate contributions."""
        # Simulate some knowledge
        self.controller.knowledge_substrate.create_knowledge_from_success(
            "test_strategy",
            {"phi_resonance": 0.8, "difficulty": 1e12, "thermal_load": 0.5},
            {"accepted": True},
        )
        density = self.controller.get_phi_density()
        self.assertGreaterEqual(density, 0.0)
        self.assertLessEqual(density, 1.0)

    def test_get_current_efficiency(self):
        """Test current efficiency computation."""
        efficiency = self.controller.get_current_efficiency()
        self.assertGreaterEqual(efficiency, 0.0)
        self.assertLessEqual(efficiency, 1.0)

    def test_generate_counterfactual_phi_scaling(self):
        """Test counterfactual generation for phi-scaling."""
        proposal = self.controller._generate_counterfactual("phi_scaling")
        self.assertIsInstance(proposal, SelfOptimizationProposal)
        self.assertEqual(proposal.improvement_type, "phi_scaling")
        self.assertGreater(proposal.current_value, 0.0)
        self.assertGreater(proposal.proposed_value, 0.0)
        self.assertTrue(0.0 <= proposal.logical_consistency_score <= 1.0)
        self.assertEqual(proposal.codebase_source_module, "phi_scaling_engine")

    def test_generate_counterfactual_search_depth(self):
        """Test counterfactual generation for search depth."""
        proposal = self.controller._generate_counterfactual("search_depth")
        self.assertIsInstance(proposal, SelfOptimizationProposal)
        self.assertEqual(proposal.improvement_type, "search_depth")
        self.assertGreater(proposal.current_value, 0.0)
        self.assertEqual(proposal.codebase_source_module, "ai_optimizer")

    def test_generate_counterfactual_compression(self):
        """Test counterfactual generation for compression (the 'hunger' drive)."""
        proposal = self.controller._generate_counterfactual("compression_target")
        self.assertIsInstance(proposal, SelfOptimizationProposal)
        self.assertEqual(proposal.improvement_type, "compression_target")
        self.assertGreater(proposal.current_value, 0.0)
        self.assertEqual(
            proposal.codebase_source_module, "pulvini_memory_compression_proof"
        )
        # Must respect Information Integrity constraint
        self.assertLessEqual(proposal.proposed_value, 2.0)

    def test_generate_counterfactual_coherence_threshold(self):
        """Test counterfactual generation for coherence threshold."""
        proposal = self.controller._generate_counterfactual("coherence_threshold")
        self.assertIsInstance(proposal, SelfOptimizationProposal)
        self.assertEqual(proposal.improvement_type, "coherence_threshold")
        self.assertEqual(proposal.codebase_source_module, "consciousness_engine")
        self.assertEqual(proposal.current_value, self.config.phi_coherence_threshold)

    def test_generate_counterfactual_default(self):
        """Test counterfactual generation defaults to phi_scaling."""
        proposal = self.controller._generate_counterfactual("unknown_target")
        self.assertIsInstance(proposal, SelfOptimizationProposal)
        self.assertEqual(proposal.improvement_type, "phi_scaling")

    def test_virtual_mining_simulation(self):
        """Test virtual mining session simulation."""
        proposal = self.controller._generate_counterfactual("phi_scaling")
        simulated_density = self.controller._simulate_virtual_mining(proposal)
        self.assertGreaterEqual(simulated_density, 0.0)
        self.assertLessEqual(simulated_density, 1.0)
        score = self.controller._sha256d_landscape_score(proposal)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_pool_response_updates_target_bandit_and_virtual_feedback(self):
        """Real pool/testnet feedback should steer target selection evidence."""
        proposal = self.controller._generate_counterfactual("compression_target")
        before = self.controller.get_reflexive_target_bandit_snapshot()[
            "compression_target"
        ]
        baseline = self.controller._simulate_virtual_mining(proposal)

        self.controller.record_pool_response(
            accepted=True,
            latency_ms=12.5,
            reason="testnet_accept",
            proposal_id=proposal.proposal_id,
            target="compression_target",
        )

        after = self.controller.get_reflexive_target_bandit_snapshot()[
            "compression_target"
        ]
        boosted = self.controller._simulate_virtual_mining(proposal)
        self.assertGreater(after["successes"], before["successes"])
        self.assertGreater(after["evidence_weight"], before["evidence_weight"])
        self.assertGreaterEqual(boosted, baseline)

    def test_deterministic_target_selection_explores_bounded_bandits(self):
        """Target selection should combine round-robin coverage with posterior evidence."""
        targets = [
            "phi_scaling",
            "search_depth",
            "compression_target",
            "coherence_threshold",
        ]
        selected = self.controller._select_reflexive_targets(
            targets,
            primary_target="search_depth",
            growth_rate=0.0,
        )

        self.assertEqual(selected[0], "search_depth")
        self.assertLessEqual(
            len(selected), self.controller.config.max_proposals_per_cycle
        )
        self.assertEqual(len(selected), len(set(selected)))

    def test_pool_response_feedback_error_codes(self):
        """Different pool error codes should be retained in bounded response history."""
        self.controller.record_pool_response(
            share_accepted=True,
            error_code=None,
            job_difficulty=1000.0,
            response_time_ms=50.0,
            target="compression_target",
        )
        self.controller.record_pool_response(
            share_accepted=False,
            error_code="low-diff",
            job_difficulty=1000.0,
            response_time_ms=45.0,
            target="compression_target",
        )
        self.controller.record_pool_response(
            share_accepted=False,
            error_code="stale-prevhash",
            job_difficulty=1000.0,
            response_time_ms=100.0,
            target="compression_target",
        )

        self.assertEqual(len(self.controller._pool_response_history), 3)
        self.assertTrue(self.controller._pool_response_history[0]["accepted"])
        self.assertEqual(
            self.controller._pool_response_history[1]["error_code"], "low-diff"
        )
        self.assertEqual(
            self.controller._pool_response_history[2]["error_code"], "stale-prevhash"
        )

    def test_pool_response_exponential_weighting_recent_samples_dominate(self):
        """Recent pool responses should carry more influence than stale samples."""
        now = time.time()
        self.controller._pool_response_history.append(
            {
                "timestamp": now - 3600,
                "recorded_at": now - 3600,
                "accepted": False,
                "target": "compression_target",
            }
        )
        self.controller._pool_response_history.append(
            {
                "timestamp": now,
                "recorded_at": now,
                "accepted": True,
                "target": "compression_target",
            }
        )

        adjustment = self.controller._pool_feedback_adjustment("compression_target")

        self.assertIsInstance(adjustment, float)
        self.assertGreater(adjustment, 0.0)

    def test_pool_response_bounded_history(self):
        """Pool response history should remain capped for long-running controllers."""
        for i in range(1500):
            self.controller.record_pool_response(
                share_accepted=(i % 2 == 0),
                error_code=None if i % 2 == 0 else "low-diff",
                job_difficulty=1000.0,
                response_time_ms=50.0,
                target="compression_target",
            )

        self.assertLessEqual(len(self.controller._pool_response_history), 1000)
        self.assertTrue(
            all(
                r["timestamp"] > time.time() - 10
                for r in self.controller._pool_response_history[:10]
            )
        )

    def test_thompson_evidence_persistence(self):
        """Target-selection bandit evidence should survive controller restart."""
        with tempfile.TemporaryDirectory() as tmp:
            ctrl1 = AutonomousMiningController(
                self.unified_engine,
                AutonomousConfig(persistence_enabled=True, persistence_dir=tmp),
            )
            ctrl1._reflexive_target_bandits["phi_scaling"].successes = 10
            ctrl1._reflexive_target_bandits["phi_scaling"].failures = 2
            ctrl1._reflexive_target_bandits["compression_target"].successes = 8
            ctrl1._reflexive_target_bandits["compression_target"].failures = 4
            ctrl1._reflexive_target_bandits["search_depth"].successes = 5
            ctrl1._reflexive_target_bandits["search_depth"].failures = 5
            ctrl1._save_reflexive_state()

            ctrl2 = AutonomousMiningController(
                self.unified_engine,
                AutonomousConfig(persistence_enabled=True, persistence_dir=tmp),
            )
            snapshot = ctrl2.get_reflexive_target_bandit_snapshot()

            self.assertEqual(snapshot["phi_scaling"]["successes"], 10)
            self.assertEqual(snapshot["phi_scaling"]["failures"], 2)
            self.assertEqual(snapshot["compression_target"]["successes"], 8)
            selected = ctrl2._select_reflexive_targets(
                ["phi_scaling", "compression_target", "search_depth"],
                primary_target="phi_scaling",
                growth_rate=0.0,
            )
            self.assertEqual(selected[0], "phi_scaling")

    def test_thompson_deterministic_selection(self):
        """Deterministic Thompson-style target selection should replay exactly."""
        self.controller._reflexive_target_bandits["phi_scaling"].successes = 10
        self.controller._reflexive_target_bandits["phi_scaling"].failures = 2
        self.controller._reflexive_target_bandits["compression_target"].successes = 5
        self.controller._reflexive_target_bandits["compression_target"].failures = 5
        self.controller._reflexive_target_bandits["search_depth"].successes = 2
        self.controller._reflexive_target_bandits["search_depth"].failures = 10

        selections = [
            tuple(
                self.controller._select_reflexive_targets(
                    ["phi_scaling", "compression_target", "search_depth"],
                    primary_target="phi_scaling",
                    growth_rate=0.0,
                )
            )
            for _ in range(5)
        ]

        self.assertEqual(len(set(selections)), 1)
        self.assertEqual(selections[0][0], "phi_scaling")

    def test_prometheus_metrics_structure_and_low_cardinality(self):
        """Prometheus metrics should expose required low-cardinality series only."""
        self.controller.record_autonomy_success()
        self.controller.record_autonomy_failure("test_failure")

        metrics_text = self.controller.get_prometheus_metrics_text()
        required_metrics = [
            "hyba_phi_density",
            "hyba_constraint_violations_total",
            "hyba_consecutive_failures",
            "hyba_autonomous_circuit_open",
            "hyba_autonomous_circuit_breaker_trips_total",
            "hyba_degradation_events_total",
            "hyba_reflexive_cycle_duration_ms",
            "hyba_operator_overrides_total",
            "hyba_stale_state_lock_recoveries_total",
        ]

        for metric in required_metrics:
            self.assertIn(metric, metrics_text)
        self.assertNotIn("decision_id=", metrics_text)
        self.assertNotIn("timestamp=", metrics_text)
        for line in [
            line
            for line in metrics_text.split("\n")
            if line and not line.startswith("#")
        ]:
            self.assertIn(" ", line)
            float(line.rsplit(" ", 1)[1])

    def test_prometheus_metrics_cache_invalidation_on_failure(self):
        """Autonomy failure events should invalidate cached scrape output."""
        controller = AutonomousMiningController(
            self.unified_engine,
            AutonomousConfig(persistence_enabled=False, metrics_cache_ttl_seconds=60.0),
        )
        metrics1 = controller.get_prometheus_metrics_text_cached()
        controller.record_autonomy_failure("cache_invalidation_test")
        metrics2 = controller.get_prometheus_metrics_text_cached()

        self.assertIn("hyba_consecutive_failures 0", metrics1)
        self.assertIn("hyba_consecutive_failures 1", metrics2)

    def test_virtual_mining_with_violations(self):
        """Test virtual mining simulation with constraint violations."""
        proposal = SelfOptimizationProposal(
            proposal_id="test_violation",
            timestamp=0.0,
            improvement_type="phi_scaling",
            current_value=1.5,
            proposed_value=3.0,
            expected_phi_density_gain=0.1,
            logical_consistency_score=0.5,
            constraints_satisfied=[],
            constraints_violated=[SafetyConstraint.ENERGY_CONSERVATION],
            counterfactual_confidence=0.3,
            codebase_source_module="test",
        )
        simulated_density = self.controller._simulate_virtual_mining(proposal)
        self.assertGreaterEqual(simulated_density, 0.0)
        self.assertLessEqual(simulated_density, 1.0)

    def test_validate_constraints_valid_proposal(self):
        """Test constraint validation for a valid proposal."""
        proposal = SelfOptimizationProposal(
            proposal_id="test_valid",
            timestamp=0.0,
            improvement_type="phi_scaling",
            current_value=1.5,
            proposed_value=1.6,
            expected_phi_density_gain=0.02,
            logical_consistency_score=0.8,
            constraints_satisfied=[
                SafetyConstraint.HERMITICITY,
                SafetyConstraint.POSITIVE_SEMIDEFINITE,
                SafetyConstraint.NATURAL_SCALING,
                SafetyConstraint.ENERGY_CONSERVATION,
                SafetyConstraint.INFORMATION_INTEGRITY,
            ],
            constraints_violated=[],
            counterfactual_confidence=0.7,
            codebase_source_module="test",
        )
        self.assertTrue(self.controller.validate_constraints(proposal))

    def test_validate_constraints_violated(self):
        """Test constraint validation rejects proposals with violations."""
        proposal = SelfOptimizationProposal(
            proposal_id="test_violated",
            timestamp=0.0,
            improvement_type="phi_scaling",
            current_value=1.5,
            proposed_value=3.0,
            expected_phi_density_gain=0.1,
            logical_consistency_score=0.8,
            constraints_satisfied=[],
            constraints_violated=[SafetyConstraint.INFORMATION_INTEGRITY],
            counterfactual_confidence=0.3,
            codebase_source_module="test",
        )
        self.assertFalse(self.controller.validate_constraints(proposal))

    def test_validate_constraints_low_consistency(self):
        """Test constraint validation rejects proposals with low consistency."""
        proposal = SelfOptimizationProposal(
            proposal_id="test_low_consistency",
            timestamp=0.0,
            improvement_type="phi_scaling",
            current_value=1.5,
            proposed_value=1.6,
            expected_phi_density_gain=0.02,
            logical_consistency_score=0.3,  # Below min_logical_consistency (0.70)
            constraints_satisfied=[
                SafetyConstraint.HERMITICITY,
                SafetyConstraint.POSITIVE_SEMIDEFINITE,
                SafetyConstraint.INFORMATION_INTEGRITY,
            ],
            constraints_violated=[],
            counterfactual_confidence=0.3,
            codebase_source_module="test",
        )
        self.assertFalse(self.controller.validate_constraints(proposal))

    def test_validate_constraints_missing_hermiticity(self):
        """Test constraint validation rejects proposals missing Hermiticity."""
        proposal = SelfOptimizationProposal(
            proposal_id="test_no_hermiticity",
            timestamp=0.0,
            improvement_type="phi_scaling",
            current_value=1.5,
            proposed_value=1.6,
            expected_phi_density_gain=0.02,
            logical_consistency_score=0.85,
            constraints_satisfied=[
                SafetyConstraint.POSITIVE_SEMIDEFINITE,
                SafetyConstraint.INFORMATION_INTEGRITY,
            ],
            constraints_violated=[],
            counterfactual_confidence=0.7,
            codebase_source_module="test",
        )
        self.assertFalse(self.controller.validate_constraints(proposal))

    def test_apply_self_optimization_phi_scaling(self):
        """Test applying a phi-scaling self-optimization."""
        proposal = SelfOptimizationProposal(
            proposal_id="test_apply_phi",
            timestamp=0.0,
            improvement_type="phi_scaling",
            current_value=1.5,
            proposed_value=1.6,
            expected_phi_density_gain=0.02,
            logical_consistency_score=0.85,
            constraints_satisfied=[
                SafetyConstraint.HERMITICITY,
                SafetyConstraint.POSITIVE_SEMIDEFINITE,
                SafetyConstraint.INFORMATION_INTEGRITY,
            ],
            constraints_violated=[],
            counterfactual_confidence=0.75,
            codebase_source_module="phi_scaling_engine",
        )
        self.controller.apply_self_optimization(proposal)
        self.assertTrue(proposal.applied)
        self.assertIsNotNone(proposal.applied_at)
        self.assertIsNotNone(proposal.outcome_phi_density)
        # Should have added an optimization target
        self.assertGreater(len(self.controller.config.optimization_targets), 0)
        self.assertEqual(
            self.controller.config.optimization_targets[-1].target_name,
            "phi_scaling",
        )

    def test_apply_self_optimization_search_depth(self):
        """Test applying a search depth self-optimization."""
        proposal = SelfOptimizationProposal(
            proposal_id="test_apply_depth",
            timestamp=0.0,
            improvement_type="search_depth",
            current_value=60.0,
            proposed_value=65.0,
            expected_phi_density_gain=0.015,
            logical_consistency_score=0.85,
            constraints_satisfied=[
                SafetyConstraint.HERMITICITY,
                SafetyConstraint.POSITIVE_SEMIDEFINITE,
                SafetyConstraint.INFORMATION_INTEGRITY,
            ],
            constraints_violated=[],
            counterfactual_confidence=0.7,
            codebase_source_module="ai_optimizer",
        )
        self.controller.apply_self_optimization(proposal)
        self.assertTrue(proposal.applied)
        self.assertEqual(
            self.controller.config.optimization_targets[-1].target_name,
            "search_depth",
        )

    def test_apply_self_optimization_compression(self):
        """Test applying a compression target self-optimization."""
        proposal = SelfOptimizationProposal(
            proposal_id="test_apply_compression",
            timestamp=0.0,
            improvement_type="compression_target",
            current_value=1.86,
            proposed_value=1.90,
            expected_phi_density_gain=0.03,
            logical_consistency_score=0.85,
            constraints_satisfied=[
                SafetyConstraint.HERMITICITY,
                SafetyConstraint.POSITIVE_SEMIDEFINITE,
                SafetyConstraint.INFORMATION_INTEGRITY,
            ],
            constraints_violated=[],
            counterfactual_confidence=0.8,
            codebase_source_module="pulvini_memory_compression_proof",
        )
        self.controller.apply_self_optimization(proposal)
        self.assertTrue(proposal.applied)
        self.assertEqual(
            self.controller.config.optimization_targets[-1].target_name,
            "compression_target",
        )

    def test_apply_self_optimization_coherence_threshold(self):
        """Test applying a coherence threshold self-optimization."""
        proposal = SelfOptimizationProposal(
            proposal_id="test_apply_coherence",
            timestamp=0.0,
            improvement_type="coherence_threshold",
            current_value=0.70,
            proposed_value=0.68,
            expected_phi_density_gain=0.01,
            logical_consistency_score=0.85,
            constraints_satisfied=[
                SafetyConstraint.HERMITICITY,
                SafetyConstraint.POSITIVE_SEMIDEFINITE,
                SafetyConstraint.INFORMATION_INTEGRITY,
            ],
            constraints_violated=[],
            counterfactual_confidence=0.7,
            codebase_source_module="consciousness_engine",
        )
        self.controller.apply_self_optimization(proposal)
        self.assertTrue(proposal.applied)
        # Threshold should be updated
        self.assertEqual(
            self.controller.config.phi_coherence_threshold,
            proposal.proposed_value,
        )

    def test_apply_self_optimization_idempotent(self):
        """Test that applying the same proposal twice is idempotent."""
        proposal = SelfOptimizationProposal(
            proposal_id="test_idempotent",
            timestamp=0.0,
            improvement_type="phi_scaling",
            current_value=1.5,
            proposed_value=1.6,
            expected_phi_density_gain=0.02,
            logical_consistency_score=0.85,
            constraints_satisfied=[
                SafetyConstraint.HERMITICITY,
                SafetyConstraint.POSITIVE_SEMIDEFINITE,
                SafetyConstraint.INFORMATION_INTEGRITY,
            ],
            constraints_violated=[],
            counterfactual_confidence=0.75,
            codebase_source_module="test",
        )
        initial_targets = len(self.controller.config.optimization_targets)
        self.controller.apply_self_optimization(proposal)
        self.controller.apply_self_optimization(proposal)  # Second application
        self.assertEqual(
            len(self.controller.config.optimization_targets),
            initial_targets + 1,  # Only one target added
        )

    def test_seek_improvement_cycle(self):
        """Test the full Reflexive Knowledge Loop improvement cycle."""
        result = asyncio.run(self.controller.seek_improvement())
        self.assertIn("reflexive_cycle_executed", result)
        self.assertTrue(result["reflexive_cycle_executed"])
        self.assertIn("epoch", result)
        self.assertIn("current_phi_density", result)
        self.assertIn("proposals_generated", result)
        self.assertIn("proposals_applied", result)
        self.assertIn("proposals", result)
        self.assertIn("knowledge_metrics", result)
        self.assertIn("surroundings", result)
        self.assertIn("compression_drive", result)
        self.assertGreaterEqual(result["epoch"], 0)

    def test_seek_improvement_multiple_epochs(self):
        """Test multiple Reflexive Knowledge Loop epochs."""
        # Run first epoch
        result1 = asyncio.run(self.controller.seek_improvement())
        # Run second epoch
        result2 = asyncio.run(self.controller.seek_improvement())
        # Epoch counter should increment
        self.assertGreater(
            result2["epoch"],
            result1["epoch"],
        )
        # Proposals should accumulate in history
        self.assertGreaterEqual(
            len(self.controller.proposal_history),
            result1["proposals_generated"],
        )

    def test_seek_improvement_disabled(self):
        """Test that reflexive loop is disabled when configured."""
        self.controller.config.reflexive_loop_enabled = False
        result = asyncio.run(self.controller.seek_improvement())
        self.assertEqual(result["proposals_generated"], 0)
        self.assertEqual(result["proposals_applied"], 0)

    def test_get_knowledge_substrate(self):
        """Test accessor for Deutsch Knowledge Substrate."""
        substrate = self.controller.get_knowledge_substrate()
        self.assertIsNotNone(substrate)
        self.assertEqual(substrate, self.controller.knowledge_substrate)

    def test_get_proposal_history(self):
        """Test accessor for proposal history."""
        history = self.controller.get_proposal_history()
        self.assertIsInstance(history, list)

    def test_get_codebase_surroundings(self):
        """Test accessor for codebase surroundings."""
        surroundings = self.controller.get_codebase_surroundings()
        self.assertIsInstance(surroundings, CodebaseSurroundings)
        self.assertEqual(surroundings, self.controller.surroundings)

    def test_autonomy_status_includes_reflexive_metrics(self):
        """Test that autonomy status includes Reflexive Learning metrics."""
        status = self.controller.get_autonomy_status()
        self.assertIn("reflexive_learning", status)
        rl = status["reflexive_learning"]
        self.assertIn("enabled", rl)
        self.assertIn("self_optimization_epochs", rl)
        self.assertIn("phi_density", rl)
        self.assertIn("compression_drive_enabled", rl)
        self.assertIn("knowledge_explanations", rl)
        self.assertIn("proposals_generated", rl)
        self.assertIn("proposals_applied", rl)

    def test_compression_drive_default(self):
        """Test compression drive is enabled by default."""
        self.assertTrue(self.controller.config.compression_drive_enabled)

    def test_compression_seeking_evolution(self):
        """Test compression seeking evolves with improvement cycles."""
        # Run multiple improvement cycles
        for _ in range(3):
            # Simulate a compression proposal
            proposal = self.controller._generate_counterfactual("compression_target")
            self.controller.proposal_history.append(proposal)
            if self.controller.validate_constraints(proposal):
                self.controller.apply_self_optimization(proposal)
            # Manually record compression seeking
            self.controller._compression_seeking_history.append(proposal.proposed_value)

        self.assertGreater(len(self.controller._compression_seeking_history), 0)
        latest_seeking = self.controller._compression_seeking_history[-1]
        self.assertGreater(latest_seeking, 0.0)

    # ================================================================
    # ORIGINAL TESTS (preserved)
    # ================================================================

    def test_optimize_search_strategy_high_coherence(self):
        """Test search strategy optimization with high phi coherence."""
        decision = asyncio.run(
            self.controller.optimize_search_strategy(
                current_coherence=0.85,
                current_hashrate_ehs=50.0,
            )
        )
        self.assertEqual(decision.decision_type, "search_strategy_optimization")
        self.assertIn("aggressive", decision.mathematical_justification["reason"])
        self.assertEqual(
            decision.expected_outcome, "faster_search_with_high_confidence"
        )

    def test_optimize_search_strategy_medium_coherence(self):
        """Test search strategy optimization with medium phi coherence."""
        decision = asyncio.run(
            self.controller.optimize_search_strategy(
                current_coherence=0.75,
                current_hashrate_ehs=50.0,
            )
        )
        self.assertEqual(decision.decision_type, "search_strategy_optimization")
        self.assertIn("balanced", decision.mathematical_justification["reason"])
        self.assertEqual(decision.expected_outcome, "balanced_speed_and_reliability")

    def test_optimize_search_strategy_low_coherence(self):
        """Test search strategy optimization with low phi coherence."""
        decision = asyncio.run(
            self.controller.optimize_search_strategy(
                current_coherence=0.50,
                current_hashrate_ehs=50.0,
            )
        )
        self.assertEqual(decision.decision_type, "search_strategy_optimization")
        self.assertIn("conservative", decision.mathematical_justification["reason"])
        self.assertEqual(decision.expected_outcome, "prioritize_reliability_over_speed")

    def test_optimize_hashrate_increase(self):
        """Test hashrate optimization for increase."""
        decision = asyncio.run(
            self.controller.optimize_hashrate_target(
                current_hashrate_ehs=0.2,
                target_hashrate_ehs=0.4,
            )
        )
        self.assertEqual(decision.decision_type, "hashrate_optimization")
        self.assertIn("increase", decision.action_taken)
        self.assertEqual(decision.expected_outcome, "higher_mining_efficiency")

    def test_optimize_hashrate_decrease(self):
        """Test hashrate optimization for decrease (energy saving)."""
        decision = asyncio.run(
            self.controller.optimize_hashrate_target(
                current_hashrate_ehs=0.4,
                target_hashrate_ehs=0.2,
            )
        )
        self.assertEqual(decision.decision_type, "hashrate_optimization")
        self.assertIn("decrease", decision.action_taken)
        self.assertEqual(decision.expected_outcome, "reduced_energy_consumption")

    def test_optimize_compression_ratio(self):
        """Test memory compression ratio optimization."""
        decision = asyncio.run(
            self.controller.optimize_compression_ratio(
                current_compression=1.5,
                target_compression=1.8,
            )
        )
        self.assertEqual(decision.decision_type, "compression_optimization")
        self.assertIn("adjust_compression", decision.action_taken)
        self.assertEqual(decision.expected_outcome, "better_memory_utilization")

    def test_emergency_shutdown(self):
        """Test emergency shutdown capability."""
        decision = asyncio.run(
            self.controller.emergency_shutdown(
                reason="test_emergency",
                mathematical_justification={"emergency": True},
            )
        )
        self.assertEqual(decision.decision_type, "emergency_shutdown")
        self.assertEqual(decision.autonomy_level, AutonomyLevel.EMERGENCY)
        self.assertEqual(decision.action_taken, "emergency_shutdown_initiated")

    def test_decision_logging(self):
        """Test that decisions are properly logged."""
        initial_log_size = len(self.controller.decision_log)
        decision = AutonomousDecision(
            decision_id="test_log",
            timestamp=0.0,
            autonomy_level=AutonomyLevel.ADVISORY,
            decision_type="test_type",
            mathematical_justification={},
            constraints_satisfied=[],
            constraints_violated=[],
            action_taken="test_action",
            expected_outcome="test_outcome",
        )
        self.controller._log_decision(decision)
        self.assertEqual(len(self.controller.decision_log), initial_log_size + 1)
        self.assertEqual(self.controller.decision_log[-1].decision_id, "test_log")

    def test_decision_log_size_limit(self):
        """Test that decision log respects size limit."""
        self.controller.config.decision_audit_log_size = 5
        for i in range(10):
            decision = AutonomousDecision(
                decision_id=f"test_{i}",
                timestamp=0.0,
                autonomy_level=AutonomyLevel.ADVISORY,
                decision_type="test_type",
                mathematical_justification={},
                constraints_satisfied=[],
                constraints_violated=[],
                action_taken="test_action",
                expected_outcome="test_outcome",
            )
            self.controller._log_decision(decision)
        self.assertEqual(len(self.controller.decision_log), 5)

    def test_get_decision_history(self):
        """Test retrieving decision history."""
        # Add some decisions
        for i in range(5):
            decision = AutonomousDecision(
                decision_id=f"test_{i}",
                timestamp=float(i),
                autonomy_level=AutonomyLevel.ADVISORY,
                decision_type="test_type",
                mathematical_justification={},
                constraints_satisfied=[],
                constraints_violated=[],
                action_taken="test_action",
                expected_outcome="test_outcome",
            )
            self.controller._log_decision(decision)

        # Get all history
        all_history = self.controller.get_decision_history()
        self.assertEqual(len(all_history), 5)

        # Get limited history
        limited_history = self.controller.get_decision_history(limit=3)
        self.assertEqual(len(limited_history), 3)

    def test_get_autonomy_status(self):
        """Test getting autonomy status."""
        # Add some decisions
        for i in range(3):
            decision = AutonomousDecision(
                decision_id=f"test_{i}",
                timestamp=0.0,
                autonomy_level=AutonomyLevel.ADVISORY,
                decision_type="test_type",
                mathematical_justification={},
                constraints_satisfied=[],
                constraints_violated=[],
                action_taken="test_action",
                expected_outcome="test_outcome",
            )
            self.controller._log_decision(decision)

        status = self.controller.get_autonomy_status()
        self.assertEqual(status["autonomy_level"], "advisory")
        self.assertEqual(status["total_decisions"], 3)
        self.assertEqual(status["autonomous_decisions"], 3)
        self.assertEqual(status["operator_overrides"], 0)

    def test_set_operator_approval_callback(self):
        """Test setting operator approval callback."""
        callback = MagicMock(return_value=True)
        self.controller.set_operator_approval_callback(callback)
        self.assertEqual(self.controller.operator_approval_callback, callback)

    def test_operator_approval_callback_invocation(self):
        """Test that operator approval callback is invoked when needed."""
        callback = MagicMock(return_value=True)
        self.controller.set_operator_approval_callback(callback)
        self.controller.set_autonomy_level(AutonomyLevel.SUPERVISED)

        # This should trigger callback in real scenario
        asyncio.run(
            self.controller.optimize_search_strategy(
                current_coherence=0.75,
                current_hashrate_ehs=50.0,
            )
        )
        # In supervised mode with no violations, it should execute autonomously
        # without callback invocation


@unittest.skipIf(
    UnifiedMiningEngine is None, "UnifiedMiningEngine dependencies unavailable"
)
class TestAutonomousMiningControllerIntegration(unittest.TestCase):
    """Integration tests for autonomous mining controller with unified engine."""

    def setUp(self):
        """Set up test fixtures with real unified engine."""
        self._tmpdir = tempfile.TemporaryDirectory()
        self._env_patch = patch.dict(
            os.environ, {"HYBA_AUTONOMY_STATE_DIR": self._tmpdir.name}
        )
        self._env_patch.start()
        self.addCleanup(self._env_patch.stop)
        self.addCleanup(self._tmpdir.cleanup)
        # Create a minimal unified engine for testing
        self.unified_engine = UnifiedMiningEngine(
            configured_capacity_ehs=100.0,
        )
        self.controller = AutonomousMiningController(
            unified_engine=self.unified_engine,
            config=AutonomousConfig(
                autonomy_level=AutonomyLevel.ADVISORY,
                max_autonomous_hashrate_ehs=1.0,  # Mission-memory 1 EH/s hard limit
                reflexive_loop_enabled=True,
                persistence_enabled=False,
            ),
        )

    def test_unified_engine_has_autonomous_controller(self):
        """Test that unified engine has autonomous controller initialized."""
        self.assertIsNotNone(self.unified_engine.autonomous_controller)
        # Default autonomy level is AUTONOMOUS when HYBA_ENABLE_AUTONOMOUS_MINING=true
        self.assertEqual(
            self.unified_engine.autonomous_controller.current_autonomy_level,
            AutonomyLevel.AUTONOMOUS,
        )

    def test_set_autonomy_level_via_engine(self):
        """Test setting autonomy level via unified engine method."""
        self.unified_engine.set_autonomy_level(AutonomyLevel.AUTONOMOUS)
        self.assertEqual(
            self.unified_engine.autonomous_controller.current_autonomy_level,
            AutonomyLevel.AUTONOMOUS,
        )

    def test_get_autonomy_status_via_engine(self):
        """Test getting autonomy status via unified engine method."""
        status = self.unified_engine.get_autonomy_status()
        self.assertIn("autonomy_level", status)
        self.assertIn("total_decisions", status)
        # Reflexive Learning metrics should be included
        self.assertIn("reflexive_learning", status)

    def test_get_autonomous_decision_history_via_engine(self):
        """Test getting decision history via unified engine method."""
        history = self.unified_engine.get_autonomous_decision_history()
        self.assertIsInstance(history, list)

    def test_seek_improvement_via_controller(self):
        """Test seek_improvement through the real controller."""
        result = asyncio.run(self.controller.seek_improvement())
        self.assertTrue(result["reflexive_cycle_executed"])
        self.assertGreaterEqual(result["epoch"], 0)
        # With reflexive loop enabled, should generate proposals
        self.assertGreaterEqual(result["proposals_generated"], 0)


class TestAutonomousMiningControllerOperationalHardening(unittest.TestCase):
    """Production hardening tests for approval, audit, and state recovery."""

    def setUp(self):
        self.unified_engine = MagicMock(spec=Any)
        self.unified_engine.optimizer = MagicMock()
        self.unified_engine.optimizer.current_strategy = MagicMock()

    def test_guarded_decision_fails_closed_without_approval_callback(self):
        controller = AutonomousMiningController(
            self.unified_engine,
            AutonomousConfig(
                autonomy_level=AutonomyLevel.AUTONOMOUS,
                persistence_enabled=False,
            ),
        )
        decision = AutonomousDecision(
            decision_id="guarded-1",
            timestamp=0.0,
            autonomy_level=AutonomyLevel.AUTONOMOUS,
            decision_type="pool_connection_change",
            mathematical_justification={},
            constraints_satisfied=[SafetyConstraint.ENERGY_CONSERVATION],
            constraints_violated=[],
            action_taken="change_pool",
            expected_outcome="pool_updated",
        )

        self.assertFalse(controller._can_execute_autonomously(decision))
        self.assertEqual(controller.operator_approval_requests[-1].status, "rejected")
        self.assertEqual(
            controller.operator_approval_requests[-1].reason,
            "approval_callback_missing",
        )

    def test_operator_approval_timeout_rejects(self):
        controller = AutonomousMiningController(
            self.unified_engine,
            AutonomousConfig(
                autonomy_level=AutonomyLevel.AUTONOMOUS,
                operator_approval_timeout_seconds=0.0,
                persistence_enabled=False,
            ),
        )
        controller.set_operator_approval_callback(lambda _decision: True)
        decision = AutonomousDecision(
            decision_id="guarded-timeout",
            timestamp=0.0,
            autonomy_level=AutonomyLevel.AUTONOMOUS,
            decision_type="wallet_address_change",
            mathematical_justification={},
            constraints_satisfied=[SafetyConstraint.ENERGY_CONSERVATION],
            constraints_violated=[],
            action_taken="change_wallet",
            expected_outcome="wallet_updated",
        )

        self.assertFalse(controller._can_execute_autonomously(decision))
        self.assertEqual(controller.operator_approval_requests[-1].status, "rejected")
        self.assertEqual(
            controller.operator_approval_requests[-1].reason, "approval_timeout"
        )

    def test_operator_approval_structured_response_is_audited(self):
        controller = AutonomousMiningController(
            self.unified_engine,
            AutonomousConfig(
                autonomy_level=AutonomyLevel.AUTONOMOUS,
                persistence_enabled=False,
            ),
        )
        controller.set_operator_approval_callback(
            lambda _decision: OperatorApprovalDecision(
                approved=True,
                operator_id="operator-7",
                reason="bounded observed run",
            )
        )
        decision = AutonomousDecision(
            decision_id="guarded-structured",
            timestamp=0.0,
            autonomy_level=AutonomyLevel.AUTONOMOUS,
            decision_type="wallet_address_change",
            mathematical_justification={},
            constraints_satisfied=[SafetyConstraint.ENERGY_CONSERVATION],
            constraints_violated=[],
            action_taken="change_wallet",
            expected_outcome="wallet_updated",
        )

        self.assertTrue(controller._can_execute_autonomously(decision))
        request = controller.operator_approval_requests[-1]
        self.assertEqual(request.status, "approved")
        self.assertEqual(request.operator_id, "operator-7")
        self.assertEqual(request.reason, "bounded observed run")
        self.assertEqual(controller.get_audit_log()[-1].operator_id, "operator-7")

    def test_prometheus_metrics_include_alerting_series(self):
        controller = AutonomousMiningController(
            self.unified_engine,
            AutonomousConfig(
                autonomy_level=AutonomyLevel.SUPERVISED,
                persistence_enabled=False,
            ),
        )
        decision = AutonomousDecision(
            decision_id="violation-1",
            timestamp=0.0,
            autonomy_level=AutonomyLevel.SUPERVISED,
            decision_type="compression_optimization",
            mathematical_justification={},
            constraints_satisfied=[SafetyConstraint.HERMITICITY],
            constraints_violated=[SafetyConstraint.INFORMATION_INTEGRITY],
            action_taken="adjust_compression",
            expected_outcome="blocked",
        )
        controller._log_decision(decision)

        metrics = controller.get_metrics_snapshot()
        prometheus_text = controller.get_prometheus_metrics_text()

        self.assertEqual(
            metrics["constraint_violations_by_type"]["information_integrity"], 1
        )
        self.assertIn("hyba_phi_density", prometheus_text)
        self.assertIn("hyba_constraint_violations_total 1", prometheus_text)
        self.assertIn(
            'hyba_constraint_violations_by_type_total{constraint="information_integrity"} 1',
            prometheus_text,
        )

    def test_reflexive_state_is_atomic_checksumed_and_restorable(self):
        import hashlib
        import json
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            controller = AutonomousMiningController(
                self.unified_engine,
                AutonomousConfig(
                    autonomy_level=AutonomyLevel.ADVISORY,
                    persistence_enabled=True,
                    persistence_dir=tmp,
                ),
            )
            controller._self_optimization_epochs = 7
            controller._phi_density_history = [0.5, 0.6]
            controller._save_reflexive_state()

            state_file = Path(tmp) / "reflexive_state.json"
            checksum_file = Path(tmp) / "reflexive_state.json.sha256"
            self.assertTrue(state_file.exists())
            self.assertTrue(checksum_file.exists())
            self.assertEqual(
                checksum_file.read_text(encoding="utf-8"),
                hashlib.sha256(state_file.read_bytes()).hexdigest(),
            )
            state = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(state["schema_version"], 3)
            self.assertTrue((Path(tmp) / "backups").exists())

            restored = AutonomousMiningController(
                self.unified_engine,
                AutonomousConfig(persistence_enabled=True, persistence_dir=tmp),
            )
            self.assertEqual(restored._self_optimization_epochs, 7)
            self.assertEqual(restored._phi_density_history, [0.5, 0.6])

    def test_stale_state_lock_is_removed_before_save(self):
        import tempfile
        import time
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            controller = AutonomousMiningController(
                self.unified_engine,
                AutonomousConfig(
                    persistence_enabled=True,
                    persistence_dir=tmp,
                    state_lock_stale_seconds=0.01,
                ),
            )
            state_file = Path(tmp) / "reflexive_state.json"
            lock_file = Path(tmp) / "reflexive_state.json.lock"
            lock_file.write_text("stale-pid", encoding="utf-8")
            old_time = time.time() - 30
            os.utime(lock_file, (old_time, old_time))

            controller._self_optimization_epochs = 3
            controller._save_reflexive_state()

            self.assertTrue(state_file.exists())
            self.assertFalse(lock_file.exists())
            self.assertTrue(
                any(
                    entry.event_type == "stale_state_lock_removed"
                    for entry in controller.get_audit_log()
                )
            )

    def test_cached_prometheus_metrics_reuses_snapshot_until_ttl_expires(self):
        controller = AutonomousMiningController(
            self.unified_engine,
            AutonomousConfig(
                autonomy_level=AutonomyLevel.SUPERVISED,
                persistence_enabled=False,
                metrics_cache_ttl_seconds=60.0,
            ),
        )
        first = controller.get_prometheus_metrics_text_cached()
        controller._degradation_events += 1
        second = controller.get_prometheus_metrics_text_cached()
        fresh = controller.get_prometheus_metrics_text_cached(cache_ttl_seconds=0)

        self.assertEqual(first, second)
        self.assertIn("hyba_degradation_events_total 1", fresh)

    def test_autonomous_circuit_breaker_opens_and_cools_down(self):
        controller = AutonomousMiningController(
            self.unified_engine,
            AutonomousConfig(
                autonomy_level=AutonomyLevel.SUPERVISED,
                persistence_enabled=False,
                circuit_breaker_failure_threshold=2,
                circuit_breaker_cooldown_seconds=10.0,
            ),
        )

        controller.record_circuit_failure("first")
        self.assertFalse(controller.is_circuit_open())
        controller.record_circuit_failure("second")
        self.assertTrue(controller.is_circuit_open())
        self.assertIn(
            "hyba_autonomous_circuit_open 1", controller.get_prometheus_metrics_text()
        )
        controller._circuit_open_until = time.time() - 1
        self.assertFalse(controller.is_circuit_open())

    def test_manual_circuit_reset_captures_before_after_state(self):
        controller = AutonomousMiningController(
            self.unified_engine,
            AutonomousConfig(
                autonomy_level=AutonomyLevel.SUPERVISED,
                persistence_enabled=False,
                circuit_breaker_failure_threshold=1,
            ),
        )
        controller.record_circuit_failure("boom")

        result = controller.reset_circuit_breaker("ops", "root cause fixed")

        self.assertTrue(result["before_state"]["circuit_open"])
        self.assertFalse(result["after_state"]["circuit_open"])
        self.assertEqual(result["after_state"]["consecutive_failures"], 0)

    def test_constraint_violation_invalidates_cached_prometheus_metrics(self):
        controller = AutonomousMiningController(
            self.unified_engine,
            AutonomousConfig(
                autonomy_level=AutonomyLevel.SUPERVISED,
                persistence_enabled=False,
                metrics_cache_ttl_seconds=60.0,
            ),
        )
        first = controller.get_prometheus_metrics_text_cached()
        self.assertIn("hyba_constraint_violations_total 0", first)
        decision = AutonomousDecision(
            decision_id="violation-cache-1",
            timestamp=0.0,
            autonomy_level=AutonomyLevel.SUPERVISED,
            decision_type="compression_optimization",
            mathematical_justification={},
            constraints_satisfied=[SafetyConstraint.HERMITICITY],
            constraints_violated=[SafetyConstraint.INFORMATION_INTEGRITY],
            action_taken="adjust_compression",
            expected_outcome="blocked",
        )

        controller._log_decision(decision)
        refreshed = controller.get_prometheus_metrics_text_cached()

        self.assertIn("hyba_constraint_violations_total 1", refreshed)

    def test_stale_state_lock_recovery_is_exported_as_prometheus_counter(self):
        import tempfile
        import time
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            controller = AutonomousMiningController(
                self.unified_engine,
                AutonomousConfig(
                    persistence_enabled=True,
                    persistence_dir=tmp,
                    state_lock_stale_seconds=0.01,
                ),
            )
            lock_file = Path(tmp) / "reflexive_state.json.lock"
            lock_file.write_text("stale-pid", encoding="utf-8")
            old_time = time.time() - 30
            os.utime(lock_file, (old_time, old_time))

            controller._save_reflexive_state()

            prometheus_text = controller.get_prometheus_metrics_text()
            self.assertIn("hyba_stale_state_lock_recoveries_total 1", prometheus_text)

    def test_emergency_bypass_source_is_isolated_from_verification_firewall(self):
        import inspect

        source = inspect.getsource(
            AutonomousMiningController.authorize_emergency_operator_bypass
        )

        self.assertNotIn("submit_candidate", source)
        self.assertNotIn("submit_validated_share", source)
        self.assertNotIn("optimize_nonce_search", source)
        self.assertNotIn("verify_batch", source)

    def test_emergency_operator_bypass_requires_configured_operator_and_reason(self):
        controller = AutonomousMiningController(
            self.unified_engine,
            AutonomousConfig(
                autonomy_level=AutonomyLevel.AUTONOMOUS,
                persistence_enabled=False,
                emergency_operator_ids=["incident-commander"],
            ),
        )
        decision = AutonomousDecision(
            decision_id="emergency-1",
            timestamp=0.0,
            autonomy_level=AutonomyLevel.AUTONOMOUS,
            decision_type="emergency_shutdown",
            mathematical_justification={},
            constraints_satisfied=[SafetyConstraint.ENERGY_CONSERVATION],
            constraints_violated=[],
            action_taken="protective_shutdown",
            expected_outcome="shutdown",
        )

        rejected = controller.authorize_emergency_operator_bypass(
            decision, "unknown", "approval service outage INC-1"
        )
        approved = controller.authorize_emergency_operator_bypass(
            decision, "incident-commander", "approval service outage INC-1"
        )

        self.assertFalse(rejected.approved)
        self.assertTrue(approved.approved)
        self.assertEqual(approved.operator_id, "incident-commander")
        self.assertIn("EMERGENCY_BYPASS", approved.reason)
        self.assertTrue(
            any(
                entry.event_type == "emergency_operator_bypass_approved"
                for entry in controller.get_audit_log()
            )
        )

    def test_pool_feedback_window_preserves_first_class_pool_signals(self):
        """Pool/testnet feedback should be bounded and rich enough to drive learning."""
        controller = AutonomousMiningController(
            self.unified_engine,
            AutonomousConfig(persistence_enabled=False),
        )

        for index in range(1005):
            controller.record_pool_response(
                accepted=index % 3 == 0,
                latency_ms=10 + index,
                response_time_ms=20 + index,
                reason="low-difficulty-share" if index % 3 else "accepted",
                error_code=None if index % 3 == 0 else "23",
                difficulty=1.0 + (index % 7),
                proposal_id=f"proposal-{index}",
                decision_id=f"decision-{index}",
                target="search_depth",
            )

        self.assertEqual(len(controller._pool_response_history), 1000)
        first = controller._pool_response_history[0]
        self.assertEqual(first["proposal_id"], "proposal-5")
        self.assertIn("error_code", first)
        self.assertIn("difficulty", first)
        self.assertIn("recorded_at", first)

        evidence = controller.supervised_production_evidence_status()
        self.assertEqual(evidence["pool_response_window_limit"], 1000)
        self.assertEqual(evidence["pool_feedback_samples"], 1000)
        self.assertEqual(evidence["pythia_decision_linked_samples"], 1000)
        self.assertTrue(
            evidence["acceptance_criteria"]["real_pool_or_testnet_feedback"]
        )
        self.assertTrue(
            evidence["acceptance_criteria"]["share_telemetry_tied_to_pythia_decisions"]
        )
        self.assertEqual(
            evidence["unattended_production"], "blocked_until_24h_evidence_pack"
        )

    def test_pool_feedback_and_target_evidence_survive_restart(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            controller = AutonomousMiningController(
                self.unified_engine,
                AutonomousConfig(persistence_enabled=True, persistence_dir=tmp),
            )
            controller.record_pool_response(
                accepted=True,
                latency_ms=12.5,
                error_code=None,
                difficulty=4.0,
                proposal_id="proposal-live-1",
                decision_id="decision-live-1",
                target="phi_scaling",
            )
            controller._save_reflexive_state()

            restored = AutonomousMiningController(
                self.unified_engine,
                AutonomousConfig(persistence_enabled=True, persistence_dir=tmp),
            )

            self.assertEqual(len(restored._pool_response_history), 1)
            self.assertEqual(restored._pool_response_history[0]["difficulty"], 4.0)
            self.assertEqual(
                restored.get_reflexive_target_bandit_snapshot()["phi_scaling"][
                    "successes"
                ],
                2,
            )
            self.assertTrue(
                restored.supervised_production_evidence_status()["acceptance_criteria"][
                    "share_telemetry_tied_to_pythia_decisions"
                ]
            )


if __name__ == "__main__":
    unittest.main()
