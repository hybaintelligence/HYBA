# HYBA Sovereign Deployment Whitepaper

## BLUF

HYBA can be deployed across cloud, private-cloud, on-premise, sovereign-site, and air-gapped environments while preserving local governance controls over ingestion, workloads, administrative actions, usage, and audit evidence.

The sovereign posture is implemented through a control plane rather than a marketing label:

```text
HYBA service request
  -> PrincipalContext
  -> SovereignDeploymentProfile
  -> SovereignControlPlane
  -> policy decision + evidence seal + audit event
  -> central ingestion / workload execution / admin action
```

## Why this matters

Sovereign and regulated customers often cannot allow operational data, sensitive intelligence, regulated records, audit logs, or administrative control to depend on unmanaged external services.

Typical requirements include:

- no customer-data egress by default;
- no external ingestion by default;
- no cloud object storage by default;
- local policy enforcement;
- local usage governance;
- local privileged-admin controls;
- local tamper-evident audit evidence;
- deployment-mode attestation;
- data-residency enforcement.

HYBA now provides these technical enforcement surfaces through `hyba_ciaas.sovereign_runtime`.

## Deployment modes

| Mode | Intended environment | Default external network | Default cloud storage | Data-control posture |
|---|---|---:|---:|---|
| `cloud` | HYBA-managed or managed cloud deployment | allowed | allowed | managed cloud |
| `private_cloud` | Customer VPC / private managed cloud | allowed | allowed | customer cloud boundary |
| `on_premise` | Customer data centre or secure facility | blocked by default | blocked by default | local |
| `sovereign_site` | Government, defence, or regulated national estate | blocked by default | blocked by default | local sovereign |
| `air_gapped` | Disconnected enclave | blocked | blocked | isolated local |

## Control surfaces

The sovereign control plane enforces:

1. deployment mode;
2. data residency;
3. external network posture;
4. cloud/object-storage posture;
5. allowed source types;
6. admin role requirements;
7. privileged-admin dual control;
8. reason and change-ticket requirements;
9. usage quotas without cloud billing;
10. privacy classification against principal clearance;
11. restricted operations;
12. append-only audit hash-chain events;
13. deployment attestation.

## Relationship to central ingestion

The central ingestion layer gives HYBA a common service contract for arbitrary data sources and sectors through `DataSourceSpec`, `ConnectorRegistry`, `DataIngestionService`, `IngestionEnvelope`, `DataQualityReport`, and lineage events.

The sovereign control plane wraps that ingestion service so HYBA can ingest only permitted data from permitted sources inside the permitted deployment boundary.

```text
Any data source
  -> DataSourceSpec
  -> SovereignControlPlane decision
  -> DataIngestionService
  -> IngestionEnvelope
  -> HYBA services
```

## Evidence posture

Every governed action can emit:

- a policy decision;
- allowed or denied reasons;
- controls applied;
- evidence seal;
- append-only audit event;
- previous event hash;
- deployment attestation.

This allows a customer, auditor, regulator, or security team to inspect the posture without relying on verbal assurances.

## Buyer-safe claims

HYBA can safely state:

```text
HYBA supports cloud, private-cloud, on-premise, sovereign-site, and air-gapped deployment profiles.

HYBA can enforce local data-residency, source restriction, usage, admin, and audit controls without requiring customer data to leave the deployment boundary.

HYBA blocks external ingestion and cloud object storage by default in local sovereign deployment modes.

HYBA can require dual control, reason codes, and authorised roles for privileged administrative actions.

HYBA can produce machine-readable deployment attestation and append-only audit evidence for inspection.
```

## Claim boundary

HYBA should not claim automatic accreditation, classified approval, or regulator certification simply because the control plane exists.

Correct formulation:

```text
HYBA provides the technical enforcement surfaces required to support sovereign, regulated, on-premise, and air-gapped deployment assessment. Accreditation remains a customer, regulator, and environment-specific process.
```

## Verification

```bash
pytest tests/test_central_data_ingestion.py -q
pytest tests/test_sovereign_deployment_control_plane.py -q
```
