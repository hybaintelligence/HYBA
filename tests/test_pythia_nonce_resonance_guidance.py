from pythia_mining.nonce_resonance_guidance import (
    BlockContext,
    EmpiricalStructureEvidence,
    MiningLaunchDecision,
    MiningPreflight,
    ResonanceSignal,
    SovereignMiningCap,
    build_nonce_resonance_guidance,
    evaluate_mining_preflight,
)


def _evidence():
    return EmpiricalStructureEvidence(
        sample_size=4096,
        phi15_rate=0.41,
        golden_angle_alignment=0.77,
        birthday_echo_rate=0.33,
        sector_coverage=0.94,
        large_gap_score=0.58,
        dodecahedral_domain_score=0.91,
        icosahedral_face_score=0.87,
        mass_gap_valley_score=0.82,
        entanglement_spectrum_score=0.79,
        uniformity_score=0.62,
    )


def _context(height=850_001, difficulty=83_000_000_000_000.0):
    return BlockContext(
        block_height=height,
        difficulty=difficulty,
        target_hex="0000000000000000000123456789abcdef",
        previous_block_hash="00" * 32,
        mempool_pressure=0.4,
    )


def test_guidance_is_not_phi15_only():
    guidance = build_nonce_resonance_guidance(_evidence(), _context())

    signals = [priority.signal for priority in guidance.priorities]

    assert ResonanceSignal.PHI15_RESONANCE in signals
    assert ResonanceSignal.DODECAHEDRAL_DOMAIN in signals
    assert ResonanceSignal.ICOSAHEDRAL_FACE in signals
    assert ResonanceSignal.MASS_GAP_VALLEY in signals
    assert ResonanceSignal.ENTANGLEMENT_SPECTRUM in signals
    assert ResonanceSignal.DIFFICULTY_PRESSURE in signals
    assert ResonanceSignal.RETARGET_EPOCH_PHASE in signals
    assert signals.index(ResonanceSignal.PHI15_RESONANCE) > 0


def test_block_height_and_difficulty_shape_search_context():
    early = build_nonce_resonance_guidance(_evidence(), _context(height=848_064))
    late = build_nonce_resonance_guidance(_evidence(), _context(height=849_900))

    assert early.block_context.retarget_phase == "early_epoch_exploration"
    assert late.block_context.retarget_phase == "late_epoch_precision"
    assert late.block_context.difficulty_pressure > 0.0
    assert any("Retarget phase" in priority.reason for priority in late.priorities)


def test_guidance_uses_quantum_arsenal_dodeca_icosa_pulvini_and_collapse():
    guidance = build_nonce_resonance_guidance(_evidence(), _context())

    assert guidance.arsenal.quantum_mathematics_first is True
    assert guidance.arsenal.substrate_independent_execution is True
    assert guidance.arsenal.golden_ratio_grammar is True
    assert guidance.arsenal.tensor_network_prior is True
    assert guidance.arsenal.pulvin_memory_compression is True
    assert guidance.arsenal.hendrix_phi_traversal is True
    assert guidance.search_plan.m32_domains == 32
    assert guidance.search_plan.icosahedral_symmetry_order == 120
    assert guidance.search_plan.dodecahedral_working_surface == 20
    assert guidance.search_plan.full_nonce_coverage == 2**32
    assert "Collapse" in guidance.collapse_instruction
    assert "exact SHA-256d" in guidance.collapse_instruction
    assert guidance.seal


def test_preflight_allows_guarded_search_when_caps_and_evidence_are_satisfied():
    guidance = build_nonce_resonance_guidance(_evidence(), _context())
    report = evaluate_mining_preflight(
        guidance,
        MiningPreflight(
            operator_approved=True,
            pool_credentials_present=True,
            exact_sha256d_enabled=True,
            full_coverage_preserved=True,
            evidence_packet_present=True,
            runtime_minutes=30,
            power_limit_watts=1200.0,
            cap=SovereignMiningCap(
                accepted_blocks_today=23, accepted_blocks_current_hour=0
            ),
        ),
    )

    assert report.decision == MiningLaunchDecision.GUARDED_SEARCH_READY
    assert report.allowed is True
    assert report.blocked_reasons == []


def test_hourly_and_daily_sovereign_caps_block_search():
    guidance = build_nonce_resonance_guidance(_evidence(), _context())

    hourly = evaluate_mining_preflight(
        guidance,
        MiningPreflight(
            operator_approved=True,
            pool_credentials_present=True,
            exact_sha256d_enabled=True,
            full_coverage_preserved=True,
            evidence_packet_present=True,
            runtime_minutes=30,
            power_limit_watts=1200.0,
            cap=SovereignMiningCap(
                accepted_blocks_today=3, accepted_blocks_current_hour=1
            ),
        ),
    )
    daily = evaluate_mining_preflight(
        guidance,
        MiningPreflight(
            operator_approved=True,
            pool_credentials_present=True,
            exact_sha256d_enabled=True,
            full_coverage_preserved=True,
            evidence_packet_present=True,
            runtime_minutes=30,
            power_limit_watts=1200.0,
            cap=SovereignMiningCap(
                accepted_blocks_today=24, accepted_blocks_current_hour=0
            ),
        ),
    )

    assert hourly.decision == MiningLaunchDecision.BLOCKED
    assert "hourly sovereign cap" in hourly.blocked_reasons[-1]
    assert daily.decision == MiningLaunchDecision.BLOCKED
    assert "daily sovereign cap" in daily.blocked_reasons[-1]


def test_forbidden_claims_and_disabled_verifier_fail_closed():
    guidance = build_nonce_resonance_guidance(_evidence(), _context())
    report = evaluate_mining_preflight(
        guidance,
        MiningPreflight(
            operator_approved=True,
            pool_credentials_present=True,
            exact_sha256d_enabled=False,
            full_coverage_preserved=True,
            evidence_packet_present=True,
            runtime_minutes=30,
            power_limit_watts=1200.0,
            forbidden_claim_text="guaranteed block and bypass sha",
        ),
    )

    assert report.decision == MiningLaunchDecision.BLOCKED
    assert "exact SHA-256d verifier disabled" in report.blocked_reasons
    assert any("guaranteed block" in reason for reason in report.blocked_reasons)
    assert any("bypass sha" in reason for reason in report.blocked_reasons)


def test_insufficient_structure_evidence_blocks_guided_search():
    weak = EmpiricalStructureEvidence(sample_size=16)
    guidance = build_nonce_resonance_guidance(weak, _context())
    report = evaluate_mining_preflight(
        guidance,
        MiningPreflight(
            operator_approved=True,
            pool_credentials_present=True,
            exact_sha256d_enabled=True,
            full_coverage_preserved=True,
            evidence_packet_present=True,
            runtime_minutes=15,
            power_limit_watts=900.0,
        ),
    )

    assert report.decision == MiningLaunchDecision.BLOCKED
    assert (
        "insufficient empirical blockchain structure evidence" in report.blocked_reasons
    )
