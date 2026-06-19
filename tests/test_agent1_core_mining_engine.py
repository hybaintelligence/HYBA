"""Agent 1 coverage for core mining engine and production orchestrator behavior.

These tests keep all network/mining surfaces mocked or local-only. They exercise
state transitions, strategy selection, failover accounting, and configuration
validation without claiming live pool acceptance or runtime performance.
"""

from __future__ import annotations

import asyncio
import importlib
import sys
import types
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest


@dataclass
class DummyOptimizationResult:
    nonce: int = 7
    hash_value: str = "00abc"
    strategy_used: str = "dummy_strategy"
    success: bool = True


@dataclass
class DummySearchStrategy:
    phi_resonance_enabled: bool
    adaptive_difficulty: bool
    max_search_time: float


class DummySolver:
    def __init__(self, configured_capacity_ehs: float | None = None) -> None:
        self.configured_capacity_ehs = configured_capacity_ehs
        self.metrics = {
            "phi_compression_factor": 2.5,
            "available": True,
            "von_neumann_entropy": 0.25,
            "phi_phase_alignment": 0.75,
            "compressed_working_set_size": 32,
            "working_set_compression_ratio": 2.5,
        }

    def get_metrics(self) -> dict[str, Any]:
        return dict(self.metrics)


class DummyOptimizer:
    def __init__(
        self, quantum_solver: Any, consciousness_engine: Any, blockchain_oracle: Any
    ) -> None:
        self.quantum_solver = quantum_solver
        self.consciousness_engine = consciousness_engine
        self.blockchain_oracle = blockchain_oracle
        self.current_strategy = DummySearchStrategy(True, True, 60.0)
        self.accepted: list[dict[str, Any]] = []
        self.rejected: list[dict[str, Any]] = []
        self.result = DummyOptimizationResult(strategy_used="dummy_strategy")

    async def optimize_nonce_search(self, job: Any) -> DummyOptimizationResult:
        self.last_job = job
        return self.result

    async def on_share_accepted(self, share_info: dict[str, Any]) -> None:
        self.accepted.append(share_info)

    async def on_share_rejected(
        self, share_info: dict[str, Any], error_code: int, error_msg: str
    ) -> None:
        self.rejected.append({"share": share_info, "code": error_code, "message": error_msg})

    def meta_learning_snapshot(self) -> dict[str, Any]:
        return {"accepted": len(self.accepted), "rejected": len(self.rejected)}


@dataclass
class DummyPhiMetrics:
    phi_integrated: float
    phi_causal: float
    complexity: float
    source: str


class DummyRegime:
    value = "singular"


class DummyState:
    integrated_information: float | None = 0.8
    component_integration: float | None = 0.6
    system_complexity: float | None = 0.5
    source: str | None = "test"


class DummyConsciousnessEngine:
    def __init__(self, config: Any = None) -> None:
        self.config = config
        self.current_state = DummyState()
        self._integration_regime = DummyRegime()
        self.needs_healing = False
        self.health_updates: list[tuple[str, bool]] = []

    def update_component_health(self, component: str, healthy: bool) -> None:
        self.health_updates.append((component, healthy))
        if self.current_state.integrated_information is None:
            self.current_state.integrated_information = 0.35
            self.current_state.component_integration = 0.25
            self.current_state.system_complexity = 0.2

    def get_metrics(self) -> dict[str, Any]:
        return {
            "coherence_meter": self.current_state.integrated_information,
            "integration_regime": self._integration_regime.value,
            "active_components": [name for name, ok in self.health_updates if ok],
            "autonomic_events": [],
            "source": self.current_state.source,
        }


@dataclass
class DummyConsciousnessConfig:
    phi_singular_threshold: float = 0.7
    phi_distributed_threshold: float = 0.4
    phi_critical_threshold: float = 0.2
    measurement_window: int = 100
    heal_trigger_threshold: float = 0.3


