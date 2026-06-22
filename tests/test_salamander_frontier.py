from __future__ import annotations

from pythia_mining.salamander_frontier import (
    AdaptivePhiTuning,
    DistributedAgentCoherence,
    EvidenceBasedRegenerator,
    ImmutableEvidenceLog,
    SelfScalingWorkerPool,
)


def test_evidence_based_regeneration_replays_agent_state_without_checkpoint():
    audit_log = (
        ImmutableEvidenceLog()
        .append("agent_spawned", actor="agent-1", timestamp=1.0, job_id="job-a")
        .append("worker_spawned", actor="agent-1", timestamp=2.0, worker_id="w1")
        .append("search_started", actor="agent-1", timestamp=3.0, start_nonce=42)
        .append("share_found", actor="agent-1", timestamp=4.0, nonce=99)
        .append("share_submitted", actor="agent-1", timestamp=5.0, nonce=99)
        .append("share_accepted", actor="agent-1", timestamp=6.0, nonce=99)
    )

    recovered = EvidenceBasedRegenerator(audit_log).recover_agent("agent-1")

    assert recovered.current_job_id == "job-a"
    assert recovered.search_in_progress is True
    assert recovered.search_start_nonce == 42
    assert recovered.workers == 1
    assert recovered.shares_found == 1
    assert recovered.shares_submitted == 1
    assert recovered.shares_accepted == 1
    assert audit_log.seal() == ImmutableEvidenceLog(audit_log.entries()).seal()


def test_distributed_agent_coherence_emerges_from_shared_evidence():
    audit_log = ImmutableEvidenceLog()
    coherence = DistributedAgentCoherence(audit_log, total_target_hashrate=300.0)
    audit_log = coherence.add_agent("agent-1", "job-a", timestamp=1.0)
    coherence = DistributedAgentCoherence(audit_log, total_target_hashrate=300.0)
    audit_log = coherence.add_agent("agent-2", "job-a", timestamp=2.0)

    metrics = DistributedAgentCoherence(audit_log, total_target_hashrate=300.0).measure(
        "job-a", {"agent-1": 148.0, "agent-2": 152.0}
    )

    assert metrics.active_agents == 2
    assert metrics.agents_on_current_job == 2
    assert metrics.jobs_diverged == 0
    assert metrics.coherent is True
    assert metrics.max_hashrate_deviation < 0.02


def test_adaptive_phi_tuning_adopts_measured_improvement_only():
    tuner = AdaptivePhiTuning(improvement_threshold=0.01)
    experiments = tuner.run_experiments([1.0, 2.0, 3.0, 5.0], candidates=[1.2, 1.7])

    new_phi, adopted, best = tuner.adopt_best(baseline_ratio=0.1, experiments=experiments)

    assert adopted is True
    assert new_phi == best.phi_value
    assert tuner.phi_current == best.phi_value


def test_self_scaling_worker_count_stops_at_marginal_drop():
    scaler = SelfScalingWorkerPool(marginal_benefit_threshold=0.10)

    optimal = scaler.find_optimal_worker_count({1: 100.0, 2: 190.0, 3: 205.0, 4: 207.0})

    assert optimal == 2


def test_evidence_seal_lifecycle_detects_tampering_for_non_repudiation():
    from pythia_mining.salamander_frontier import EvidenceSealLifecycle

    lifecycle = EvidenceSealLifecycle(hmac_secret=b"frontier-secret")
    audit_log = ImmutableEvidenceLog().append(
        "adaptation_decision",
        actor="api-gateway",
        timestamp=1.0,
        domain="runtime",
        action="add_capacity",
    )
    seals = lifecycle.seal_log(audit_log)

    tampered = ImmutableEvidenceLog().append(
        "adaptation_decision",
        actor="api-gateway",
        timestamp=1.0,
        domain="runtime",
        action="do_nothing",
    )

    assert seals[0].hmac_signature is not None
    assert lifecycle.verify_log(audit_log, seals) is True
    assert lifecycle.verify_log(tampered, seals) is False


def test_ubiquitous_frontier_records_non_mining_adaptation_decisions():
    from pythia_mining.salamander_frontier import (
        CapabilityObservation,
        EvidenceSealLifecycle,
        UbiquitousSalamanderFrontier,
    )

    frontier = UbiquitousSalamanderFrontier(
        seal_lifecycle=EvidenceSealLifecycle(hmac_secret=b"frontier-secret"),
        adaptation_threshold=0.9,
    )
    observation = CapabilityObservation(
        domain="customer_api",
        capability="api-gateway",
        metric_name="p95_latency_ms",
        current_value=240.0,
        target_value=120.0,
        higher_is_better=False,
    )

    decision, seal = frontier.observe_decide_and_seal(observation, timestamp=1.0)

    assert decision is not None
    assert decision.action == "shed_or_rebalance_load"
    assert decision.domain == "customer_api"
    assert seal is not None
    assert seal.hmac_signature is not None
    assert [entry.event for entry in frontier.audit_log.entries()] == [
        "capability_observed",
        "adaptation_decision",
    ]


