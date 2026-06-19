from pythia_mining.pythia_matched_mining_benchmark import (
    MAX_HASH,
    ReplayBlockTemplate,
    TraversalStrategy,
    baseline_nonce_order,
    build_guidance_from_structure,
    pythia_structured_nonce_order,
    run_matched_mining_benchmark,
    synthetic_header_prefix,
    target_from_best_nonce,
    verify_candidate,
)


def _guidance():
    return build_guidance_from_structure(
        block_height=840_321,
        difficulty=88_000_000_000_000.0,
        target_hex="00000000000000000002b0000000000000000000000000000000000000000000",
        dodecahedral_domain_score=0.97,
        icosahedral_face_score=0.94,
        mass_gap_valley_score=0.86,
        entanglement_spectrum_score=0.84,
        sector_coverage=0.91,
        golden_angle_alignment=0.72,
        phi15_rate=0.23,
    )


def test_pythia_order_is_deterministic_duplicate_free_and_not_baseline():
    guidance = _guidance()
    first = pythia_structured_nonce_order(guidance, 128, start_nonce=0)
    second = pythia_structured_nonce_order(guidance, 128, start_nonce=0)

    assert first == second
    assert len(first) == 128
    assert len(set(first)) == 128
    assert first != baseline_nonce_order(128, start_nonce=0)


def test_exact_sha256d_candidate_verification_is_used():
    prefix = synthetic_header_prefix("exact-sha256d-test")
    template = ReplayBlockTemplate(
        header_prefix_hex=prefix,
        target=MAX_HASH,
        block_height=1,
        difficulty=1.0,
    )

    result = verify_candidate(template, 42)

    assert result.nonce == 42
    assert result.accepted is True
    assert len(result.hash_hex) == 64
    assert result.hash_int <= MAX_HASH


def test_matched_report_preserves_claim_boundaries_and_hashes_stably():
    guidance = _guidance()
    prefix = synthetic_header_prefix("matched-report-stability")
    target, _, _ = target_from_best_nonce(
        template_prefix_hex=prefix,
        nonces=baseline_nonce_order(64, start_nonce=0),
        block_height=840_321,
        difficulty=88_000_000_000_000.0,
    )
    template = ReplayBlockTemplate(
        header_prefix_hex=prefix,
        target=target,
        block_height=840_321,
        difficulty=88_000_000_000_000.0,
        template_id="stable_replay",
    )

    first = run_matched_mining_benchmark(
        template=template,
        guidance=guidance,
        candidate_budget=64,
    )
    second = run_matched_mining_benchmark(
        template=template,
        guidance=guidance,
        candidate_budget=64,
    )

    assert first.report_hash == second.report_hash
    assert first.protocol == "PYTHIA_MATCHED_MINING_BENCHMARK_V1"
    assert first.baseline.strategy == TraversalStrategy.BASELINE_SEQUENTIAL
    assert first.pythia.strategy == TraversalStrategy.PYTHIA_STRUCTURED
    assert first.baseline.candidate_budget == first.pythia.candidate_budget == 64
    assert any("exact double SHA-256" in boundary for boundary in first.claim_boundary)
    assert any("no live pool" in boundary for boundary in first.claim_boundary)


def test_structured_replay_can_demonstrate_candidate_budget_advantage():
    guidance = _guidance()
    budget = 512
    prefix = synthetic_header_prefix("pythia-structured-advantage")
    pythia_order = pythia_structured_nonce_order(guidance, budget, start_nonce=0)
    structured_window = pythia_order[:48]
    target, target_nonce, _ = target_from_best_nonce(
        template_prefix_hex=prefix,
        nonces=structured_window,
        block_height=840_321,
        difficulty=88_000_000_000_000.0,
        template_id="pythia_advantage_fixture",
    )
    # Ensure the chosen structural target is not trivially early in the baseline.
    assert target_nonce not in set(baseline_nonce_order(48, start_nonce=0))

    template = ReplayBlockTemplate(
        header_prefix_hex=prefix,
        target=target,
        block_height=840_321,
        difficulty=88_000_000_000_000.0,
        template_id="pythia_advantage_fixture",
    )
    report = run_matched_mining_benchmark(
        template=template,
        guidance=guidance,
        candidate_budget=budget,
    )

    assert report.pythia.first_hit_budget is not None
    assert (
        report.baseline.first_hit_budget is None
        or report.pythia.first_hit_budget < report.baseline.first_hit_budget
    )
    if report.candidate_budget_advantage is not None:
        assert report.candidate_budget_advantage > 1.0
    assert "PYTHIA" in report.interpretation


def test_no_hit_replay_becomes_criticism_not_false_claim():
    guidance = _guidance()
    template = ReplayBlockTemplate(
        header_prefix_hex=synthetic_header_prefix("no-hit-replay"),
        target=1,
        block_height=840_321,
        difficulty=88_000_000_000_000.0,
        template_id="no_hit_replay",
    )

    report = run_matched_mining_benchmark(
        template=template,
        guidance=guidance,
        candidate_budget=32,
    )

    assert report.baseline.first_hit_budget is None
    assert report.pythia.first_hit_budget is None
    assert report.candidate_budget_advantage is None
    assert "doctrine" not in " ".join(report.claim_boundary).lower()
