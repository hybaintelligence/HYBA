#!/usr/bin/env python3
"""HYBA sovereign readiness smoke gate.

This script is intentionally narrow and dependency-light. It validates the
sovereign deployment control plane and central ingestion boundary without
requiring cloud credentials, external APIs, Kafka, SCADA simulators, customer
systems, or live network egress.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from hyba_ciaas import (  # noqa: E402
    DataSourceSpec,
    DeploymentMode,
    PrincipalContext,
    SovereignControlPlane,
    SovereignDeploymentProfile,
    UsagePolicy,
    create_default_ingestion_service,
)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_gate() -> Dict[str, Any]:
    profile = SovereignDeploymentProfile(
        deployment_mode=DeploymentMode.AIR_GAPPED,
        tenant_id="sovereign-ci",
        jurisdiction="test-jurisdiction",
        site_name="ci-air-gap-simulation",
        data_residency="uk",
        allowed_source_types=("records", "inline", "file", "csv", "json"),
        usage_policy=UsagePolicy(
            max_ingestions_per_day=5,
            max_records_per_ingestion=100,
            max_records_per_day=500,
            max_privileged_admin_actions_per_day=5,
        ),
    )
    control_plane = SovereignControlPlane(profile)
    analyst = PrincipalContext(
        principal_id="analyst-ci",
        roles=("analyst",),
        tenant_id="sovereign-ci",
        clearance="secret",
    )
    auditor = PrincipalContext(
        principal_id="auditor-ci",
        roles=("auditor",),
        tenant_id="sovereign-ci",
        clearance="secret",
    )
    admin = PrincipalContext(
        principal_id="admin-ci",
        roles=("sovereign_admin",),
        tenant_id="sovereign-ci",
        clearance="top_secret",
    )

    attestation = control_plane.deployment_attestation()
    assert_condition(attestation["profile"]["deployment_mode"] == "air_gapped", "air-gapped mode not attested")
    assert_condition(attestation["data_control_plane"] == "local", "local control plane not attested")
    assert_condition(attestation["customer_data_leaves_site_by_default"] is False, "data egress default is not false")
    assert_condition(attestation["cloud_dependency_required"] is False, "cloud dependency is unexpectedly required")
    assert_condition(attestation["audit_log_mode"] == "append_only_hash_chain", "audit hash-chain mode not attested")

    cloud_denial = control_plane.authorize_ingestion(
        analyst,
        DataSourceSpec(
            source_type="gcs",
            sector="national_security",
            privacy_classification="secret",
            metadata={"data_residency": "uk"},
        ),
    )
    assert_condition(not cloud_denial.allowed, "air-gapped cloud storage source was allowed")

    http_denial = control_plane.authorize_ingestion(
        analyst,
        DataSourceSpec(
            source_type="http",
            sector="national_security",
            privacy_classification="secret",
            metadata={"data_residency": "uk"},
        ),
    )
    assert_condition(not http_denial.allowed, "air-gapped external HTTP source was allowed")

    envelope = control_plane.ingest_with_controls(
        analyst,
        DataSourceSpec(
            source_type="records",
            sector="national_security",
            source_id="ci-local-feed",
            tenant_id="sovereign-ci",
            privacy_classification="secret",
            metadata={"data_residency": "uk"},
            config={
                "records": [
                    {"case_id": "A", "risk": 0.82, "region": "uk"},
                    {"case_id": "B", "risk": 0.43, "region": "uk"},
                ]
            },
        ),
        service=create_default_ingestion_service(),
        estimated_records=2,
    )
    assert_condition(envelope.raw_shape == (2, 3), "local ingestion did not preserve expected shape")
    assert_condition(envelope.metadata["deployment_control"]["decision"]["allowed"] is True, "ingestion control decision was not allowed")

    admin_denial = control_plane.evaluate_action(
        admin,
        "privileged_admin_mutation",
        metadata={"reason": "rotate sovereign policy"},
    )
    assert_condition(not admin_denial.allowed, "privileged admin mutation without dual control was allowed")

    admin_allowed = control_plane.evaluate_action(
        admin,
        "privileged_admin_mutation",
        metadata={"reason": "rotate sovereign policy", "second_approver": "auditor-ci"},
    )
    assert_condition(admin_allowed.allowed, "privileged admin mutation with dual control was denied")

    audit_events = control_plane.export_audit_log(auditor)
    assert_condition(len(audit_events) >= 4, "audit log did not capture readiness events")
    assert_condition(audit_events[0]["previous_hash"] == "genesis", "audit chain does not start at genesis")
    for previous, current in zip(audit_events, audit_events[1:]):
        assert_condition(
            current["previous_hash"] == previous["evidence_seal"],
            "audit hash-chain linkage is broken",
        )

    return {
        "status": "passed",
        "deployment_mode": attestation["profile"]["deployment_mode"],
        "data_control_plane": attestation["data_control_plane"],
        "cloud_dependency_required": attestation["cloud_dependency_required"],
        "audit_events": len(audit_events),
        "ingestion_run_id": envelope.run_id,
        "ingestion_records": envelope.raw_shape[0],
        "attestation_evidence_seal": attestation["evidence_seal"],
    }


def main() -> int:
    result = run_gate()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