def test_default_portfolio_covers_funding_qaas_qiaas_ciaas_and_research():
    from pythia_mining.salamander_frontier import FrontierCapabilityPortfolio

    portfolio = FrontierCapabilityPortfolio.default()
    observations = portfolio.as_observations(
        {
            ("funding", "treasury-resilience"): 0.985,
            ("qaas", "quantum-job-orchestration"): 0.996,
            ("qiaas", "quantum-intelligence-routing"): 0.96,
            ("ciaas", "computational-intelligence-api"): 180.0,
            ("research", "math-proof-workbench"): 0.99,
        }
    )

    assert portfolio.domains() == ("ciaas", "funding", "qaas", "qiaas", "research")
    assert {observation.domain for observation in observations} == set(portfolio.domains())
    assert next(obs for obs in observations if obs.domain == "ciaas").higher_is_better is False


def test_distributed_evidence_replicator_merges_replica_logs_deterministically():
    from pythia_mining.salamander_frontier import DistributedEvidenceReplicator

    log_a = ImmutableEvidenceLog().append(
        "capability_observed", actor="qaas", timestamp=2.0, domain="qaas", metric=0.99
    )
    log_b = ImmutableEvidenceLog().append(
        "capability_observed", actor="ciaas", timestamp=1.0, domain="ciaas", metric=120.0
    )
    replicator = DistributedEvidenceReplicator()

    merged_ab = replicator.merge(log_a, log_b)
    merged_ba = replicator.merge(log_b, log_a)

    assert merged_ab.seal() == merged_ba.seal()
    assert [entry.actor for entry in merged_ab.entries()] == ["ciaas", "qaas"]
    assert replicator.verify_replicas(merged_ab, log_a, log_b) is True


def test_feedback_loop_validator_rejects_artifacts_without_matched_load_samples():
    from pythia_mining.salamander_frontier import ExperimentMeasurement, FeedbackLoopValidator

    validator = FeedbackLoopValidator(min_samples=2, min_relative_improvement=0.05)
    measurements = [
        ExperimentMeasurement("baseline", 100.0, "load-a", 1.0),
        ExperimentMeasurement("candidate", 130.0, "load-b", 2.0),
    ]

    result = validator.validate(
        measurements,
        baseline_strategy="baseline",
        candidate_strategy="candidate",
        load_signature="load-a",
    )

    assert result.accepted is False
    assert result.reason == "insufficient_matched_samples"


def test_feedback_loop_validator_accepts_matched_load_improvement_and_snapshot_exports():
    from pythia_mining.salamander_frontier import (
        EvidenceSealLifecycle,
        ExperimentMeasurement,
        FeedbackLoopValidator,
        SalamanderObservabilitySnapshot,
    )

    validator = FeedbackLoopValidator(min_samples=2, min_relative_improvement=0.05)
    measurements = [
        ExperimentMeasurement("baseline", 100.0, "same-load", 1.0),
        ExperimentMeasurement("baseline", 102.0, "same-load", 2.0),
        ExperimentMeasurement("candidate", 112.0, "same-load", 3.0),
        ExperimentMeasurement("candidate", 114.0, "same-load", 4.0),
    ]

    result = validator.validate(
        measurements,
        baseline_strategy="baseline",
        candidate_strategy="candidate",
        load_signature="same-load",
    )

    assert result.accepted is True
    assert result.relative_improvement > 0.05

    audit_log = ImmutableEvidenceLog().append(
        "adaptation_decision",
        actor="qiaas-router",
        timestamp=1.0,
        domain="qiaas",
        action="add_capacity",
    )
    snapshot = SalamanderObservabilitySnapshot(audit_log, EvidenceSealLifecycle()).to_dict()

    assert snapshot["evidence_events_total"] == 1
    assert snapshot["adaptation_events_total"] == 1
    assert snapshot["domains"] == ["qiaas"]
    assert snapshot["integrity"] == "sealed"