class DummyVerifier:
    def __init__(self, configured_capacity_ehs: float | None = None) -> None:
        self.configured_capacity_ehs = configured_capacity_ehs
        self.batch_result = types.SimpleNamespace(
            backend="cpu",
            metal_available=False,
            total_nonces=3,
            hashes_per_second=1200.0,
            hashrate_ehs=1.2e-15,
        )
        self.candidate_result = types.SimpleNamespace(
            backend="cpu", valid=True, block_hash="00feed"
        )

    def status(self) -> dict[str, Any]:
        return {"selected_backend": "cpu", "metal": {"available": False}}

    def initialize_metal(self) -> dict[str, Any]:
        return {"selected_backend": "cpu", "metal": {"available": False}}

    def verify_batch(self, job: Any, nonces: list[int], extranonce2: str | None = None) -> Any:
        self.batch_result.total_nonces = len(nonces)
        return self.batch_result

    def submit_candidate(self, job: Any, nonce: int, extranonce2: str | None = None) -> Any:
        return self.candidate_result


class DummyAutonomyLevel:
    def __init__(self, value: str = "supervised", should_optimize: bool = True) -> None:
        self.value = value
        self.should_optimize = should_optimize


class DummyAutonomousController:
    def __init__(self, unified_engine: Any) -> None:
        self.unified_engine = unified_engine
        self.current_autonomy_level = DummyAutonomyLevel()
        self.config = types.SimpleNamespace(
            reflexive_loop_interval=999999.0, reflexive_loop_enabled=True
        )
        self._last_reflexive_cycle = 0.0
        self.fail_next = False
        self.failures = 0
        self.successes = 0
        self.level_set = None

    def is_circuit_open(self) -> bool:
        return self.failures >= 2

    async def optimize_search_strategy(self, **kwargs: Any) -> Any:
        if self.fail_next:
            raise RuntimeError("optimizer unavailable")
        self.last_search_kwargs = kwargs
        return types.SimpleNamespace(
            decision_id="d1",
            action_taken="tune",
            expected_outcome="stable",
            actual_outcome=None,
            operator_override=False,
            autonomy_level=self.current_autonomy_level,
        )

    async def optimize_hashrate_target(self, **kwargs: Any) -> Any:
        self.last_hashrate_kwargs = kwargs
        return types.SimpleNamespace(
            decision_id="d2",
            action_taken="cap",
            expected_outcome="bounded",
            actual_outcome="bounded",
            operator_override=False,
            autonomy_level=self.current_autonomy_level,
        )

    async def seek_improvement(self) -> None:
        self.sought = True

    def record_autonomy_success(self) -> None:
        self.successes += 1

    def record_autonomy_failure(self, reason: str) -> DummyAutonomyLevel:
        self.failures += 1
        return DummyAutonomyLevel("manual", False)

    def record_circuit_success(self) -> None:
        self.circuit_success = True

    def set_autonomy_level(self, level: Any) -> None:
        self.level_set = level
        self.current_autonomy_level = level

    def reset_circuit_breaker(self, operator_reason: str) -> None:
        self.reset_reason = operator_reason
        self.failures = 0

    def get_autonomy_status(self) -> dict[str, Any]:
        return {"level": self.current_autonomy_level.value, "failures": self.failures}

    def get_decision_history(self, limit: int | None = None) -> list[Any]:
        constraint = types.SimpleNamespace(value="operator_review")
        return [
            types.SimpleNamespace(
                decision_id="d1",
                timestamp=1.0,
                autonomy_level=self.current_autonomy_level,
                decision_type="search",
                action_taken="tune",
                expected_outcome="stable",
                actual_outcome=None,
                operator_override=False,
                constraints_satisfied=[constraint],
                constraints_violated=[],
            )
        ]


