from pythia_mining.golden_quantum_trifecta import (
    TrifectaPillar,
    assert_golden_quantum_trifecta_integrity,
    bounded_mps_parameter_upper_bound,
    build_golden_quantum_trifecta_certificate,
)


def test_golden_quantum_trifecta_combines_all_three_pillars():
    certificate = build_golden_quantum_trifecta_certificate()

    assert certificate.protocol == "HYBA_GOLDEN_QUANTUM_TRIFECTA_V1"
    assert set(certificate.pillars) == {pillar.value for pillar in TrifectaPillar}
    assert "quantum mathematics first" in certificate.distinctive_claim
    assert "substrate-independent execution" in certificate.distinctive_claim
    assert "golden-ratio stabilisation" in certificate.distinctive_claim


def test_thousand_qubit_surface_is_preserved_without_full_state_materialisation():
    certificate = build_golden_quantum_trifecta_certificate()

    assert certificate.qubit_formalism_sites == 1000
    assert certificate.full_state_log10_amplitudes > 300.0
    assert certificate.bounded_mps_parameter_upper_bound == 512000
    assert certificate.avoided_full_state_materialisation is True
    assert certificate.hardware_required_for_quantum_mathematics is False
    assert certificate.physical_qpu_required is False


def test_bounded_parameter_count_scales_as_tensor_network_surface():
    assert (
        bounded_mps_parameter_upper_bound(
            qubit_formalism_sites=1000,
            physical_dimension=2,
            max_bond_dimension=16,
        )
        == 1000 * 2 * 16 * 16
    )


def test_integrity_guard_rejects_any_attempt_to_remove_golden_ratio_grammar():
    certificate = build_golden_quantum_trifecta_certificate()
    body = certificate.as_dict()
    body["distinctive_claim"] = body["distinctive_claim"].replace("golden-ratio", "")
    broken = type(certificate)(**body)

    try:
        assert_golden_quantum_trifecta_integrity(broken)
    except AssertionError as exc:
        assert "golden-ratio system" in str(exc)
    else:
        raise AssertionError("certificate without golden-ratio grammar should fail closed")


def test_integrity_guard_accepts_canonical_certificate():
    certificate = build_golden_quantum_trifecta_certificate()
    assert_golden_quantum_trifecta_integrity(certificate)


def test_certificate_hash_is_replay_stable():
    first = build_golden_quantum_trifecta_certificate()
    second = build_golden_quantum_trifecta_certificate()

    assert first.certificate_hash == second.certificate_hash
    assert len(first.certificate_hash) == 64