def test_cross_language_replay_manifest_round_trips_and_detects_digest_mismatch():
    from pythia_mining.salamander_frontier import CrossLanguageReplayManifest

    audit_log = ImmutableEvidenceLog().append(
        "capability_observed", actor="rust-agent", timestamp=1.0, domain="qaas", value=0.99
    )
    manifest = CrossLanguageReplayManifest(audit_log).to_manifest()

    replayed = CrossLanguageReplayManifest.from_manifest(manifest)
    tampered = dict(manifest)
    tampered["entries"] = [dict(manifest["entries"][0])]
    tampered["entries"][0]["data"] = {"domain": "qaas", "value": 0.1}

    assert replayed.seal() == audit_log.seal()
    assert manifest["schema_version"] == CrossLanguageReplayManifest.SCHEMA_VERSION
    try:
        CrossLanguageReplayManifest.from_manifest(tampered)
        assert False, "tampered manifest should not replay"
    except ValueError as exc:
        assert "digest mismatch" in str(exc)


def test_anticipatory_planner_grows_capacity_before_predicted_breach():
    from pythia_mining.salamander_frontier import (
        AnticipatoryAdaptationPlanner,
        CapabilityObservation,
        MetricTrendPoint,
    )

    observation = CapabilityObservation(
        domain="qaas",
        capability="quantum-job-orchestration",
        metric_name="job_success_rate",
        current_value=0.96,
        target_value=0.99,
        higher_is_better=True,
    )
    trend = [MetricTrendPoint(0.0, 0.98), MetricTrendPoint(60.0, 0.96)]

    plan = AnticipatoryAdaptationPlanner(minimum_lead_time_seconds=120.0).plan(
        observation, trend, now=60.0
    )

    assert plan is not None
    assert plan.action == "pre_grow_capacity"
    assert plan.lead_time_seconds is not None
    assert plan.lead_time_seconds > 120.0


def test_economic_autonomy_allocator_approves_only_risk_adjusted_roi():
    from pythia_mining.salamander_frontier import ComputeGrowthOption, EconomicAutonomyAllocator

    allocator = EconomicAutonomyAllocator(roi_threshold=0.20)
    decision = allocator.choose(
        [
            ComputeGrowthOption("small-node", expected_value=120.0, cost=100.0, risk_discount=0.05),
            ComputeGrowthOption(
                "burst-cluster", expected_value=180.0, cost=100.0, risk_discount=0.10
            ),
        ],
        available_budget=150.0,
    )
    rejected = allocator.choose(
        [ComputeGrowthOption("low-yield", expected_value=105.0, cost=100.0, risk_discount=0.0)],
        available_budget=150.0,
    )

    assert decision.approved is True
    assert decision.option_id == "burst-cluster"
    assert decision.budget_after == 50.0
    assert rejected.approved is False
    assert rejected.reason == "roi_below_threshold"


def test_immune_system_quarantines_non_physical_trait_claim_and_peer_audit():
    from pythia_mining.salamander_frontier import (
        EvidenceSealLifecycle,
        EvidenceTraitClaim,
        SalamanderImmuneSystem,
    )

    immune = SalamanderImmuneSystem(min_work_per_watt_hour=1.0, max_work_per_watt_hour=100.0)
    plausible = EvidenceTraitClaim(
        "node-a", work_units=200.0, energy_watts=100.0, duration_seconds=3600.0
    )
    impossible = EvidenceTraitClaim(
        "node-b", work_units=1_000_000.0, energy_watts=10.0, duration_seconds=1.0
    )
    audit_log = ImmutableEvidenceLog().append("capability_observed", actor="node-a", timestamp=1.0)
    lifecycle = EvidenceSealLifecycle(hmac_secret=b"immune")
    seals = lifecycle.seal_log(audit_log)

    assert immune.validate_trait(plausible).accepted is True
    rejected = immune.validate_trait(impossible)
    assert rejected.accepted is False
    assert rejected.reason == "non_physical_efficiency_claim"
    assert "node-b" in immune.quarantined_nodes
    assert immune.peer_audit("node-a", audit_log, seals, lifecycle).accepted is True
    assert immune.peer_audit("node-c", audit_log, [], lifecycle).quarantined is True


def test_morphogenetic_blueprint_library_remembers_success_templates():
    from pythia_mining.salamander_frontier import (
        AdaptationDecision,
        MorphogeneticBlueprintLibrary,
    )

    library = MorphogeneticBlueprintLibrary()
    decision = AdaptationDecision(
        domain="ciaas",
        capability="computational-intelligence-api",
        action="shed_or_rebalance_load",
        reason="p95_latency_ms_outside_frontier_threshold",
        severity="degraded",
        metric_name="p95_latency_ms",
        current_value=240.0,
        target_value=150.0,
    )

    blueprint = library.distill_from_decision(
        decision,
        parameters={"workers": 4, "phi": 1.61803398875, "latency_ms": 120.0},
        fitness_score=0.97,
        environment_signature="weekday-peak",
    )

    assert blueprint.blueprint_id.startswith("BLP-")
    assert library.best_for("ciaas", "computational-intelligence-api", "weekday-peak") == blueprint
    assert library.best_for("ciaas", "computational-intelligence-api", "weekend") is None


