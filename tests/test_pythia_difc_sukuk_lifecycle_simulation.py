from pythia_finance_audit.sukuk_lifecycle_simulation import (
    SCHEMA_VERSION,
    compute_lifecycle_hash,
    simulate_sukuk_lifecycle_drift,
)


def test_lifecycle_simulation_detects_warning_then_blocker_without_action():
    bundle = simulate_sukuk_lifecycle_drift(include_packets=False)

    assert bundle["schema"] == SCHEMA_VERSION
    assert bundle["human_review_required"] is True
    assert bundle["automatic_action_allowed"] is False
    assert bundle["summary"]["total_steps"] == 5
    assert bundle["summary"]["first_warning_step_id"] == "03"
    assert bundle["summary"]["first_blocker_step_id"] == "04"
    assert (
        bundle["summary"]["first_blocker_stage"] == "asset_drift_restructuring_trigger"
    )

    for entry in bundle["timeline"]:
        assert entry["human_review_required"] is True
        assert entry["automatic_action_allowed"] is False
        assert entry["action"] == "ESCALATE_TO_SOVEREIGN_HUMAN"
        assert entry["packet_hash"]

    step_03 = next(entry for entry in bundle["timeline"] if entry["step_id"] == "03")
    assert "DIFC_AAOIFI_RISK_SHARING_DEBT_MIMICRY" in step_03["warning_findings"]
    assert step_03["failed_findings"] == []

    step_04 = next(entry for entry in bundle["timeline"] if entry["step_id"] == "04")
    assert "DIFC_AAOIFI_ASSET_BACKING_OWNERSHIP" in step_04["failed_findings"]
    assert "DIFC_AAOIFI_SUBSTANCE_OVER_FORM" in step_04["failed_findings"]
    assert "DIFC_AAOIFI_GHARAR_UNCERTAINTY" in step_04["failed_findings"]


def test_lifecycle_hash_recomputes_and_is_stable_for_same_scenario():
    first = simulate_sukuk_lifecycle_drift(include_packets=True)
    second = simulate_sukuk_lifecycle_drift(include_packets=True)

    assert first["lifecycle_packet_hash"] == compute_lifecycle_hash(first)
    assert second["lifecycle_packet_hash"] == compute_lifecycle_hash(second)
    assert first["lifecycle_packet_hash"] == second["lifecycle_packet_hash"]


def test_compact_lifecycle_keeps_lift_out_shape_without_embedded_packets():
    bundle = simulate_sukuk_lifecycle_drift(include_packets=False)

    assert all("packet" not in entry for entry in bundle["timeline"])
    assert all("packet_hash" in entry for entry in bundle["timeline"])
    assert "pythia_mining" not in str(bundle["timeline"])