@pytest.fixture()
def engine_module(monkeypatch: pytest.MonkeyPatch):
    """Import the unified engine with deterministic local dependency doubles."""
    stubs: dict[str, types.ModuleType] = {}

    def module(name: str) -> types.ModuleType:
        mod = types.ModuleType(name)
        stubs[name] = mod
        monkeypatch.setitem(sys.modules, name, mod)
        return mod

    ai = module("pythia_mining.ai_optimizer")
    ai.AIOptimizer = DummyOptimizer
    ai.OptimizationResult = DummyOptimizationResult
    ai.SearchStrategy = DummySearchStrategy

    consciousness = module("pythia_mining.consciousness_engine")
    consciousness.ConsciousnessConfig = DummyConsciousnessConfig
    consciousness.ConsciousnessEngine = DummyConsciousnessEngine
    consciousness.PhiMetrics = DummyPhiMetrics

    golden = module("pythia_mining.golden_ratio_library")
    golden.PHI = 1.61803398875

    hendrix = module("pythia_mining.hendrix_phi_solver")
    hendrix.M32 = tuple(range(32))
    hendrix.YANG_MILLS_GAP = 1.0
    for name in [
        "cheap_phi_resonance",
        "embed_nonce",
        "phi_gradient_proposal",
        "phi_resonance",
        "soft_mass_gap_gate",
        "voronoi_domain",
        "yang_mills_action",
    ]:
        setattr(hendrix, name, lambda *args, **kwargs: 0)

    metal = module("pythia_mining.metal_sha256_pipeline")
    metal.BatchResult = object
    metal.NonceVerification = object
    metal.UnifiedBatchVerifier = DummyVerifier

    scaling = module("pythia_mining.phi_scaling_engine")
    scaling.PhiScaledEnsemble = lambda config: types.SimpleNamespace(config=config)
    scaling.PhiResonanceAnalyzer = lambda: types.SimpleNamespace(
        analyze_phi_resonance=lambda payload: {
            "count": len(payload["nonces"]),
            "nonces": payload["nonces"],
        }
    )
    scaling.benchmark_vs_asic = (
        lambda measured_hashes_per_second=None, asic_baseline_hashes_per_second=110e12: {
            "measured_hashes_per_second": measured_hashes_per_second,
            "asic_baseline_hashes_per_second": asic_baseline_hashes_per_second,
        }
    )

    compressed = module("pythia_mining.pulvini_compressed_solver")
    compressed.PulviniCompressedQuantumSolver = DummySolver

    proof = module("pythia_mining.pulvini_memory_compression_proof")
    proof.phi_folding_mathematical_proof = lambda: {"invertible": True}

    stratum = module("pythia_mining.stratum_client")
    stratum.MiningJob = object

    auto = module("pythia_mining.autonomous_mining_controller")
    auto.AutonomousMiningController = DummyAutonomousController
    auto.AutonomyLevel = DummyAutonomyLevel
    auto.AutonomousDecision = object

    sys.modules.pop("pythia_mining.phi_unified_mining_engine", None)
    return importlib.import_module("pythia_mining.phi_unified_mining_engine")


@pytest.fixture()
def engine(engine_module: types.ModuleType):
    return engine_module.UnifiedMiningEngine(configured_capacity_ehs=0.5)


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def test_unified_mining_engine_initialization_default_config(
    engine_module: types.ModuleType,
) -> None:
    engine = engine_module.UnifiedMiningEngine()
    assert engine.configured_capacity_ehs is None
    assert engine.state.verifier_backend == "cpu"
    assert engine.state.verifier_initialized is True


def test_unified_mining_engine_initialization_with_custom_capacity(engine: Any) -> None:
    assert engine.configured_capacity_ehs == 0.5
    assert engine.solver.configured_capacity_ehs == 0.5
    assert engine.verifier.configured_capacity_ehs == 0.5


def test_engine_lifecycle_startup_shutdown_records_backend(engine: Any) -> None:
    assert engine.initialize_metal()["selected_backend"] == "cpu"
    assert engine.get_unified_state()["state"]["verifier_backend"] == "cpu"


def test_strategy_selection_based_on_high_coherence(engine: Any) -> None:
    run(engine.search(job={"job_id": "high"}))
    assert engine.optimizer.current_strategy.max_search_time == 30.0
    assert engine.optimizer.current_strategy.adaptive_difficulty is True


