"""Property battery coverage for the Salamander substrate invariants."""

import pytest

try:
    from hypothesis import given, settings
    from hypothesis import strategies as st
except ImportError:  # pragma: no cover
    given = settings = st = None

from pythia_mining.salamander_frontier import (
    ImmutableEvidenceLog,
    MetabolicInvariantMetrics,
    PHI,
    SalamanderPropertyBattery,
)


def _evidence_logs():
    event_names = st.sampled_from(
        [
            "agent_spawned",
            "job_received",
            "search_started",
            "share_found",
            "share_submitted",
            "share_accepted",
            "job_completed",
            "target_hashrate_updated",
        ]
    )
    data_values = st.one_of(
        st.integers(min_value=0, max_value=1_000_000),
        st.floats(
            min_value=0.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False
        ),
        st.text(min_size=0, max_size=20),
    )
    event_data = st.dictionaries(
        keys=st.sampled_from(
            ["job_id", "start_nonce", "target_hashrate", "domain", "roi"]
        ),
        values=data_values,
        max_size=3,
    )
    entries = st.lists(
        st.tuples(
            event_names,
            st.text(min_size=1, max_size=16),
            st.floats(
                min_value=0.0,
                max_value=1_000_000.0,
                allow_nan=False,
                allow_infinity=False,
            ),
            event_data,
        ),
        max_size=20,
    )

    def build_log(raw_entries):
        log = ImmutableEvidenceLog()
        for event, actor, timestamp, data in raw_entries:
            log = log.append(event, actor=actor, timestamp=timestamp, **data)
        return log

    return entries.map(build_log)


if given is not None:

    @given(evidence_log=_evidence_logs())
    @settings(max_examples=50)
    def test_property_battery_preserves_evidence_fidelity(evidence_log):
        result = SalamanderPropertyBattery().invariant_evidence_fidelity(evidence_log)

        assert result.passed is True
        assert result.reason == "replay_digest_matches_evidence"
        assert result.observed["original_digest"] == result.observed["replayed_digest"]

    @given(
        energy_input=st.floats(
            min_value=0.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False
        ),
        efficiency=st.floats(
            min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
        ),
        max_work_per_joule=st.floats(
            min_value=0.0, max_value=1_000_000.0, allow_nan=False, allow_infinity=False
        ),
        utilization=st.floats(
            min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
        ),
    )
    @settings(max_examples=50)
    def test_property_battery_accepts_work_within_metabolic_budget(
        energy_input, efficiency, max_work_per_joule, utilization
    ):
        budget = energy_input * efficiency * max_work_per_joule
        metrics = MetabolicInvariantMetrics(
            work_performed=budget * utilization,
            energy_input_joules=energy_input,
            thermodynamic_efficiency=efficiency,
            max_work_per_joule=max_work_per_joule,
        )

        result = SalamanderPropertyBattery().invariant_metabolic_conservation(metrics)

        assert result.passed is True
        assert result.reason == "work_within_energy_budget"

    @given(
        drift=st.floats(
            min_value=-0.49, max_value=0.49, allow_nan=False, allow_infinity=False
        )
    )
    @settings(max_examples=50)
    def test_property_battery_accepts_phi_inside_harmonic_zone(drift):
        result = SalamanderPropertyBattery().invariant_phi_resonance_bounds(PHI + drift)

        assert result.passed is True
        assert result.reason == "phi_within_harmonic_zone"

else:

    @pytest.mark.skip(reason="hypothesis is not installed")
    def test_property_battery_preserves_evidence_fidelity():
        pass

    @pytest.mark.skip(reason="hypothesis is not installed")
    def test_property_battery_accepts_work_within_metabolic_budget():
        pass

    @pytest.mark.skip(reason="hypothesis is not installed")
    def test_property_battery_accepts_phi_inside_harmonic_zone():
        pass


def test_property_battery_rejects_impossible_metabolic_claim():
    result = SalamanderPropertyBattery().invariant_metabolic_conservation(
        MetabolicInvariantMetrics(
            work_performed=101.0,
            energy_input_joules=10.0,
            thermodynamic_efficiency=0.5,
            max_work_per_joule=20.0,
        )
    )

    assert result.passed is False
    assert "PHYSICS_VIOLATION" in result.reason


@pytest.mark.parametrize("current_phi", [PHI + 0.5, PHI - 0.5001, 9.999])
def test_property_battery_rejects_phi_outside_harmonic_zone(current_phi):
    result = SalamanderPropertyBattery().invariant_phi_resonance_bounds(current_phi)

    assert result.passed is False
    assert "GENETIC_DRIFT" in result.reason


def test_property_battery_rejects_non_finite_inputs():
    battery = SalamanderPropertyBattery()

    with pytest.raises(ValueError, match="finite"):
        battery.invariant_phi_resonance_bounds(float("nan"))

    with pytest.raises(ValueError, match="finite"):
        battery.invariant_metabolic_conservation(
            MetabolicInvariantMetrics(
                work_performed=float("inf"),
                energy_input_joules=1.0,
                thermodynamic_efficiency=1.0,
                max_work_per_joule=1.0,
            )
        )
