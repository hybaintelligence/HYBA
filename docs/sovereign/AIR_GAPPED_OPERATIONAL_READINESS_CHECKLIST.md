# Air-Gapped HYBA Operational Readiness Checklist

## Purpose

This checklist converts HYBA's sovereign deployment posture into an operational acceptance process for air-gapped, on-premise, sovereign-site, defence, national-security, regulated, and critical-infrastructure environments.

## Phase 1: Deployment boundary

- [ ] Confirm target deployment mode is `air_gapped` or `sovereign_site`.
- [ ] Confirm no production customer data is used before environment acceptance.
- [ ] Confirm the deployment network has no unmanaged outbound internet route.
- [ ] Confirm DNS, package mirrors, container registries, and dependency sources are local or approved.
- [ ] Confirm time synchronisation source is approved for the enclave.
- [ ] Confirm local backup and restore paths do not cross the sovereign boundary.
- [ ] Confirm customer security team has reviewed the deployment topology.
- [ ] Confirm no external telemetry is enabled by default.
- [ ] Confirm no cloud object storage is configured unless explicitly approved.
- [ ] Confirm deployment attestation reports local data control and no required cloud dependency.

## Phase 2: Sovereign profile configuration

- [ ] Set `HYBA_DEPLOYMENT_MODE=air_gapped` or `HYBA_DEPLOYMENT_MODE=sovereign_site`.
- [ ] Set `HYBA_TENANT_ID`.
- [ ] Set `HYBA_JURISDICTION`.
- [ ] Set `HYBA_SITE_NAME`.
- [ ] Set `HYBA_DATA_RESIDENCY`.
- [ ] Set `HYBA_ALLOW_EXTERNAL_NETWORK=false`.
- [ ] Set `HYBA_ALLOW_CLOUD_STORAGE=false`.
- [ ] Set approved `HYBA_ALLOWED_SOURCE_TYPES`.
- [ ] Set any `HYBA_RESTRICTED_OPERATIONS`.
- [ ] Set `HYBA_IMMUTABLE_AUDIT=true`.

## Phase 3: Identity and admin controls

- [ ] Define local principal identity source.
- [ ] Define admin roles.
- [ ] Define auditor roles.
- [ ] Define operator roles.
- [ ] Define clearance/classification mapping.
- [ ] Require privileged-admin reason codes.
- [ ] Require dual control for privileged admin.
- [ ] Require change-ticket binding where the customer mandates it.
- [ ] Test denial for unauthorised admin mutation.
- [ ] Test approval for authorised privileged mutation with second approver.

## Phase 4: Data ingestion controls

- [ ] Confirm central ingestion is available locally.
- [ ] Confirm allowed source types match the site security policy.
- [ ] Test local record ingestion.
- [ ] Test local file ingestion.
- [ ] Test local SQL ingestion if permitted.
- [ ] Test SCADA/industrial ingestion only if approved.
- [ ] Confirm external HTTP/API ingestion is denied by default.
- [ ] Confirm cloud object storage ingestion is denied by default.
- [ ] Confirm source data residency mismatch is denied.
- [ ] Confirm principal clearance below source classification is denied.
- [ ] Confirm ingestion envelope includes lineage, quality report, and deployment control metadata.

## Phase 5: Usage governance

- [ ] Define daily ingestion quota.
- [ ] Define records-per-ingestion quota.
- [ ] Define records-per-day quota.
- [ ] Define workloads-per-day quota.
- [ ] Define privileged-admin-actions-per-day quota.
- [ ] Test quota acceptance below threshold.
- [ ] Test quota denial above threshold.
- [ ] Confirm usage snapshot can be inspected locally.
- [ ] Confirm usage enforcement does not depend on cloud billing.

## Phase 6: Audit and evidence

- [ ] Confirm every allowed action creates an audit event.
- [ ] Confirm every denied action creates an audit event where required.
- [ ] Confirm first event uses `genesis` previous hash.
- [ ] Confirm each later event links to the prior evidence seal.
- [ ] Confirm auditor role can export audit events.
- [ ] Confirm non-auditor cannot export audit events.
- [ ] Confirm deployment attestation is captured at acceptance.
- [ ] Confirm evidence seals are included in policy decisions.
- [ ] Confirm audit export format is accepted by customer security team.
- [ ] Confirm audit retention policy is documented.

## Phase 7: Workload execution readiness

- [ ] Confirm workload endpoints are reachable only inside the approved network.
- [ ] Confirm restricted operations are denied.
- [ ] Confirm allowed operations execute under policy.
- [ ] Confirm workload usage quota is enforced.
- [ ] Confirm workload outputs do not include unapproved egress.
- [ ] Confirm operational logs remain local.
- [ ] Confirm incident response process for denied or suspicious actions.

## Phase 8: Resilience and recovery

- [ ] Test restart of HYBA runtime.
- [ ] Test restoration of local configuration.
- [ ] Test audit log preservation.
- [ ] Test backup restore in isolated environment.
- [ ] Test degraded mode without external dependencies.
- [ ] Test local package/container redeployment.
- [ ] Confirm key rotation process.
- [ ] Confirm emergency admin break-glass process, if permitted.
- [ ] Confirm break-glass events are always audited.

## Phase 9: Acceptance tests

Minimum acceptance tests before sovereign go-live:

```text
1. deployment_attestation reports air_gapped or sovereign_site
2. external HTTP ingestion is denied
3. cloud object storage ingestion is denied
4. local records ingestion is allowed
5. data residency mismatch is denied
6. insufficient clearance is denied
7. unauthorised admin mutation is denied
8. privileged admin without second approver is denied
9. privileged admin with reason and second approver is allowed
10. audit export denied to non-auditor
11. audit export allowed to auditor
12. audit hash chain links correctly
13. local quotas are enforced
14. no cloud billing dependency is required
15. no customer data leaves the deployment boundary by default
```

## Verification commands

```bash
pytest tests/test_sovereign_deployment_control_plane.py -q
pytest tests/test_central_data_ingestion.py -q
```