@pytest.mark.parametrize(
    ("coherence", "expected_time", "adaptive"),
    [(0.55, 60.0, True), (0.1, 120.0, False)],
)
def test_strategy_selection_thresholds(
    engine: Any, coherence: float, expected_time: float, adaptive: bool
) -> None:
    engine.consciousness.current_state.integrated_information = coherence
    run(engine.search(job={"job_id": str(coherence)}))
    assert engine.optimizer.current_strategy.max_search_time == expected_time
    assert engine.optimizer.current_strategy.adaptive_difficulty is adaptive


def test_search_updates_state_metrics(engine: Any) -> None:
    result = run(engine.search(job={"job_id": "state"}))
    assert result.strategy_used == "dummy_strategy"
    assert engine.state.phi_coherence == 0.8
    assert engine.state.m32_domains_covered == 32
    assert engine.state.working_set_compression == 2.5
    assert engine.get_unified_state()["state"]["solve_count"] == 1


def test_autonomic_event_when_healing_needed(engine: Any) -> None:
    engine.consciousness.needs_healing = True
    run(engine.search(job={"job_id": "heal"}))
    assert engine.state.autonomic_event["action"] == "reduced_search_aggressiveness"


def test_autonomous_failure_opens_degraded_path_without_blocking_search(engine: Any) -> None:
    engine.autonomous_controller.fail_next = True
    result = run(engine.search(job={"job_id": "failure"}))
    assert result.success is True
    assert engine.autonomous_controller.failures == 1


def test_coherence_for_next_search_initializes_missing_measurement(engine: Any) -> None:
    engine.consciousness.current_state.integrated_information = None
    metrics = engine._coherence_for_next_search()
    assert metrics.phi_integrated == 0.35
    assert ("quantum_solver", True) in engine.consciousness.health_updates


def test_verify_batch_records_hashrate_and_batch_size(engine: Any) -> None:
    result = engine.verify_batch(job=object(), nonces=[1, 2, 3, 4])
    assert result.total_nonces == 4
    assert engine.state.last_batch_size == 4
    assert engine.state.last_batch_hashrate_hps == 1200.0


def test_submit_candidate_records_candidate_validity(engine: Any) -> None:
    result = engine.submit_candidate(job=object(), nonce=42)
    assert result.valid is True
    assert engine.state.last_candidate_valid is True
    assert engine.state.last_candidate_hash == "00feed"


def test_share_acceptance_ratio_tracking_counts_accepted_and_rejected(engine: Any) -> None:
    run(engine.on_share_result({"share": "a"}, accepted=True))
    run(engine.on_share_result({"share": "b", "error_code": 21}, accepted=False))
    state = engine.get_unified_state()["state"]
    assert state["accepted_shares"] == 1
    assert state["rejected_shares"] == 1
    assert state["meta_learning_event"] == {"accepted": 1, "rejected": 1}


def test_analyze_nonce_resonance_uses_float_nonce_payload(engine: Any) -> None:
    assert engine.analyze_nonce_resonance([1, 2, 3]) == {"count": 3, "nonces": [1.0, 2.0, 3.0]}


def test_benchmark_passes_measured_and_baseline_values(engine: Any) -> None:
    assert engine.benchmark(100.0, asic_baseline=200.0) == {
        "measured_hashes_per_second": 100.0,
        "asic_baseline_hashes_per_second": 200.0,
    }


def test_autonomous_control_methods_delegate_to_controller(engine: Any) -> None:
    search_decision = run(engine.autonomous_optimize_search())
    hash_decision = run(engine.autonomous_optimize_hashrate(target_hashrate_ehs=2.0))
    assert search_decision["decision_id"] == "d1"
    assert hash_decision["action_taken"] == "cap"
    assert engine.autonomous_controller.last_hashrate_kwargs["target_hashrate_ehs"] == 2.0


def test_autonomy_status_level_and_decision_history(engine: Any) -> None:
    new_level = DummyAutonomyLevel("manual", False)
    engine.set_autonomy_level(new_level)
    assert engine.get_autonomy_status()["level"] == "manual"
    assert engine.get_autonomous_decision_history()[0]["constraints_satisfied"] == [
        "operator_review"
    ]
    engine.reset_autonomy_circuit_breaker("review complete")
    assert engine.autonomous_controller.reset_reason == "review complete"


