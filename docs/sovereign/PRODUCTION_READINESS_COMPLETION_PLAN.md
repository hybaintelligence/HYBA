# HYBA Sovereign Production Readiness Completion Plan

## Status

Central ingestion and sovereign deployment controls are merged into `main` through PR #176 and PR #177. The code, tests, and buyer/operator documentation now exist in the repository.

This document defines the remaining gates before HYBA should be described as production-ready for a sovereign customer deployment.

## Non-negotiable production gates

HYBA is not production-ready for sovereign deployment until all of the following are true:

1. CI is green on `main`.
2. Production Readiness workflow is green on `main`.
3. Frontend CI is green on `main`.
4. Supply Chain Security is green on `main`.
5. Build verification is green on `main`.
6. Sovereign acceptance tests pass in CI.
7. Air-gapped readiness checklist is executed in a representative environment.
8. Deployment attestation is captured from that environment.
9. Audit hash-chain export is verified by a security/audit role.
10. A named owner signs the go/no-go record.

## Current implementation already merged

- `python_backend/hyba_ciaas/ingestion.py`
- `python_backend/hyba_ciaas/sovereign_runtime.py`
- `tests/test_central_data_ingestion.py`
- `tests/test_sovereign_deployment_control_plane.py`
- `docs/CENTRAL_DATA_INGESTION.md`
- `docs/SOVEREIGN_DEPLOYMENT_CONTROL_PLANE.md`
- `docs/sovereign/*`

## CI status observed after merge

The merged sovereign head commit triggered repository workflows, but the connector reported failures across:

- CI
- Production Readiness
- Frontend CI
- Supply Chain Security
- Build verification

Detailed logs were not retrievable through the connector at the time this document was written. Until these are resolved, the correct status is:

```text
Production foundation: implemented
Merged to main: yes
Production-ready: not yet
Reason: repository CI and production gates are red
```

## Production hardening tasks

### 1. Dedicated sovereign CI gate

Add a narrow CI job that installs only the sovereign/ingestion runtime requirements and runs:

```bash
PYTHONPATH=python_backend pytest \
  tests/test_central_data_ingestion.py \
  tests/test_sovereign_deployment_control_plane.py \
  -q
```

This isolates the sovereign foundation from unrelated frontend/mining workflow failures and gives reviewers a clear pass/fail signal.

### 2. Runtime import smoke

Validate that the package exports work from repository root:

```bash
PYTHONPATH=python_backend python - <<'PY'
from hyba_ciaas import (
    DataSourceSpec,
    DeploymentMode,
    PrincipalContext,
    SovereignControlPlane,
    SovereignDeploymentProfile,
    create_default_ingestion_service,
)
print('sovereign import smoke passed')
PY
```

### 3. Air-gapped default-deny smoke

Validate that `air_gapped` blocks external network and cloud storage source types by default.

### 4. Attestation smoke

Validate that local sovereign modes report:

- `data_control_plane=local`
- `customer_data_leaves_site_by_default=false`
- `cloud_dependency_required=false`
- `audit_log_mode=append_only_hash_chain`

### 5. Evidence export smoke

Validate that:

- auditor role can export audit events;
- non-auditor role cannot export audit events;
- event 0 has `previous_hash=genesis`;
- event 1 links to event 0's evidence seal.

## Go/no-go rubric

| Gate | Required result | Status |
|---|---|---|
| Central ingestion merged | yes | done |
| Sovereign control plane merged | yes | done |
| Buyer/operator docs committed | yes | done |
| Dedicated sovereign CI gate | green | pending |
| Repository CI | green | pending |
| Production Readiness workflow | green | pending |
| Frontend CI | green | pending |
| Supply Chain Security | green | pending |
| Build verification | green | pending |
| Air-gapped checklist executed | signed | pending |
| External audit/accreditation | customer-specific | not claimed |

## Executive answer

HYBA now has a real sovereign deployment foundation in `main`, not just narrative. However, production readiness requires green CI and execution of the operational acceptance checklist. Until then, HYBA should be positioned as:

> Sovereign foundation implemented and merged; production acceptance in progress.
