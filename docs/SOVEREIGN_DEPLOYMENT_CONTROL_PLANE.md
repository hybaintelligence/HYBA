# HYBA Sovereign Deployment Control Plane

## BLUF

HYBA can now be configured as a cloud, private-cloud, on-premise, sovereign-site, or air-gapped runtime while preserving the same governance surfaces: usage limits, admin privilege control, policy restrictions, data-residency checks, and append-only audit evidence.

This is the posture needed for sovereign customers who may run HYBA inside facilities such as a national lab, secure government site, Langley-style classified network, GCHQ-style secure environment, defence integrator enclave, or private regulated infrastructure. The code does not require customer data to leave that site.

## What this adds

```text
HYBA service request
  ↓
PrincipalContext
  ↓
SovereignDeploymentProfile
  ↓
SovereignControlPlane
  ↓
policy decision + evidence seal + audit event
  ↓
central ingestion / workload execution / admin action
```

The implementation is in:

- `python_backend/hyba_ciaas/sovereign_runtime.py`
- `tests/test_sovereign_deployment_control_plane.py`

It wraps the central ingestion layer introduced in `hyba_ciaas.ingestion`.

## Deployment modes

| Mode | Intended use | Default external network | Default cloud storage | Data-control posture |
|---|---|---:|---:|---|
| `cloud` | HYBA-managed SaaS/cloud deployment | allowed | allowed | managed cloud |
| `private_cloud` | Customer VPC / private managed cloud | allowed | allowed | customer/private cloud |
| `on_premise` | Customer data centre / secure facility | blocked | blocked | local |
| `sovereign_site` | Government/defence/regulated national infrastructure | blocked | blocked | local |
| `air_gapped` | Disconnected enclave | blocked | blocked | local |

For local sovereign modes, `deployment_attestation()` reports:

- `data_control_plane=local`
- `customer_data_leaves_site_by_default=false`
- `cloud_dependency_required=false`
- `audit_log_mode=append_only_hash_chain`

## Controls enforced

The control plane enforces:

1. deployment mode;
2. data residency;
3. external network egress;
4. cloud/object-storage use;
5. allowed source types;
6. admin role requirements;
7. dual-control requirements for privileged admin mutation;
8. reason/change-ticket requirements;
9. daily usage quotas;
10. privacy classification vs principal clearance;
11. operation restrictions;
12. append-only audit hash chain.

## Environment variables

The profile can be configured from environment variables so the same artifact can run in cloud or on-prem:

```bash
HYBA_DEPLOYMENT_MODE=sovereign_site
HYBA_TENANT_ID=uk-sovereign-customer
HYBA_JURISDICTION=uk
HYBA_SITE_NAME=secure-government-site
HYBA_DATA_RESIDENCY=uk
HYBA_CLASSIFICATION_FLOOR=unclassified

# local/sovereign defaults are already false, but they may be explicit
HYBA_ALLOW_EXTERNAL_NETWORK=false
HYBA_ALLOW_CLOUD_STORAGE=false

# restrict what the site may ingest
HYBA_ALLOWED_SOURCE_TYPES=records,inline,file,csv,json,sql,scada

# restrict specific operations if the customer/site requires it
HYBA_RESTRICTED_OPERATIONS=external_model_call,third_party_export

# local quota enforcement without cloud billing
HYBA_MAX_INGESTIONS_PER_DAY=100
HYBA_MAX_RECORDS_PER_INGESTION=1000000
HYBA_MAX_RECORDS_PER_DAY=10000000
HYBA_MAX_WORKLOADS_PER_DAY=1000
HYBA_MAX_PRIVILEGED_ADMIN_ACTIONS_PER_DAY=10

# governance
HYBA_ADMIN_ROLES=admin,security_admin,sovereign_admin
HYBA_AUDITOR_ROLES=admin,auditor,security_admin,sovereign_admin
HYBA_REQUIRE_DUAL_CONTROL_FOR_PRIVILEGED_ADMIN=true
HYBA_REQUIRE_REASON_FOR_PRIVILEGED_ADMIN=true
HYBA_IMMUTABLE_AUDIT=true
```

## Example: local sovereign ingestion

```python
from hyba_ciaas import (
    DataSourceSpec,
    DeploymentMode,
    PrincipalContext,
    SovereignControlPlane,
    SovereignDeploymentProfile,
    UsagePolicy,
    create_default_ingestion_service,
)

profile = SovereignDeploymentProfile(
    deployment_mode=DeploymentMode.SOVEREIGN_SITE,
    tenant_id="national-security-customer",
    jurisdiction="uk",
    data_residency="uk",
    allowed_source_types=("records", "inline", "file", "csv", "json", "sql", "scada"),
    usage_policy=UsagePolicy(
        max_ingestions_per_day=100,
        max_records_per_ingestion=1_000_000,
    ),
)

control_plane = SovereignControlPlane(profile)
principal = PrincipalContext(
    principal_id="operator-001",
    roles=("analyst",),
    tenant_id="national-security-customer",
    clearance="secret",
)

envelope = control_plane.ingest_with_controls(
    principal,
    DataSourceSpec(
        source_type="records",
        sector="national_security",
        source_id="local-feed",
        tenant_id="national-security-customer",
        privacy_classification="secret",
        metadata={"data_residency": "uk"},
        config={"records": [{"case": "A", "score": 0.91}]},
    ),
    service=create_default_ingestion_service(),
)
```

The returned ingestion envelope includes `metadata["deployment_control"]` with:

- the policy decision;
- the deployment attestation;
- the local record-metering count;
- evidence seals.

## Example: privileged admin mutation

```python
admin = PrincipalContext(
    principal_id="admin-001",
    roles=("sovereign_admin",),
    clearance="top_secret",
)

decision = control_plane.evaluate_action(
    admin,
    "privileged_admin_mutation",
    metadata={
        "reason": "rotate tenant execution restrictions",
        "second_approver": "auditor-002",
    },
)

decision.assert_allowed()
```

If the principal lacks an admin role, omits a reason, or fails dual control, the action is denied and the denial is still written to the audit log.

## Audit posture

Every decision is written as an `AuditEvent` with:

- event ID;
- timestamp;
- action;
- principal;
- tenant;
- allowed/denied status;
- reasons;
- decision evidence seal;
- previous event hash;
- event evidence seal.

This creates a local append-only evidence chain suitable for export to the customer’s own SIEM, evidence ledger, paper trail, or classified audit infrastructure.

## What this does not claim

This module does not claim that every customer deployment is automatically accredited, certified, or approved for classified use. Accreditation remains a customer/environment process. What the code now provides is the internal HYBA enforcement surface required to support that process:

- no cloud dependency in local sovereign modes;
- deterministic policy decisions;
- usage limits without cloud billing;
- admin and privileged-admin controls;
- local audit/evidence chain;
- explicit data residency and network/cloud-storage restrictions.

## Verification

```bash
pytest tests/test_sovereign_deployment_control_plane.py -q
```