def test_phi_config_validation_bounds_checking() -> None:
    from pythia_mining.phi_config import PhiCompressionPolicy, PhiScalingPolicy

    assert PhiScalingPolicy(memory_limit=0).memory_limit == 0
    with pytest.raises(ValueError, match="high_variance_threshold"):
        PhiScalingPolicy(low_variance_threshold=0.5, high_variance_threshold=0.4)
    with pytest.raises(ValueError, match="fold_depth"):
        PhiCompressionPolicy(fold_depth=0)
    with pytest.raises(ValueError, match="sparse_skip_threshold"):
        PhiCompressionPolicy(sparse_skip_threshold=1.1)


def test_phi_config_loading_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    from pythia_mining import phi_config

    monkeypatch.setenv("HYBA_ALLOW_DEV_FIXTURES", "true")
    monkeypatch.delenv("HYBA_ENV", raising=False)
    monkeypatch.delenv("HYBA_ENABLE_LIVE_STRATUM", raising=False)
    assert phi_config.initialize_production_secrets() == {"status": "DEV_PASS"}


def test_environment_variable_precedence_blocks_dev_fixtures_in_live_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pythia_mining import phi_config

    monkeypatch.setenv("HYBA_ALLOW_DEV_FIXTURES", "true")
    monkeypatch.setenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", "1")
    with pytest.raises(SystemExit):
        phi_config.initialize_production_secrets()


def test_production_secret_gate_accepts_secure_values(monkeypatch: pytest.MonkeyPatch) -> None:
    from pythia_mining import phi_config

    monkeypatch.delenv("HYBA_ALLOW_DEV_FIXTURES", raising=False)
    monkeypatch.setenv("JWT_SECRET", "x" * 16)
    monkeypatch.setenv("HYBA_OPERATOR_CREDENTIALS", "operator" * 3)
    monkeypatch.setenv("POOL_PRIMARY_CREDENTIALS", "pool" * 5)
    assert phi_config.initialize_production_secrets() == {"status": "SEC_SECURE"}


@pytest.fixture()
def orchestrator_module(monkeypatch: pytest.MonkeyPatch):
    audit = types.ModuleType("pythia_mining.audit_logger")
    audit.AuditEvent = object
    audit.AuditEventType = object
    audit.get_audit_logger = lambda: types.SimpleNamespace(
        log_pool_initialized=Mock(), log_pool_health_change=Mock()
    )
    monkeypatch.setitem(sys.modules, "pythia_mining.audit_logger", audit)

    metrics = types.ModuleType("pythia_mining.metrics_store")
    metrics.PoolMetrics = object
    metrics.get_metrics_store = lambda: types.SimpleNamespace()
    monkeypatch.setitem(sys.modules, "pythia_mining.metrics_store", metrics)

    stratum = types.ModuleType("pythia_mining.stratum_client")

    class AllPoolsOfflineError(Exception):
        pass

    @dataclass
    class ShareResult:
        accepted: bool
        response: Any = None
        error: str | None = None

    class StratumClient:
        pass

    stratum.AllPoolsOfflineError = AllPoolsOfflineError
    stratum.StratumClient = StratumClient
    stratum.ShareResult = ShareResult
    monkeypatch.setitem(sys.modules, "pythia_mining.stratum_client", stratum)

    profiles = types.ModuleType("pythia_mining.pool_profiles")

    @dataclass
    class PoolProfile:
        pool_id: str
        name: str
        url: str
        username: str = "user"
        password: str = "pass"
        stratum_version: str = "v1"

    profiles.PoolProfile = PoolProfile
    monkeypatch.setitem(sys.modules, "pythia_mining.pool_profiles", profiles)

    sys.modules.pop("pythia_mining.production_mining_orchestrator", None)
    return importlib.import_module("pythia_mining.production_mining_orchestrator")


