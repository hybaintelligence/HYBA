"""VALIDATION TIER: SCIENTIFIC DELTA.

The fixtures below are deterministic replay datasets used to verify that the
benchmark harness can detect improvement. They are not live mining telemetry.
"""

from pythia_mining.salamander_frontier import (
    DreamMutation,
    ImmutableEvidenceLog,
    ResonanceMeasurement,
    ResonantSubstrateTuner,
    SalamanderDreamState,
    SalamanderGene,
)


def test_benchmark_thermal_resonance_efficiency_fixture():
    tuner = ResonantSubstrateTuner(jitter_weight=1.0, thermal_weight=4.0, throughput_weight=1.0)
    standard = ResonanceMeasurement(
        phi_value=1.60, execution_jitter_ms=3.0, thermal_drift_c=8.0, throughput=100.0
    )
    resonant = ResonanceMeasurement(
        phi_value=1.618, execution_jitter_ms=1.0, thermal_drift_c=2.0, throughput=105.0
    )

    lock = tuner.find_harmonic_phi([standard, resonant])
    heat_per_work_standard = standard.thermal_drift_c / standard.throughput
    heat_per_work_resonant = resonant.thermal_drift_c / resonant.throughput

    assert lock.phi_value == resonant.phi_value
    assert heat_per_work_resonant < heat_per_work_standard


def test_benchmark_dream_optimization_roi_fixture():
    historical = ImmutableEvidenceLog().append(
        "month_window", actor="benchmark", timestamp=1.0, revenue=120.0, cost=100.0
    )
    genes = {
        "fee_pressure": SalamanderGene(
            "fee_pressure", value=0.20, min_value=0.0, max_value=1.0
        )
    }

    def roi_model(log, candidate_genes):
        entry = log.entries()[0]
        base_roi = (entry.data["revenue"] - entry.data["cost"]) / entry.data["cost"]
        # Fixture optimum is 0.35; the dream must discover the better static setting.
        return base_roi - abs(candidate_genes["fee_pressure"].value - 0.35)

    dream = SalamanderDreamState(roi_model, promotion_threshold=0.01)
    outcomes = dream.dream(
        historical,
        genes,
        [DreamMutation("fee_pressure", 0.25), DreamMutation("fee_pressure", 0.35)],
        timestamp=2.0,
    )

    assert outcomes[0].promoted is True
    assert outcomes[0].mutated_value == 0.35
    assert outcomes[0].simulated_fitness > outcomes[0].baseline_fitness
