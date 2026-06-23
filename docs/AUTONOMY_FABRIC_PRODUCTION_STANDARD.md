# HYBA Autonomy Fabric Production Standard

## BLUF

HYBA autonomy is now a platform contract, not a set of isolated features.

Every client-facing surface must make the same operating loop visible:

```text
observe -> reason -> recommend -> simulate -> approve -> execute -> audit -> learn
```

The implementation added for this standard is:

- `python_backend/hyba_genesis_api/core/autonomy_fabric.py`
- `python_backend/hyba_genesis_api/api/proofs.py` endpoints:
  - `GET /api/proofs/autonomy-fabric`
  - `GET /api/proofs/client-intelligence-brief`
  - `POST /api/proofs/autonomy-fabric/simulate`
  - `POST /api/proofs/autonomy-fabric/execute`
- `src/components/HybaIntelligenceRail.tsx`
- `src/components/SovereignCommandPost.tsx` integration
- `tests/test_autonomy_fabric_contract.py`
- `tests/test_autonomy_ubiquity_contract.test.ts`

## Product standard

Every major HYBA module must answer six questions on behalf of the client:

```text
What is HYBA seeing?
What does HYBA recommend?
What can HYBA safely automate?
What requires approval?
What evidence supports the recommendation?
What audit trail will be produced?
```

## Risk rule

HYBA may run low-risk read-only or advisory actions autonomously, but those actions still need audit evidence.

HYBA must not silently execute high-impact actions. High-risk actions require simulation first, then explicit approval or dual control, then an audit event.

High-risk examples include:

- production execution changes;
- privileged admin mutation;
- funding disbursement;
- customer data export;
- externally material deployment changes;
- production mining start/stop/share-submission paths.

## Client value workflows

The canonical autonomy fabric defines these initial surfaces:

1. client onboarding diagnostic;
2. opportunity scan;
3. sovereign runtime controls;
4. proof and claim interrogation;
5. production execution guardrails;
6. PYTHIA bounded self-optimization.

Each surface must include:

- `client_value`
- `observation`
- `insight`
- `recommendation`
- `risk`
- `confidence`
- `available_actions`
- `approval_required`
- `evidence`
- `audit_event`
- `evidence_seal`

## Buyer posture

HYBA should not ask buyers to believe the system.

HYBA should invite buyers to interrogate the system:

```text
query the endpoint
inspect the evidence seal
simulate the action
verify the approval boundary
run the test
read the audit trail
```

## Verification commands

```bash
PYTHONPATH=python_backend pytest tests/test_autonomy_fabric_contract.py -q
npx vitest run tests/test_autonomy_ubiquity_contract.test.ts
```

The tests enforce that autonomy is useful, evidenced, approval-safe, and visible in the client-facing command post.