def test_metabolic_allocator_includes_power_cost_before_growth():
    from pythia_mining.salamander_frontier import (
        ComputeGrowthOption,
        MetabolicCostProfile,
        MetabolicEconomicAutonomyAllocator,
    )

    allocator = MetabolicEconomicAutonomyAllocator(roi_threshold=0.20)
    decision = allocator.choose_with_metabolism(
        [
            (
                ComputeGrowthOption("efficient-node", expected_value=200.0, cost=100.0),
                MetabolicCostProfile(watts=200.0, duration_hours=10.0, cost_per_kwh=0.10),
            ),
            (
                ComputeGrowthOption("wasteful-node", expected_value=200.0, cost=100.0),
                MetabolicCostProfile(watts=10_000.0, duration_hours=10.0, cost_per_kwh=0.50),
            ),
        ],
        available_budget=200.0,
    )

    assert decision.approved is True
    assert decision.option_id == "efficient-node"
    assert decision.budget_after < 100.0


def test_symbiotic_bridge_accepts_only_trusted_evidence_and_blastema_plan_points_to_seed():
    from pathlib import Path

    from pythia_mining.salamander_frontier import (
        BlastemaRehydrator,
        CrossLanguageReplayManifest,
        SymbioticEvidenceBridge,
        SymbioticNutrientOffer,
    )

    audit_log = ImmutableEvidenceLog().append(
        "adaptation_decision", actor="research", timestamp=1.0, domain="research"
    )
    evidence_hash = audit_log.seal()
    offer = SymbioticNutrientOffer("funding", "research", "compute_credits", 25.0, evidence_hash)
    bridge = SymbioticEvidenceBridge()

    accepted = bridge.evaluate_offer(offer, {evidence_hash}, "compute_credits", 10.0)
    rejected = bridge.evaluate_offer(offer, set(), "compute_credits", 10.0)
    manifest = CrossLanguageReplayManifest(audit_log).to_manifest()
    plan = BlastemaRehydrator().plan(manifest)

    assert accepted.accepted is True
    assert accepted.amount == 10.0
    assert rejected.accepted is False
    assert plan.runtime_hint == "rust"
    assert Path(plan.seed_path).exists()
    assert plan.command[0] == "rustc"


def test_nervous_system_selects_regeneration_affinity_from_latency_and_gravity():
    from pythia_mining.salamander_frontier import SalamanderNervousSystem, SynapticLatencyEdge

    nervous = SalamanderNervousSystem(
        [
            SynapticLatencyEdge("origin", "near-data", latency_ms=20.0, jitter_ms=2.0),
            SynapticLatencyEdge("origin", "near-treasury", latency_ms=35.0, jitter_ms=1.0),
            SynapticLatencyEdge("origin", "far-node", latency_ms=90.0, jitter_ms=5.0),
        ]
    )

    affinity = nervous.choose_regeneration_affinity(
        "origin",
        ["near-data", "near-treasury", "far-node"],
        data_gravity={"near-data": 15.0},
        treasury_gravity={"near-treasury": 40.0},
    )

    assert affinity is not None
    assert affinity.node_id == "near-treasury"
    assert affinity.reason == "lowest_latency_with_gravity_bonus"
    assert nervous.latency_map("origin")["near-data"] == 22.0


def test_recursive_gene_folder_evolves_thresholds_toward_best_fitness():
    from pythia_mining.salamander_frontier import (
        GeneExperimentOutcome,
        RecursiveGeneFolder,
        SalamanderGene,
    )

    genes = {
        "marginal_benefit_threshold": SalamanderGene(
            "marginal_benefit_threshold", value=0.02, min_value=0.005, max_value=0.10
        ),
        "immune_error_rate": SalamanderGene(
            "immune_error_rate", value=0.05, min_value=0.01, max_value=0.20
        ),
    }
    outcomes = [
        GeneExperimentOutcome("marginal_benefit_threshold", tested_value=0.015, fitness_score=0.9),
        GeneExperimentOutcome("marginal_benefit_threshold", tested_value=0.03, fitness_score=0.5),
        GeneExperimentOutcome("immune_error_rate", tested_value=0.08, fitness_score=0.8),
    ]

    evolved = RecursiveGeneFolder(learning_rate=0.5).evolve(genes, outcomes)

    assert evolved["marginal_benefit_threshold"].value == 0.0175
    assert evolved["immune_error_rate"].value == 0.065