@pytest.fixture()
def profile(orchestrator_module: types.ModuleType):
    return orchestrator_module.PoolProfile(pool_id="p1", name="Primary", url="stratum+tcp://pool")


def test_orchestrator_requires_at_least_one_pool(orchestrator_module: types.ModuleType) -> None:
    with pytest.raises(ValueError, match="At least one pool"):
        orchestrator_module.ProductionMiningOrchestrator([])


def test_orchestrator_initializes_pool_health(
    profile: Any, orchestrator_module: types.ModuleType
) -> None:
    orchestrator = orchestrator_module.ProductionMiningOrchestrator([profile])
    status = orchestrator.get_pool_health_status("p1")["p1"]
    assert status["pool_name"] == "Primary"
    assert status["health"] == "unknown"


def test_pool_health_updates_reset_consecutive_failures(
    profile: Any, orchestrator_module: types.ModuleType
) -> None:
    orchestrator = orchestrator_module.ProductionMiningOrchestrator([profile])
    orchestrator.pool_health["p1"].consecutive_failures = 4
    orchestrator._update_pool_health("p1", orchestrator_module.PoolHealth.HEALTHY)
    assert orchestrator.pool_health["p1"].consecutive_failures == 0
    assert orchestrator.pool_health["p1"].health is orchestrator_module.PoolHealth.HEALTHY


def test_pool_failure_thresholds_progress_to_degraded(
    profile: Any, orchestrator_module: types.ModuleType
) -> None:
    orchestrator = orchestrator_module.ProductionMiningOrchestrator(
        [profile], max_pool_failures_before_degraded=2, max_pool_failures_before_offline=3
    )
    orchestrator._record_pool_failure("p1", "timeout")
    assert orchestrator.pool_health["p1"].health is orchestrator_module.PoolHealth.UNHEALTHY
    orchestrator._record_pool_failure("p1", "timeout")
    assert orchestrator.pool_health["p1"].health is orchestrator_module.PoolHealth.DEGRADED
    assert orchestrator.pool_health["p1"].consecutive_failures == 0


def test_pool_failure_can_mark_offline_without_degraded_reset(
    profile: Any, orchestrator_module: types.ModuleType
) -> None:
    orchestrator = orchestrator_module.ProductionMiningOrchestrator(
        [profile], max_pool_failures_before_degraded=5, max_pool_failures_before_offline=2
    )
    orchestrator._record_pool_failure("p1", "timeout")
    orchestrator._record_pool_failure("p1", "timeout")
    assert orchestrator.pool_health["p1"].health is orchestrator_module.PoolHealth.OFFLINE


def test_orchestrator_job_dispatch_uses_priority_order(
    profile: Any, orchestrator_module: types.ModuleType
) -> None:
    second = orchestrator_module.PoolProfile(
        pool_id="p2", name="Secondary", url="stratum+tcp://pool2"
    )
    orchestrator = orchestrator_module.ProductionMiningOrchestrator([profile, second])
    orchestrator._update_pool_health("p1", orchestrator_module.PoolHealth.OFFLINE)
    orchestrator._update_pool_health("p2", orchestrator_module.PoolHealth.HEALTHY)
    assert orchestrator._get_healthy_pools() == ["p2"]


def test_share_collection_records_acceptance_and_rejection(
    profile: Any, orchestrator_module: types.ModuleType
) -> None:
    orchestrator = orchestrator_module.ProductionMiningOrchestrator([profile])
    orchestrator._record_share_result("p1", orchestrator_module.ShareResult(accepted=True))
    orchestrator._record_share_result("p1", orchestrator_module.ShareResult(accepted=False))
    status = orchestrator.pool_health["p1"]
    assert status.shares_submitted_total == 2
    assert status.shares_accepted_total == 1
    assert status.shares_rejected_total == 1


