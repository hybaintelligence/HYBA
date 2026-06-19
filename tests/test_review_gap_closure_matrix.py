from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class GapClosure:
    gap_id: str
    category: str
    implementation_paths: tuple[str, ...]
    regression_tests: tuple[str, ...]
    evidence_or_gate_paths: tuple[str, ...]
    closure_boundary: str


GAP_CLOSURES = (
    GapClosure(
        gap_id="P0-QUANTUM-SOLVER-JOB-PLUMBING",
        category="quantum_solver_job_backed_fallback",
        implementation_paths=("python_backend/pythia_mining/dodecahedral_solver.py",),
        regression_tests=("tests/test_agent3_quantum_solvers.py", "tests/test_hendrix_phi_performance_benchmark.py"),
        evidence_or_gate_paths=("scripts/local_clean_10_gate.py",),
        closure_boundary="Proves job-aware local validation and graceful no-job fallback; not pool-side revenue.",
    ),
    GapClosure(
        gap_id="P0-HENDRIX-API-COMPATIBILITY",
        category="hendrix_phi_solver_api_stability",
        implementation_paths=("python_backend/pythia_mining/hendrix_phi_solver.py",),
        regression_tests=("tests/test_hendrix_phi_solver_contracts.py", "tests/test_hendrix_phi_performance_benchmark.py"),
        evidence_or_gate_paths=("scripts/local_clean_10_gate.py",),
        closure_boundary="Preserves start_nonce compatibility and bounded local benchmark claims.",
    ),
    GapClosure(
        gap_id="P1-IIT-PHI-BOUNDED-PROXY",
        category="iit_phi_runtime_proxy",
        implementation_paths=("python_backend/pythia_mining/iit_4_analyzer.py", "python_backend/pythia_mining/consciousness_engine.py"),
        regression_tests=("tests/test_iit_4_analyzer.py", "tests/test_iit_4_complete.py", "tests/test_iit_phi_mining_correlation.py"),
        evidence_or_gate_paths=("scripts/local_clean_10_gate.py", "scripts/evidence_boundary_report.py"),
        closure_boundary="Proves bounded diagnostic-proxy behaviour; not phenomenal consciousness or mining-performance validation.",
    ),
    GapClosure(
        gap_id="P2-API-JSON-SERIALIZATION",
        category="api_error_serialization",
        implementation_paths=("python_backend/hyba_genesis_api/core/api_posture.py",),
        regression_tests=("tests/test_api_posture_serialization.py", "tests/test_backend_mining_api.py"),
        evidence_or_gate_paths=("scripts/local_clean_10_gate.py",),
        closure_boundary="Proves validation and HTTPException details are JSON-safe.",
    ),
    GapClosure(
        gap_id="P2-FRONTEND-MINING-AUTH",
        category="frontend_mining_authorization_header",
        implementation_paths=("src/apiClient.ts",),
        regression_tests=("tests/test_bridge_security.test.ts",),
        evidence_or_gate_paths=("scripts/local_clean_10_gate.py",),
        closure_boundary="Proves authenticated client request path exists; browser token issuance remains an auth concern.",
    ),
    GapClosure(
        gap_id="P2-SECURITY-SWARM-SANITIZATION",
        category="security_swarm_syndrome_redaction",
        implementation_paths=("src/server.ts",),
        regression_tests=("tests/test_security_swarm_routes.test.ts",),
        evidence_or_gate_paths=("scripts/local_clean_10_gate.py",),
        closure_boundary="Proves HTTP response redaction; internal audit telemetry can retain detailed syndrome state.",
    ),
    GapClosure(
        gap_id="P3-CAPABILITY-REGISTRY",
        category="capability_registry_and_manifest",
        implementation_paths=("docs/ADAPTIVE_SYSTEMS_CAPABILITY_REGISTRY.md", "docs/evidence/claim_evidence_manifest.json"),
        regression_tests=("tests/test_adaptive_capability_registry.py", "tests/test_claim_evidence_manifest.py"),
        evidence_or_gate_paths=("scripts/local_clean_10_gate.py",),
        closure_boundary="Proves documentation/evidence coupling; does not independently validate scientific claims.",
    ),
    GapClosure(
        gap_id="LIVE-EMPIRICAL-PROOF",
        category="live_pool_and_commercial_claim_evidence",
        implementation_paths=("scripts/evidence_boundary_report.py",),
        regression_tests=("tests/test_evidence_boundary_report.py",),
        evidence_or_gate_paths=("artifacts/evidence_boundary", "artifacts/clean_10"),
        closure_boundary="GO requires artefacts; repository code alone must not claim revenue, hashrate advantage, or accepted shares.",
    ),
)


def test_every_review_gap_has_implementation_tests_and_gate() -> None:
    for gap in GAP_CLOSURES:
        assert gap.gap_id
        assert gap.category
        assert gap.closure_boundary
        assert gap.implementation_paths, gap.gap_id
        assert gap.regression_tests, gap.gap_id
        assert gap.evidence_or_gate_paths, gap.gap_id


def test_review_gap_paths_exist_or_are_artifact_directories() -> None:
    artifact_prefixes = ("artifacts/",)
    for gap in GAP_CLOSURES:
        for rel_path in gap.implementation_paths + gap.regression_tests + gap.evidence_or_gate_paths:
            path = ROOT / rel_path
            if rel_path.startswith(artifact_prefixes):
                # Artifact directories are generated by the local evidence gates.
                continue
            assert path.exists(), f"{gap.gap_id} references missing path: {rel_path}"


def test_live_empirical_gap_remains_claim_bounded_until_artifact_exists() -> None:
    live_gap = next(gap for gap in GAP_CLOSURES if gap.gap_id == "LIVE-EMPIRICAL-PROOF")

    assert "GO requires artefacts" in live_gap.closure_boundary
    assert "must not claim revenue" in live_gap.closure_boundary
    assert "tests/test_evidence_boundary_report.py" in live_gap.regression_tests


def test_iit_gap_is_registered_as_diagnostic_proxy_not_consciousness_claim() -> None:
    iit_gap = next(gap for gap in GAP_CLOSURES if gap.gap_id == "P1-IIT-PHI-BOUNDED-PROXY")

    assert "diagnostic-proxy" in iit_gap.closure_boundary
    assert "not phenomenal consciousness" in iit_gap.closure_boundary
    assert "tests/test_iit_4_complete.py" in iit_gap.regression_tests