def test_global_evidence_ledger_shares_trusted_blueprints_only():
    from pythia_mining.salamander_frontier import (
        AdaptationDecision,
        GlobalEvidenceLedger,
        MorphogeneticBlueprintLibrary,
    )

    decision = AdaptationDecision(
        domain="qaas",
        capability="quantum-job-orchestration",
        action="pre_grow_capacity",
        reason="trend_predicts_future_threshold_breach",
        severity="degraded",
        metric_name="job_success_rate",
        current_value=0.96,
        target_value=0.99,
    )
    library = MorphogeneticBlueprintLibrary()
    blueprint = library.distill_from_decision(
        decision,
        parameters={"region": "tokyo", "workers": 8},
        fitness_score=0.99,
        environment_signature="asia-peak",
    )
    audit_log = ImmutableEvidenceLog().append(
        "blueprint_published", actor="tokyo-agent", timestamp=1.0, domain="qaas"
    )
    ledger = GlobalEvidenceLedger()
    record = ledger.publish_blueprint(
        blueprint, origin_node="tokyo-agent", audit_log=audit_log, published_at=1.0
    )

    inherited = ledger.inherit_blueprints(
        trusted_hashes={record.evidence_hash},
        domain="qaas",
        capability="quantum-job-orchestration",
    )
    blocked = ledger.inherit_blueprints(
        trusted_hashes=set(),
        domain="qaas",
        capability="quantum-job-orchestration",
    )

    assert inherited == (blueprint,)
    assert blocked == ()


def test_apoptosis_exports_evidence_manifest_before_pruning_unfit_agent():
    from pythia_mining.salamander_frontier import AgentViabilityMetrics, SalamanderApoptosis

    evidence_log = ImmutableEvidenceLog().append(
        "capability_observed", actor="unfit-node", timestamp=1.0, domain="ciaas", roi=-0.1
    )
    metrics = AgentViabilityMetrics(
        agent_id="unfit-node",
        roi=-0.1,
        metabolic_cost=0.05,
        consecutive_underperforming_windows=4,
        evidence_log=evidence_log,
    )

    decision = SalamanderApoptosis(
        species_roi_ratio_threshold=0.70, minimum_underperforming_windows=3
    ).check_viability(metrics, species_average_roi=1.0)

    assert decision.should_prune is True
    assert decision.reason == "export_evidence_then_graceful_shutdown"
    assert decision.evidence_hash == evidence_log.seal()
    assert decision.final_manifest is not None
    assert decision.final_manifest["entry_count"] == 1


def test_apoptosis_keeps_temporarily_slow_but_viable_agent():
    from pythia_mining.salamander_frontier import AgentViabilityMetrics, SalamanderApoptosis

    evidence_log = ImmutableEvidenceLog().append(
        "capability_observed", actor="slow-node", timestamp=1.0
    )
    metrics = AgentViabilityMetrics(
        agent_id="slow-node",
        roi=0.65,
        metabolic_cost=0.05,
        consecutive_underperforming_windows=1,
        evidence_log=evidence_log,
    )

    decision = SalamanderApoptosis().check_viability(metrics, species_average_roi=1.0)

    assert decision.should_prune is False
    assert decision.final_manifest is None


def test_resonant_substrate_tuner_selects_low_jitter_low_heat_harmonic():
    from pythia_mining.salamander_frontier import PHI, ResonanceMeasurement, ResonantSubstrateTuner

    tuner = ResonantSubstrateTuner(jitter_weight=2.0, thermal_weight=3.0, throughput_weight=1.0)
    candidates = tuner.candidate_phi_values(center_phi=PHI, epsilon=0.001)
    measurements = [
        ResonanceMeasurement(
            candidates[0], execution_jitter_ms=5.0, thermal_drift_c=3.0, throughput=120.0
        ),
        ResonanceMeasurement(
            candidates[1], execution_jitter_ms=1.0, thermal_drift_c=0.5, throughput=118.0
        ),
        ResonanceMeasurement(
            candidates[2], execution_jitter_ms=2.0, thermal_drift_c=2.0, throughput=121.0
        ),
    ]

    lock = tuner.find_harmonic_phi(measurements)

    assert lock.phi_value == candidates[1]
    assert lock.reason == "max_throughput_min_jitter_min_thermal_drift"
