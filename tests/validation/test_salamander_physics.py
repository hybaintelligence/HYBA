"""VALIDATION TIER: PHYSICS & MATH INVARIANTS.

These checks are bounded repository invariants, not claims of external physical
irrefutability.  They make conservation failures explicit and auditable.
"""

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


if given is not None:

    @given(wattage=st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=32)
    def test_invariant_metabolic_conservation_under_efficiency_ceiling(wattage):
        battery = SalamanderPropertyBattery()
        one_hour_joules = wattage * 3600.0
        metrics = MetabolicInvariantMetrics(
            work_performed=one_hour_joules * 0.42,
            energy_input_joules=one_hour_joules,
            thermodynamic_efficiency=0.42,
            max_work_per_joule=1.0,
        )

        result = battery.invariant_metabolic_conservation(metrics)

        assert result.passed is True
        assert result.observed["efficiency_used"] <= 1.0

    @given(random_data=st.text(max_size=128))
    @settings(max_examples=32)
    def test_invariant_evidence_manifest_detects_tamper(random_data):
        log = ImmutableEvidenceLog().append(
            "validation_payload", actor="physics-watchdog", timestamp=1.0, data=random_data
        )
        battery = SalamanderPropertyBattery()

        result = battery.invariant_evidence_fidelity(log)
        tampered = ImmutableEvidenceLog().append(
            "validation_payload",
            actor="physics-watchdog",
            timestamp=1.0,
            data=random_data + "_tampered",
        )

        assert result.passed is True
        assert tampered.seal() != log.seal()

else:

    @pytest.mark.skip(reason="hypothesis is not installed")
    def test_invariant_metabolic_conservation_under_efficiency_ceiling():
        pass

    @pytest.mark.skip(reason="hypothesis is not installed")
    def test_invariant_evidence_manifest_detects_tamper():
        pass


def test_invariant_phi_resonance_rejects_siren_ratio():
    result = SalamanderPropertyBattery().invariant_phi_resonance_bounds(9.999)

    assert result.passed is False
    assert "GENETIC_DRIFT" in result.reason
    assert result.observed["golden_ratio"] == PHI
