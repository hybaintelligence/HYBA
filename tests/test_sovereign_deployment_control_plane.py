from hyba_ciaas import (
    DataSourceSpec,
    DeploymentMode,
    PrincipalContext,
    SovereignControlPlane,
    SovereignDeploymentProfile,
    UsagePolicy,
    create_default_ingestion_service,
)


def test_on_prem_profile_allows_local_ingestion_and_seals_controls():
    profile = SovereignDeploymentProfile(
        deployment_mode=DeploymentMode.ON_PREMISE,
        tenant_id="gchq-lab",
        jurisdiction="uk",
        site_name="local-secure-room",
        data_residency="uk",
        allowed_source_types=("records", "inline", "file", "csv"),
        usage_policy=UsagePolicy(max_ingestions_per_day=2, max_records_per_ingestion=10),
    )
    control_plane = SovereignControlPlane(profile)
    principal = PrincipalContext(
        principal_id="analyst-1",
        tenant_id="gchq-lab",
        roles=("analyst",),
        clearance="secret",
    )

    envelope = control_plane.ingest_with_controls(
        principal,
        DataSourceSpec(
            source_type="records",
            sector="national_security",
            source_id="local-case-feed",
            tenant_id="gchq-lab",
            privacy_classification="secret",
            metadata={"data_residency": "uk"},
            config={
                "records": [
                    {"case_id": "A", "risk": 0.72, "region": "uk"},
                    {"case_id": "B", "risk": 0.31, "region": "uk"},
                ]
            },
        ),
        service=create_default_ingestion_service(),
        estimated_records=2,
    )

    assert envelope.raw_shape == (2, 3)
    assert envelope.metadata["deployment_control"]["decision"]["allowed"] is True
    assert envelope.metadata["deployment_control"]["deployment_attestation"]["profile"]["deployment_mode"] == "on_premise"
    assert envelope.metadata["deployment_control"]["deployment_attestation"]["cloud_dependency_required"] is False
    assert control_plane.get_usage_snapshot(principal)["records"] == 2


def test_on_prem_profile_blocks_cloud_storage_and_external_sources_by_default():
    profile = SovereignDeploymentProfile(
        deployment_mode=DeploymentMode.ON_PREMISE,
        tenant_id="langley-site",
        jurisdiction="us",
        data_residency="us",
    )
    control_plane = SovereignControlPlane(profile)
    principal = PrincipalContext(principal_id="analyst-2", roles=("analyst",), clearance="secret")

    cloud_decision = control_plane.authorize_ingestion(
        principal,
        DataSourceSpec(
            source_type="gcs",
            sector="defence",
            privacy_classification="secret",
            metadata={"data_residency": "us"},
        ),
    )
    api_decision = control_plane.authorize_ingestion(
        principal,
        DataSourceSpec(
            source_type="http",
            sector="defence",
            privacy_classification="secret",
            metadata={"data_residency": "us"},
        ),
    )

    assert cloud_decision.allowed is False
    assert "cloud/object-storage ingestion is disabled" in "; ".join(cloud_decision.reasons)
    assert api_decision.allowed is False
    assert "external network ingestion is disabled" in "; ".join(api_decision.reasons)


def test_privileged_admin_requires_authorised_role_reason_and_dual_control():
    profile = SovereignDeploymentProfile(
        deployment_mode=DeploymentMode.SOVEREIGN_SITE,
        tenant_id="sovereign-customer",
        jurisdiction="uk",
        data_residency="uk",
    )
    control_plane = SovereignControlPlane(profile)

    non_admin = PrincipalContext(principal_id="user-1", roles=("analyst",), clearance="secret")
    denied = control_plane.evaluate_action(
        non_admin,
        "privileged_admin_mutation",
        metadata={"reason": "rotate customer policy", "second_approver": "security-controller"},
    )
    assert denied.allowed is False
    assert "admin action requires an authorised admin role" in "; ".join(denied.reasons)

    admin = PrincipalContext(principal_id="admin-1", roles=("sovereign_admin",), clearance="top_secret")
    needs_dual_control = control_plane.evaluate_action(
        admin,
        "privileged_admin_mutation",
        metadata={"reason": "change tenant execution restriction"},
    )
    assert needs_dual_control.allowed is False
    assert "dual-control" in "; ".join(needs_dual_control.reasons)

    allowed = control_plane.evaluate_action(
        admin,
        "privileged_admin_mutation",
        metadata={"reason": "change tenant execution restriction", "second_approver": "auditor-1"},
    )
    assert allowed.allowed is True
    assert allowed.evidence_seal


def test_usage_quotas_are_enforced_without_cloud_billing():
    profile = SovereignDeploymentProfile(
        deployment_mode=DeploymentMode.AIR_GAPPED,
        tenant_id="air-gap",
        jurisdiction="uk",
        data_residency="uk",
        usage_policy=UsagePolicy(max_ingestions_per_day=1, max_records_per_day=5),
    )
    control_plane = SovereignControlPlane(profile)
    principal = PrincipalContext(principal_id="operator-1", roles=("operator",), clearance="secret")

    first = control_plane.authorize_ingestion(
        principal,
        DataSourceSpec(
            source_type="records",
            sector="energy",
            privacy_classification="secret",
            metadata={"data_residency": "uk"},
        ),
        estimated_records=3,
    )
    assert first.allowed is True
    control_plane.record_usage(principal, "ingestions", 1)
    control_plane.record_usage(principal, "records", 3)

    second = control_plane.authorize_ingestion(
        principal,
        DataSourceSpec(
            source_type="records",
            sector="energy",
            privacy_classification="secret",
            metadata={"data_residency": "uk"},
        ),
        estimated_records=3,
    )
    assert second.allowed is False
    assert "daily ingestion quota exceeded" in "; ".join(second.reasons)
    assert "daily record quota exceeded" in "; ".join(second.reasons)


def test_audit_export_requires_auditor_role_and_hash_chain_is_present():
    profile = SovereignDeploymentProfile(
        deployment_mode=DeploymentMode.SOVEREIGN_SITE,
        tenant_id="national-lab",
        jurisdiction="uk",
        data_residency="uk",
    )
    control_plane = SovereignControlPlane(profile)
    analyst = PrincipalContext(principal_id="analyst", roles=("analyst",), clearance="secret")
    auditor = PrincipalContext(principal_id="auditor", roles=("auditor",), clearance="secret")

    control_plane.evaluate_action(analyst, "execute_workload", quantity=1)
    denied_export = control_plane.evaluate_action(analyst, "export_audit", record_audit=False)
    assert denied_export.allowed is False

    events = control_plane.export_audit_log(auditor)
    assert len(events) >= 2
    assert events[0]["previous_hash"] == "genesis"
    assert events[1]["previous_hash"] == events[0]["evidence_seal"]
