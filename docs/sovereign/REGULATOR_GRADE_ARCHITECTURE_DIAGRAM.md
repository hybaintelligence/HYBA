# HYBA Regulator-Grade Architecture Diagram

## Purpose

This document gives regulators, security reviewers, customer assurance teams, and sovereign-cloud onboarding teams a concise view of HYBA's governance boundary.

## Control-plane architecture

```mermaid
flowchart TD
    A[User or Service Request] --> B[PrincipalContext]
    B --> C[SovereignDeploymentProfile]
    C --> D[SovereignControlPlane]

    D --> E{Policy Decision}

    E -->|Allowed| F[Evidence Seal]
    E -->|Denied| G[Denied Decision + Reasons]

    F --> H[Append-only Audit Event]
    G --> H
    H --> I[Audit Hash Chain]

    F --> J{Action Type}
    J --> K[Central Data Ingestion]
    J --> L[Workload Execution]
    J --> M[Admin Mutation]
    J --> N[Audit Export]
    J --> O[Policy Change]

    K --> P[IngestionEnvelope]
    P --> Q[HYBA Services]
    Q --> R[Optimisation / Intelligence / Dashboards / Evidence]

    C --> S[Deployment Attestation]
    S --> T[Regulator / Auditor / Customer Security Team]
```

## Sovereign data-boundary view

```mermaid
flowchart LR
    subgraph Customer_Site[Customer sovereign site / secure facility]
        A[Local Data Sources]
        B[HYBA Runtime]
        C[SovereignControlPlane]
        D[Central Ingestion]
        E[HYBA Workloads]
        F[Local Audit Hash Chain]
        G[Local Admin Console]
    end

    subgraph External_World[External world]
        H[Cloud Object Storage]
        I[External APIs]
        J[Third-party Telemetry]
        K[HYBA Managed Cloud]
    end

    A --> C
    G --> C
    C --> D
    D --> E
    C --> F
    E --> F

    H -. blocked by default in sovereign/on-prem .- C
    I -. blocked by default in sovereign/on-prem .- C
    J -. not required .- C
    K -. not required for local sovereign mode .- B
```

## Regulator inspection points

| Inspection point | Question answered |
|---|---|
| `PrincipalContext` | Who is acting, with what role and clearance? |
| `SovereignDeploymentProfile` | Where is HYBA running, and which deployment restrictions apply? |
| `SovereignControlPlane` | Was the action allowed, denied, sealed, and audited? |
| Evidence seal | Can the decision be identified and verified? |
| Audit hash chain | Is the event sequence tamper-evident? |
| `IngestionEnvelope` | What was ingested, from where, under which lineage and quality report? |
| Deployment attestation | Can HYBA prove its active deployment posture? |

## Architecture claim

```text
HYBA separates deployment governance from workload logic.

Ingestion, workloads, and administrative actions do not execute merely because an endpoint was called. They pass through a local sovereign control plane that evaluates principal, deployment mode, source type, data residency, usage quota, admin privilege, and audit requirements before allowing execution.
```

## Control-plane sequence

```mermaid
sequenceDiagram
    participant Caller
    participant PrincipalContext
    participant Profile as SovereignDeploymentProfile
    participant Control as SovereignControlPlane
    participant Audit as Audit Hash Chain
    participant Ingestion as Central Ingestion

    Caller->>PrincipalContext: Present identity, roles, clearance
    PrincipalContext->>Profile: Resolve deployment constraints
    Profile->>Control: Evaluate action context
    Control->>Control: Check residency, source type, roles, quotas, restrictions
    Control->>Audit: Append allowed or denied decision
    alt Allowed
        Control->>Ingestion: Permit governed operation
        Ingestion-->>Control: IngestionEnvelope
        Control->>Audit: Append completion evidence
        Control-->>Caller: Result + deployment_control metadata
    else Denied
        Control-->>Caller: Denial + reasons + evidence seal
    end
```