def test_hashrate_acceptance_ratio_tracking_in_mining_stats(
    profile: Any, orchestrator_module: types.ModuleType
) -> None:
    orchestrator = orchestrator_module.ProductionMiningOrchestrator([profile])
    orchestrator.total_connection_attempts = 4
    orchestrator.successful_connections = 3
    orchestrator._record_share_result("p1", orchestrator_module.ShareResult(accepted=True))
    orchestrator._record_share_result("p1", orchestrator_module.ShareResult(accepted=False))
    stats = orchestrator.get_mining_stats()
    assert stats.global_acceptance_rate == 0.5
    assert stats.connection_success_rate == 0.75
    assert stats.healthy_pools == 1


def test_orchestrator_failover_skips_rejected_first_pool(
    profile: Any, orchestrator_module: types.ModuleType
) -> None:
    second = orchestrator_module.PoolProfile(
        pool_id="p2", name="Secondary", url="stratum+tcp://pool2"
    )
    orchestrator = orchestrator_module.ProductionMiningOrchestrator([profile, second])
    orchestrator._update_pool_health("p1", orchestrator_module.PoolHealth.HEALTHY)
    orchestrator._update_pool_health("p2", orchestrator_module.PoolHealth.HEALTHY)
    orchestrator.clients = {
        "p1": types.SimpleNamespace(
            submit_validated_share=AsyncMock(return_value=orchestrator_module.ShareResult(False))
        ),
        "p2": types.SimpleNamespace(
            submit_validated_share=AsyncMock(return_value=orchestrator_module.ShareResult(True))
        ),
    }
    result = run(orchestrator._submit_failover(job=object(), nonce=1))
    assert result.accepted is True
    assert orchestrator.pool_health["p1"].shares_rejected_total == 1
    assert orchestrator.pool_health["p2"].shares_accepted_total == 1


def test_multi_pool_submission_collects_only_share_results(
    profile: Any, orchestrator_module: types.ModuleType
) -> None:
    second = orchestrator_module.PoolProfile(
        pool_id="p2", name="Secondary", url="stratum+tcp://pool2"
    )
    orchestrator = orchestrator_module.ProductionMiningOrchestrator(
        [profile, second], mining_strategy=orchestrator_module.MiningStrategy.MULTI_POOL
    )
    orchestrator._update_pool_health("p1", orchestrator_module.PoolHealth.HEALTHY)
    orchestrator._update_pool_health("p2", orchestrator_module.PoolHealth.HEALTHY)
    orchestrator.clients = {
        "p1": types.SimpleNamespace(
            submit_validated_share=AsyncMock(return_value=orchestrator_module.ShareResult(True))
        ),
        "p2": types.SimpleNamespace(
            submit_validated_share=AsyncMock(side_effect=RuntimeError("down"))
        ),
    }
    results = run(orchestrator.submit_share(job=object(), nonce=99))
    assert [r.accepted for r in results] == [True]
    assert orchestrator.pool_health["p2"].connection_failures == 1


def test_get_next_job_updates_job_metadata(
    profile: Any, orchestrator_module: types.ModuleType
) -> None:
    orchestrator = orchestrator_module.ProductionMiningOrchestrator([profile])
    orchestrator._update_pool_health("p1", orchestrator_module.PoolHealth.HEALTHY)
    orchestrator.clients = {
        "p1": types.SimpleNamespace(
            poll_live_event=AsyncMock(return_value={"job_id": "j1"}),
            current_jobs={"j1": object(), "j2": object()},
        )
    }
    assert run(orchestrator.get_next_job()) == {"job_id": "j1"}
    assert orchestrator.pool_health["p1"].active_jobs == 2


def test_start_stop_manage_background_tasks(
    profile: Any, orchestrator_module: types.ModuleType
) -> None:
    async def scenario() -> bool:
        orchestrator = orchestrator_module.ProductionMiningOrchestrator(
            [profile], health_check_interval=60.0
        )
        orchestrator.clients = {"p1": types.SimpleNamespace(disconnect=AsyncMock())}
        await orchestrator.start()
        assert orchestrator._running is True
        await orchestrator.stop()
        assert orchestrator._running is False
        orchestrator.clients["p1"].disconnect.assert_awaited_once()
        return True

    assert run(scenario()) is True
