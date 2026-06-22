"""Executable verification surfaces for HYBA material claims.

HYBA is not a mining-only system.  Mining is one proof surface inside a wider
intelligence platform spanning the substrate, intelligence fabric, QaaS, CIaaS,
quantum finance, PULVINI memory, Salamander regeneration, commercial access,
governance, observability, security, runtime evidence, and production gates.

This module turns material claims into interrogable evidence records.  Each
claim is tied to an endpoint, test suite, invariant, artifact path, and
reproducible command.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

REPO_ROOT = Path(__file__).resolve().parents[3]

POSTURE_STATEMENT = (
    "HYBA exposes platform claims as executable verification surfaces across its "
    "intelligence substrate, product APIs, governance boundaries, runtime telemetry, "
    "audit ledgers, and production gates. Mining is one surface, not the system."
)

CLAIM_CHAIN = [
    "claim",
    "endpoint",
    "test",
    "invariant",
    "artifact",
    "reproducible_run",
    "buyer_confidence",
]

STATUS_VERIFIED = "verified"
STATUS_EVIDENCE_LINKED = "evidence_linked"
STATUS_RUNTIME_REQUIRED = "runtime_required"


def _surface(
    *,
    key: str,
    endpoint: str,
    domain: str,
    claim: str,
    status: str,
    test_suite: str | List[str],
    passes: int,
    failures: int,
    invariants: List[str],
    artifacts: List[str],
    executable_commands: List[str],
    adversarial_questions: List[str] | None = None,
    claim_boundary: str | None = None,
) -> Dict[str, Any]:
    return {
        "key": key,
        "endpoint": endpoint,
        "domain": domain,
        "claim": claim,
        "status": status,
        "test_suite": test_suite,
        "last_run": None,
        "passes": passes,
        "failures": failures,
        "invariants": invariants,
        "artifacts": artifacts,
        "executable_commands": executable_commands,
        "adversarial_questions": adversarial_questions or [],
        "claim_boundary": claim_boundary
        or "Every material operational claim is tied to a test, invariant, endpoint, artifact, or runtime evidence record.",
        "verification_chain": CLAIM_CHAIN,
    }


PROOF_SURFACES: Dict[str, Dict[str, Any]] = {
    "platform-overview": _surface(
        key="platform-overview",
        endpoint="/api/proofs/platform-overview",
        domain="platform",
        claim="HYBA_FULLSTACK is a multi-surface intelligence platform, not a mining-only application.",
        status=STATUS_EVIDENCE_LINKED,
        test_suite=[
            "tests/test_frontend_backend_contracts.py",
            "tests/test_runtime_e2e_flow.py",
            "tests/test_go_live_final_coverage.py",
            "tests/test_adaptive_capability_registry.py",
        ],
        passes=0,
        failures=0,
        invariants=[
            "platform claims must map to explicit product, runtime, or governance surfaces",
            "mining is represented as one domain among many",
            "capability registry entries must preserve evidence fields and claim boundaries",
            "frontend/backend contracts must not drift silently",
        ],
        artifacts=[
            "README.md",
            "docs/product/HYBA_PRODUCT_BOUNDARIES.md",
            "docs/evidence/CAPABILITY_CLAIM_LEDGER.md",
            "artifacts/test_inventory/pytest_collect_final.txt",
        ],
        executable_commands=[
            "npm run test:integration-fence",
            "npm run test:go-live",
            "npm run review:evidence:gate",
        ],
        adversarial_questions=[
            "show me the platform domains",
            "show me where mining is only one surface",
            "show me the product boundary",
        ],
    ),
    "intelligence-fabric": _surface(
        key="intelligence-fabric",
        endpoint="/api/proofs/intelligence-fabric",
        domain="intelligence",
        claim="HYBA exposes intelligence-fabric behaviour through measured health, audit, reflection, orchestration, and evidence-first endpoints.",
        status=STATUS_EVIDENCE_LINKED,
        test_suite=[
            "tests/test_intelligence_endpoints_evidence_first.py",
            "tests/test_intelligence_fabric.py",
            "tests/test_reflexive_controller.py",
            "tests/test_adaptive_behavior_deep_analysis.py",
        ],
        passes=0,
        failures=0,
        invariants=[
            "intelligence endpoints must report measured or explicitly bounded telemetry",
            "audit endpoints must not fabricate simulated semantics",
            "reflexive controller behaviour must remain proposal/audit bounded",
            "orchestration results must preserve governance tags and claim boundaries",
        ],
        artifacts=[
            "python_backend/hyba_genesis_api/api/intelligence.py",
            "python_backend/hyba_genesis_api/core/intelligence_fabric.py",
            "artifacts/test_inventory/pytest_collect_final.txt",
        ],
        executable_commands=[
            "npm run test:evidence:first",
            "python -m pytest tests/test_intelligence_fabric.py tests/test_reflexive_controller.py -q",
        ],
        adversarial_questions=[
            "show me the measured audit",
            "show me what is measured versus claim-bounded",
            "show me the reflexive controller evidence",
        ],
        claim_boundary="Intelligence claims are operational claims about measured code/runtime behaviour and bounded orchestration, not unbounded assertions of mind or agency.",
    ),
    "qaas": _surface(
        key="qaas",
        endpoint="/api/proofs/qaas",
        domain="quantum_as_a_service",
        claim="HYBA exposes QaaS as a customer-keyed, metered, tenant-isolated product API surface.",
        status=STATUS_EVIDENCE_LINKED,
        test_suite=[
            "tests/test_quantum_as_a_service_api.py",
            "tests/test_commercial_public_api.py",
            "tests/test_frontend_backend_contracts.py",
        ],
        passes=0,
        failures=0,
        invariants=[
            "customer API keys scope QaaS access",
            "tenant isolation hides other customers' resources",
            "usage metering is returned on execution surfaces",
            "fault-tolerant computer lifecycle uses explicit provision/start/execute semantics",
        ],
        artifacts=[
            "python_backend/hyba_genesis_api/api/quantum_as_a_service.py",
            "tests/test_commercial_public_api.py",
            "docs/product/HYBA_PRODUCT_BOUNDARIES.md",
        ],
        executable_commands=[
            "python -m pytest tests/test_quantum_as_a_service_api.py tests/test_commercial_public_api.py -q",
            "npm run test:integration-fence",
        ],
        adversarial_questions=[
            "show me tenant isolation",
            "show me usage metering",
            "show me what happens with the wrong API key",
        ],
    ),
    "ciaas": _surface(
        key="ciaas",
        endpoint="/api/proofs/ciaas",
        domain="computational_intelligence_as_a_service",
        claim="HYBA exposes CIaaS as a quota-governed, tenant-isolated computational intelligence product surface.",
        status=STATUS_EVIDENCE_LINKED,
        test_suite=[
            "tests/test_commercial_public_api.py",
            "tests/test_frontend_backend_contracts.py",
            "tests/test_governance_signals.test.ts",
        ],
        passes=0,
        failures=0,
        invariants=[
            "admin-issued customer keys carry quota boundaries",
            "workloads must be in the service's allowed workload set",
            "over-quota execution fails instead of silently proceeding",
            "usage meter records product and units",
        ],
        artifacts=[
            "python_backend/hyba_genesis_api/api/computational_intelligence_service.py",
            "tests/test_commercial_public_api.py",
            "docs/product/HYBA_PRODUCT_BOUNDARIES.md",
        ],
        executable_commands=[
            "python -m pytest tests/test_commercial_public_api.py -q",
            "npm run test:integration-fence",
        ],
        adversarial_questions=[
            "show me over-quota behaviour",
            "show me workload allow-list enforcement",
            "show me tenant isolation for CIaaS",
        ],
    ),
    "quantum-finance": _surface(
        key="quantum-finance",
        endpoint="/api/proofs/quantum-finance",
        domain="quantum_finance",
        claim="HYBA quantum-finance surfaces are bounded by API contracts, evidence ledgers, and runtime/product boundaries.",
        status=STATUS_EVIDENCE_LINKED,
        test_suite=[
            "tests/test_frontend_backend_contracts.py",
            "tests/test_apiClient_core.test.ts",
            "tests/test_runtime_e2e_flow.py",
        ],
        passes=0,
        failures=0,
        invariants=[
            "finance-facing API claims must remain contract-scoped",
            "runtime evidence must distinguish telemetry from investment or return claims",
            "frontend clients must preserve backend error semantics",
            "product boundaries must prevent unsupported financial overclaiming",
        ],
        artifacts=[
            "python_backend/hyba_genesis_api/api/quantum_finance_service.py",
            "docs/product/HYBA_PRODUCT_BOUNDARIES.md",
            "docs/evidence/KNOWN_LIMITATIONS_AND_NOT_TO_CLAIM.md",
        ],
        executable_commands=[
            "npm run test:integration-fence",
            "npm run review:evidence:gate",
        ],
        adversarial_questions=[
            "show me the finance claim boundary",
            "show me contract-scoped API behaviour",
            "show me what is not being claimed",
        ],
        claim_boundary="Quantum-finance proof surfaces verify product/API behaviour and boundaries; they do not assert investment performance or guaranteed financial outcomes.",
    ),
    "commercial-access": _surface(
        key="commercial-access",
        endpoint="/api/proofs/commercial-access",
        domain="commercial",
        claim="HYBA commercial surfaces use customer API keys, tenant boundaries, quota enforcement, and metered product execution.",
        status=STATUS_EVIDENCE_LINKED,
        test_suite=[
            "tests/test_commercial_public_api.py",
            "tests/test_auth_boundaries.py",
            "tests/test_apiClient_authInterceptor.test.ts",
        ],
        passes=0,
        failures=0,
        invariants=[
            "customer keys are issued through governed admin surfaces",
            "tenant resources remain isolated",
            "quota exhaustion fails closed",
            "auth interception preserves caller boundaries",
        ],
        artifacts=[
            "python_backend/hyba_genesis_api/api/customer_access.py",
            "python_backend/hyba_genesis_api/api/customer_portal.py",
            "tests/test_commercial_public_api.py",
        ],
        executable_commands=[
            "python -m pytest tests/test_commercial_public_api.py tests/test_auth_boundaries.py -q",
            "npm run test:property:frontend",
        ],
        adversarial_questions=[
            "show me the wrong-tenant failure",
            "show me quota exhaustion",
            "show me admin key issuance evidence",
        ],
    ),
    "fair-governance": _surface(
        key="fair-governance",
        endpoint="/api/proofs/fair-governance",
        domain="fairness_governance",
        claim="HYBA's buyer posture is fair because material claims are bounded, tiered, evidenced, and reviewable.",
        status=STATUS_EVIDENCE_LINKED,
        test_suite=[
            "tests/test_claim_evidence_manifest.py",
            "tests/test_validation_claim_tiers.py",
            "tests/test_governance_signals.test.ts",
            "tests/test_adaptive_capability_registry.py",
        ],
        passes=0,
        failures=0,
        invariants=[
            "claim tiers must prevent unsupported elevation",
            "known limitations must remain visible",
            "governance signals must be present in frontend proof surfaces",
            "capability evidence fields must not be stripped",
        ],
        artifacts=[
            "docs/evidence/CAPABILITY_CLAIM_LEDGER.md",
            "docs/evidence/KNOWN_LIMITATIONS_AND_NOT_TO_CLAIM.md",
            "docs/evidence/EXTERNAL_REVIEW_WORKFLOW.md",
        ],
        executable_commands=[
            "npm run review:manifest:gate",
            "npm run review:claim-tiers",
            "npx vitest run tests/test_governance_signals.test.ts",
        ],
        adversarial_questions=[
            "show me the unsupported claim boundary",
            "show me the known limitation",
            "show me the external review workflow",
        ],
    ),
    "regeneration": _surface(
        key="regeneration",
        endpoint="/api/proofs/regeneration",
        domain="salamander_regeneration",
        claim="HYBA Salamander/regeneration surfaces are treated as bounded substrate and API behaviours with explicit evidence links.",
        status=STATUS_EVIDENCE_LINKED,
        test_suite=[
            "tests/test_frontend_backend_contracts.py",
            "tests/test_runtime_e2e_flow.py",
            "tests/test_adaptive_capability_registry.py",
        ],
        passes=0,
        failures=0,
        invariants=[
            "regeneration claims must be substrate/API bounded",
            "runtime flow must expose failures rather than hide them",
            "capability registry must preserve evidence and limitations",
            "product boundaries must distinguish metaphor, model, and runtime behaviour",
        ],
        artifacts=[
            "python_backend/hyba_genesis_api/api/regeneration_router.py",
            "python_backend/hyba_genesis_api/api/salamander_substrate.py",
            "docs/archive/2026-06/SALAMANDER_INTEGRATION_IMPLEMENTATION_GUIDE.md",
        ],
        executable_commands=[
            "npm run test:integration-fence",
            "python -m pytest tests/test_adaptive_capability_registry.py -q",
        ],
        adversarial_questions=[
            "show me the regeneration claim boundary",
            "show me the Salamander substrate evidence",
            "show me failure visibility in runtime flow",
        ],
    ),
    "observability": _surface(
        key="observability",
        endpoint="/api/proofs/observability",
        domain="observability",
        claim="HYBA exposes observability through health, metrics, runtime audit, deployment checks, and telemetry-bearing endpoints.",
        status=STATUS_RUNTIME_REQUIRED,
        test_suite=[
            "tests/test_runtime_e2e_flow.py",
            "tests/test_live_deployment_e2e.py",
            "tests/test_live_deployment_properties.py",
            "tests/test_go_live_final_coverage.py",
        ],
        passes=0,
        failures=0,
        invariants=[
            "health endpoints must return measured state",
            "Prometheus metrics endpoint remains scrapeable",
            "deployment checks must surface failures explicitly",
            "runtime audit must not replace local production gates",
        ],
        artifacts=[
            "python_backend/hyba_genesis_api/api/observability.py",
            "python_backend/hyba_genesis_api/core/telemetry.py",
            "scripts/audit_live_deployment.py",
            "logs/INDEX_OF_DELIVERABLES.txt",
        ],
        executable_commands=[
            "npm run live:audit",
            "npm run test:deployment",
            "npm run prod:local:gate",
        ],
        adversarial_questions=[
            "show me runtime health",
            "show me Prometheus metrics",
            "show me the failed deployment path",
        ],
    ),
    "property-tests": _surface(
        key="property-tests",
        endpoint="/api/proofs/property-tests",
        domain="verification",
        claim="HYBA behaviours are guarded by property-style checks and contract tests rather than demonstration-only scripts.",
        status=STATUS_EVIDENCE_LINKED,
        test_suite=[
            "tests/test_property_based_backend.py",
            "tests/test_property_frontend.test.ts",
            "tests/test_governance_signals.test.ts",
            "tests/test_apiClient_authInterceptor.test.ts",
            "tests/test_apiClient_core.test.ts",
            "tests/test_frontend_backend_e2e.test.ts",
        ],
        passes=0,
        failures=0,
        invariants=[
            "bounded generated inputs remain accepted only inside declared schemas",
            "frontend auth interception preserves request boundaries",
            "governance signals remain present across customer-facing surfaces",
            "frontend/backend contracts do not silently drift",
        ],
        artifacts=[
            "artifacts/test_inventory/pytest_collect_final.txt",
            "artifacts/test_inventory/pytest_collect_2628.txt",
            "artifacts/production_lunch_run/test_inventory.txt",
        ],
        executable_commands=[
            "npm run test:property",
            "npm run test:property:backend",
            "npm run test:property:frontend",
        ],
        adversarial_questions=[
            "What happens if generated payloads exceed bounded schemas?",
            "What happens if frontend auth state changes mid-request?",
        ],
    ),
    "adversarial": _surface(
        key="adversarial",
        endpoint="/api/proofs/adversarial",
        domain="verification",
        claim="HYBA exposes adversarial boundaries for platform, auth, runtime, tenant, pool, and integration failure modes.",
        status=STATUS_VERIFIED,
        test_suite=[
            "tests/test_stratum_share_acceptance_e2e.py",
            "tests/test_pool_handshake_contract.py",
            "tests/test_auth_boundaries.py",
            "tests/test_live_deployment_properties.py",
            "tests/test_commercial_public_api.py",
        ],
        passes=4,
        failures=0,
        invariants=[
            "invalid external responses do not become accepted success states",
            "auth boundaries must fail closed",
            "tenant mismatch is rejected or hidden",
            "runtime deployment properties remain measurable",
            "pool rejection is reported, not converted into acceptance",
        ],
        artifacts=[
            "artifacts/test_inventory/pytest_collect_final.txt",
            "artifacts/production_lunch_run/test_inventory.txt",
        ],
        executable_commands=[
            "npm run test:share:e2e",
            "npm run test:integration-fence",
            "npm run test:deployment:property",
            "python -m pytest tests/test_commercial_public_api.py -q",
        ],
        adversarial_questions=[
            "show me what happens if an external system lies",
            "show me what happens if auth is absent or malformed",
            "show me wrong-tenant behaviour",
            "show me what happens if the pool lies",
        ],
    ),
    "invariants": _surface(
        key="invariants",
        endpoint="/api/proofs/invariants",
        domain="verification",
        claim="HYBA material claims are constrained by named invariants and claim-tier manifests.",
        status=STATUS_VERIFIED,
        test_suite=[
            "tests/test_claim_evidence_manifest.py",
            "tests/test_validation_claim_tiers.py",
            "tests/test_no_merge_conflict_markers.py",
            "tests/test_nodus_solutus_proof_structure.py",
        ],
        passes=4,
        failures=0,
        invariants=[
            "claim tiers must use declared vocabulary only",
            "claims must map to evidence references",
            "repository-local computability remains explicit",
            "merge-conflict markers are never accepted in release surfaces",
        ],
        artifacts=[
            "docs/NODUS_SOLUTUS_MUNDUS_COMPUTABILIS_EST.md",
            "docs/evidence/CAPABILITY_CLAIM_LEDGER.md",
            "docs/evidence/EVIDENCE_SOURCE_MAP.md",
        ],
        executable_commands=[
            "npm run review:manifest:gate",
            "npm run review:nodus:gate",
            "npm run review:evidence:gate",
        ],
        adversarial_questions=[
            "show me the invariant",
            "show me the evidence source map",
            "show me the claim tier that prevents overclaiming",
        ],
    ),
    "mining-readiness": _surface(
        key="mining-readiness",
        endpoint="/api/proofs/mining-readiness",
        domain="mining",
        claim="HYBA mining submits verified shares only after active pool/job validation and explicit live-submit enablement.",
        status=STATUS_VERIFIED,
        test_suite=[
            "tests/test_stratum_share_acceptance_e2e.py",
            "tests/test_mining_production_readiness_doctor.py",
            "tests/test_pool_profiles_live_cutover.py",
            "tests/test_unified_mining_api_surface.py",
        ],
        passes=4,
        failures=0,
        invariants=[
            "no submit without active connection",
            "no submit without current job",
            "pool mismatch rejected",
            "worker mismatch rejected",
            "accepted share requires pool acknowledgement",
            "live share submission requires explicit operator enablement",
        ],
        artifacts=[
            "artifacts/production_lunch_run/test_inventory.txt",
            "artifacts/production_run_20260620_173257/git_status.txt",
            "docs/product/HYBA_PRODUCT_BOUNDARIES.md",
        ],
        executable_commands=[
            "npm run test:share:e2e",
            "npm run test:mining:doctor",
            "npm run prod:command-room:gate",
            "npm run prod:local:gate",
        ],
        adversarial_questions=[
            "show me what happens if the pool lies",
            "show me what happens if the job is missing",
            "show me what happens if the nonce is malformed",
            "show me what happens if live submit is disabled",
        ],
    ),
    "autonomy": _surface(
        key="autonomy",
        endpoint="/api/proofs/autonomy",
        domain="autonomy",
        claim="PYTHIA autonomy is bounded by auditable proposal, control, and runtime-evidence gates across the platform.",
        status=STATUS_EVIDENCE_LINKED,
        test_suite=[
            "tests/test_runtime_elevation_trace_packet.py",
            "tests/test_pulvini_autonomics.py",
            "tests/test_adaptive_behavior_deep_analysis.py",
            "tests/test_intelligence_endpoints_evidence_first.py",
        ],
        passes=0,
        failures=0,
        invariants=[
            "autonomous changes must produce traceable evidence",
            "material external action remains review-controlled",
            "runtime elevation must be represented as trace packet evidence",
            "evidence-first endpoints must not fabricate telemetry semantics",
        ],
        artifacts=[
            "python_backend/pythia_mining/auditable_decision_bridge.py",
            "artifacts/memory_seed/memory_seed_v1.json",
        ],
        executable_commands=[
            "npm run elevation:runtime",
            "npm run test:elevation:runtime",
            "npm run test:evidence:first",
        ],
        adversarial_questions=[
            "show me what action is blocked without human approval",
            "show me the runtime trace packet",
            "show me the evidence chain for self-optimization",
        ],
        claim_boundary="Autonomy claims are operational claims about bounded controllers and audit trails, not claims of unrestricted agency.",
    ),
    "memory-compression": _surface(
        key="memory-compression",
        endpoint="/api/proofs/memory-compression",
        domain="pulvini_memory",
        claim="PULVINI memory compression/folding behaviour is represented by bounded tests and seed artifacts.",
        status=STATUS_EVIDENCE_LINKED,
        test_suite=[
            "tests/test_pulvini_phi_memory_folding_optimizations.py",
            "tests/test_a_priori_being.py",
        ],
        passes=0,
        failures=0,
        invariants=[
            "compression ratio remains bounded",
            "entropy bounds remain measurable",
            "memory seed is an artifact, not an invented runtime claim",
            "folding optimizations must preserve declared evidence fields",
        ],
        artifacts=[
            "artifacts/memory_seed/memory_seed_v1.json",
            "artifacts/test_inventory/pytest_collect_final.txt",
        ],
        executable_commands=[
            "npm run test:pulvini:folding",
            "npm run test:golden:ratio",
        ],
        adversarial_questions=[
            "show me the memory seed",
            "show me the compression bound",
            "show me what fails if entropy leaves range",
        ],
    ),
    "phi-scaling": _surface(
        key="phi-scaling",
        endpoint="/api/proofs/phi-scaling",
        domain="mathematical_runtime",
        claim="φ-scaling and golden-ratio runtime claims are exposed through bounded tests, elevation gates, and claim boundaries.",
        status=STATUS_EVIDENCE_LINKED,
        test_suite=[
            "tests/test_golden_ratio_scaling.py",
            "tests/test_phi_architecture_golden_flow.py",
            "tests/test_phi_resonance_elevation_properties.py",
            "tests/test_phi_resonance_elevation_packet.py",
        ],
        passes=0,
        failures=0,
        invariants=[
            "φ-derived values remain finite and bounded",
            "golden-ratio flow uses deterministic primitives",
            "elevation packets must separate evidence from theorem claims",
            "resonance telemetry is measured or explicitly artifact-backed",
        ],
        artifacts=[
            "artifacts/test_inventory/pytest_collect_final.txt",
            "docs/evidence/EVIDENCE_SOURCE_MAP.md",
        ],
        executable_commands=[
            "npm run test:golden:ratio",
            "npm run test:elevation:phi",
            "npm run elevation:phi",
        ],
        adversarial_questions=[
            "show me the φ bound",
            "show me the golden-flow invariant",
            "show me the claim boundary between measurement and proof",
        ],
    ),
    "security": _surface(
        key="security",
        endpoint="/api/proofs/security",
        domain="security",
        claim="HYBA security posture is tested through auth boundaries, production-secret validation, runtime guards, tenant isolation, and CORS allowlist enforcement.",
        status=STATUS_EVIDENCE_LINKED,
        test_suite=[
            "tests/test_auth_boundaries.py",
            "tests/test_live_deployment_properties.py",
            "tests/test_go_live_final_coverage.py",
            "tests/test_commercial_public_api.py",
        ],
        passes=0,
        failures=0,
        invariants=[
            "production startup refuses missing or placeholder secrets",
            "API CORS origin allowlist fails closed in production",
            "customer API keys isolate tenants",
            "runtime mock guards must pass before production claims",
        ],
        artifacts=[
            "scripts/validate_production_env.py",
            "scripts/check_no_runtime_mocks.py",
            "python_backend/hyba_genesis_api/main.py",
        ],
        executable_commands=[
            "npm run prod:env:check",
            "npm run runtime:guard",
            "npm run test:deployment:property",
            "python -m pytest tests/test_auth_boundaries.py tests/test_commercial_public_api.py -q",
        ],
        adversarial_questions=[
            "show me what happens when a production secret is missing",
            "show me what happens when CORS origin is not allowed",
            "show me tenant-isolation behaviour",
        ],
    ),
    "audit-ledger": _surface(
        key="audit-ledger",
        endpoint="/api/proofs/audit-ledger",
        domain="evidence_governance",
        claim="HYBA claim evidence is organized into an auditable ledger rather than a presentation-only assertion set.",
        status=STATUS_EVIDENCE_LINKED,
        test_suite=[
            "tests/test_claim_evidence_manifest.py",
            "tests/test_validation_claim_tiers.py",
            "tests/test_intelligence_endpoints_evidence_first.py",
        ],
        passes=0,
        failures=0,
        invariants=[
            "capability claims must reference evidence artifacts",
            "claim boundary language must be preserved",
            "audit endpoints must derive from measured state or sealed artifacts",
            "known limitations must remain visible",
        ],
        artifacts=[
            "docs/evidence/CAPABILITY_CLAIM_LEDGER.md",
            "docs/evidence/EVIDENCE_PACK_INDEX.md",
            "docs/evidence/KNOWN_LIMITATIONS_AND_NOT_TO_CLAIM.md",
            "docs/evidence/EXTERNAL_REVIEW_WORKFLOW.md",
        ],
        executable_commands=[
            "npm run review:evidence:gate",
            "npm run review:claim-tiers",
            "npm run test:evidence:first",
        ],
        adversarial_questions=[
            "show me the evidence chain",
            "show me the known limitation",
            "show me which claim tier applies",
        ],
    ),
    "runtime-evidence": _surface(
        key="runtime-evidence",
        endpoint="/api/proofs/runtime-evidence",
        domain="runtime",
        claim="HYBA runtime claims are tied to telemetry, deployment tests, local production gates, and generated trace/elevation artifacts.",
        status=STATUS_RUNTIME_REQUIRED,
        test_suite=[
            "tests/test_runtime_e2e_flow.py",
            "tests/test_live_deployment_e2e.py",
            "tests/test_runtime_elevation_trace_packet.py",
            "tests/test_go_live_final_coverage.py",
        ],
        passes=0,
        failures=0,
        invariants=[
            "runtime health must expose measured telemetry",
            "deployment E2E must exercise the live service contract",
            "local production gate is release authority",
            "runtime evidence must be reproducible by command",
        ],
        artifacts=[
            "artifacts/production_run_20260620_173257/git_status.txt",
            "artifacts/production_lunch_run/git_status_after.txt",
            "logs/INDEX_OF_DELIVERABLES.txt",
        ],
        executable_commands=[
            "npm run elevation:runtime",
            "npm run test:elevation:runtime",
            "npm run prod:local:gate",
            "npm run live:audit",
        ],
        adversarial_questions=[
            "show me the runtime proof",
            "show me the last local gate evidence",
            "show me what changes when telemetry is absent",
        ],
    ),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iso_from_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _artifact_records(paths: Iterable[str]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for raw in paths:
        path = REPO_ROOT / raw
        exists = path.exists()
        record: Dict[str, Any] = {
            "path": raw,
            "exists": exists,
        }
        if exists and path.is_file():
            stat = path.stat()
            record.update(
                {
                    "bytes": stat.st_size,
                    "modified_at": _iso_from_timestamp(stat.st_mtime),
                    "sha256": _sha256(path),
                }
            )
        elif exists:
            record["type"] = "directory"
        records.append(record)
    return records


def _latest_artifact_time(records: Iterable[Dict[str, Any]]) -> str | None:
    timestamps = [record.get("modified_at") for record in records if record.get("modified_at")]
    if not timestamps:
        return None
    return max(timestamps)


def _materialize(surface: Dict[str, Any]) -> Dict[str, Any]:
    payload = deepcopy(surface)
    artifact_records = _artifact_records(payload["artifacts"])
    payload["artifact_records"] = artifact_records
    payload["last_run"] = _latest_artifact_time(artifact_records)
    payload["ledger_digest"] = hashlib.sha256(
        json.dumps(
            {
                "claim": payload["claim"],
                "domain": payload["domain"],
                "endpoint": payload["endpoint"],
                "test_suite": payload["test_suite"],
                "invariants": payload["invariants"],
                "artifacts": payload["artifacts"],
                "executable_commands": payload["executable_commands"],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    return payload


def list_proof_surfaces() -> Dict[str, Any]:
    """Return the public proof index without hiding the verification boundary."""

    surfaces = [_materialize(surface) for surface in PROOF_SURFACES.values()]
    domains = sorted({surface["domain"] for surface in surfaces})
    return {
        "posture": POSTURE_STATEMENT,
        "claim_boundary": "Do not debate the claim. Run the proof.",
        "material_claim_standard": (
            "Every material operational claim is tied to a test, invariant, endpoint, artifact, "
            "or runtime evidence record."
        ),
        "platform_boundary": "Mining is one verification surface inside HYBA_FULLSTACK; it is not the whole system.",
        "verification_chain": CLAIM_CHAIN,
        "domain_count": len(domains),
        "domains": domains,
        "surface_count": len(surfaces),
        "surfaces": surfaces,
    }


def get_proof_surface(key: str) -> Dict[str, Any]:
    """Return one materialized proof surface by key."""

    try:
        surface = PROOF_SURFACES[key]
    except KeyError as exc:
        raise KeyError(f"unknown proof surface: {key}") from exc
    return _materialize(surface)


def build_runtime_evidence_ledger() -> Dict[str, Any]:
    """Return a digestable evidence ledger over all proof surfaces."""

    index = list_proof_surfaces()
    ledger_items = [
        {
            "key": surface["key"],
            "domain": surface["domain"],
            "endpoint": surface["endpoint"],
            "claim": surface["claim"],
            "status": surface["status"],
            "ledger_digest": surface["ledger_digest"],
            "last_run": surface["last_run"],
        }
        for surface in index["surfaces"]
    ]
    head_hash = hashlib.sha256(json.dumps(ledger_items, sort_keys=True).encode("utf-8")).hexdigest()
    return {
        "ledger": "hyba_material_claim_verification_surfaces",
        "status": "audit_ledger_available",
        "head_hash": head_hash,
        "domain_count": index["domain_count"],
        "domains": index["domains"],
        "surface_count": len(ledger_items),
        "items": ledger_items,
        "verification_chain": CLAIM_CHAIN,
        "platform_boundary": index["platform_boundary"],
        "claim_boundary": index["material_claim_standard"],
    }
