import math

import pytest

from pythia_mining.yang_mills_spectral_gap import (
    EXPECTED_MASS_GAP,
    MIN_NONZERO_SPECTRUM_POINTS,
    YangMillsSpectralGapMeasurement,
)


def test_sparse_spectrum_does_not_fabricate_phi_scaled_data():
    measurement = YangMillsSpectralGapMeasurement(lattice_size=2, n_configs=0)
    measurement.actions = [0.0, 1e-12, EXPECTED_MASS_GAP]

    spectrum = measurement.compute_spectrum()
    results = measurement.measure_spectral_gap()

    assert spectrum.tolist() == [pytest.approx(EXPECTED_MASS_GAP)]
    assert results["success"] is False
    assert results["validated"] is False
    assert results["operational_elevated"] is False
    assert results["verdict"] == "insufficient_observed_spectrum"
    assert "No synthetic" in results["error"]
    assert results["controls"]["synthetic_spectrum_used"] is False
    assert results["controls"]["ablation_controls_run"] is False


def test_large_prediction_miss_fails_even_with_large_z_like_separation():
    measurement = YangMillsSpectralGapMeasurement(
        lattice_size=2, n_configs=MIN_NONZERO_SPECTRUM_POINTS
    )
    measurement.actions = [
        EXPECTED_MASS_GAP * 3.38 + i * 1e-4 for i in range(MIN_NONZERO_SPECTRUM_POINTS)
    ]

    results = measurement.measure_spectral_gap()

    assert results["success"] is True
    assert results["validated"] is False
    assert results["operational_elevated"] is False
    assert results["verdict"] == "not_elevated_against_operational_controls"
    assert results["mass_gap"]["prediction_error_pct"] > 200
    assert math.isfinite(results["mass_gap"]["prediction_z_score"])
    assert results["controls"]["ablation_controls_run"] is True
    assert results["controls"]["synthetic_spectrum_used"] is False


def test_prediction_compatible_spectrum_passes_only_against_prediction():
    measurement = YangMillsSpectralGapMeasurement(
        lattice_size=2, n_configs=MIN_NONZERO_SPECTRUM_POINTS
    )
    measurement.actions = [
        EXPECTED_MASS_GAP + i * EXPECTED_MASS_GAP * 0.02
        for i in range(MIN_NONZERO_SPECTRUM_POINTS)
    ]

    results = measurement.measure_spectral_gap()

    assert results["success"] is True
    assert results["validated"] is True
    assert results["operational_elevated"] is True
    assert results["verdict"] == "operational_phi_mass_gap_elevated"
    assert results["mass_gap"]["prediction_error_pct"] == pytest.approx(0.0)
    assert results["controls"]["phi_best_anchor"] is True
    assert results["controls"]["ranking_by_absolute_error"][0] == "phi"
    assert "not a proof" in results["claim_boundary"]["not_claimed"]
