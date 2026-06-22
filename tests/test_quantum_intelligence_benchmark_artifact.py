import json
from pathlib import Path

from reproducibility.benchmarks.quantum_intelligence_benchmark import run_benchmark


def test_quantum_intelligence_benchmark_artifact_contains_required_evidence_fields() -> None:
    report = run_benchmark("python quantum_intelligence_benchmark.py")

    assert report["commit_sha"]
    assert report["runtime_version"]["python"]
    assert report["command"] == "python quantum_intelligence_benchmark.py"
    assert report["environment"]["cpu_count"] is not None
    assert report["raw_json_output"]
    assert report["claim_boundary"]["category"] == "Quantum Intelligence benchmark evidence"

    names = {measurement["name"] for measurement in report["measurements"]}
    assert names == {
        "qi_query_latency",
        "evidence_sealing_latency",
        "metering_overhead",
        "phi_coherence_computation",
        "qae_qaoa_design_generation",
        "salamander_repair_proposal_generation",
    }
    for measurement in report["measurements"]:
        assert measurement["latency_ms"] >= 0
        assert measurement["output_hash"]
        assert measurement["raw_output"]
        assert measurement["claim_boundary"] == report["claim_boundary"]


def test_quantum_intelligence_benchmark_cli_writes_raw_json(tmp_path: Path) -> None:
    from reproducibility.benchmarks.quantum_intelligence_benchmark import main
    import sys

    output = tmp_path / "qi.json"
    original_argv = sys.argv
    try:
        sys.argv = ["quantum_intelligence_benchmark.py", "--output", str(output)]
        assert main() == 0
    finally:
        sys.argv = original_argv

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["benchmark"] == "Quantum Intelligence launch-rail proof"
    assert "artifact_hash" in payload
