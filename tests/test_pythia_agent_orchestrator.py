"""Production/adversarial tests for PYTHIA agent orchestration.

The orchestrator is allowed to spawn work and route quantum-native tasks through
HYBA/PYTHIA executors, but every result must be sealed evidence. These tests
prove bounded mathematics, deterministic packet chains, failure-to-Salamander
repair routing, hostile executor rejection, and no auto-apply bypass.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PY_BACKEND = ROOT / "python_backend"
if str(PY_BACKEND) not in sys.path:
    sys.path.insert(0, str(PY_BACKEND))

from pythia_agents import (  # noqa: E402
    PythiaAgentInvariantError,
    PythiaAgentOrchestrator,
    PythiaMathematicalQuantumExecutor,
    QuantumTask,
    verify_sealed_packet,
)


def _orchestrator() -> PythiaAgentOrchestrator:
    orchestrator = PythiaAgentOrchestrator(max_workers_limit=8)
    orchestrator.register_builtin_agent("math")
    return orchestrator


def test_phi_weighted_consensus_properties_are_bounded_and_sealed() -> None:
    orchestrator = _orchestrator()
    tasks = orchestrator.spawn_tasks(
        base_description="phi consensus",
        operation="phi_weighted_consensus",
        task_payloads=[{"scores": [0.2, 0.5, 0.8], "phi_exponent": 1.0}],
    )

    packets = orchestrator.run_entangled_group(
        agent_name="math", tasks=tasks, shared_state={"phi_context": "golden"}
    )
    packet = packets[0]
    result = packet["body"]["result"]

    assert verify_sealed_packet(packet) is True
    assert packet["body"]["status"] == "EXECUTION_STAGED"
    assert 0.0 <= result["harmonic_score"] <= 1.0
    assert 0.0 <= result["coherence"] <= 1.0
    assert abs(sum(result["weights"]) - 1.0) < 1e-12
    assert packet["body"]["auto_apply"] is False
    assert packet["body"]["source_modified"] is False
    assert packet["body"]["stable_core_modified"] is False


def test_ising_energy_matches_exhaustive_manual_formula() -> None:
    executor = PythiaMathematicalQuantumExecutor()
    fields = {"z0": 0.5, "z1": -0.25}
    couplers = {"z0z1": 1.5}
    for bitstring in ("00", "01", "10", "11"):
        response = executor(
            {
                "operation": "ising_energy",
                "fields": fields,
                "couplers": couplers,
                "constant": 0.125,
                "bitstring": bitstring,
            }
        )
        spins = {f"z{i}": 1 if bit == "1" else -1 for i, bit in enumerate(bitstring)}
        expected = (
            0.125
            + fields["z0"] * spins["z0"]
            + fields["z1"] * spins["z1"]
            + couplers["z0z1"] * spins["z0"] * spins["z1"]
        )
        assert response["result"]["energy"] == pytest.approx(expected)
        assert response["evidence"]["finite"] is True


def test_amplitude_expectation_qae_accounting_is_quadratic_and_finite() -> None:
    executor = PythiaMathematicalQuantumExecutor()
    response = executor(
        {
            "operation": "amplitude_expectation",
            "samples": [0.1, 0.2, 0.4, 0.8, 0.9],
            "precision_epsilon": 0.05,
        }
    )
    result = response["result"]

    assert result["variance"] >= 0.0
    assert (
        result["classical_samples_for_epsilon"]
        >= result["qae_oracle_calls_for_epsilon"]
    )
    assert result["quadratic_speedup_factor"] >= 1.0
    assert response["evidence"]["speedup_class"] == "quadratic_sampling_accounting"


def test_density_matrix_invariant_check_accepts_trace_one_hermitian_state() -> None:
    executor = PythiaMathematicalQuantumExecutor()
    response = executor(
        {
            "operation": "density_matrix_invariants",
            "matrix": [[0.5, [0.0, 0.0]], [[0.0, 0.0], 0.5]],
        }
    )

    assert response["result"]["density_matrix_invariant_ok"] is True
    assert response["result"]["trace_error"] <= 1e-9
    assert response["result"]["hermitian_error"] <= 1e-9


def test_multi_agent_parallel_outputs_deterministic_verified_chains() -> None:
    orchestrator = _orchestrator()
    task_a = QuantumTask.create(
        description="a",
        operation="phi_weighted_consensus",
        payload={"scores": [0.4, 0.6]},
    )
    task_b = QuantumTask.create(
        description="b",
        operation="phi_weighted_consensus",
        payload={"scores": [0.1, 0.9]},
    )

    first = orchestrator.run_multi_agent_parallel(
        {"math": [task_b, task_a]}, shared_state={"shared": "state"}
    )
    second = orchestrator.run_multi_agent_parallel(
        {"math": [task_a, task_b]}, shared_state={"shared": "state"}
    )

    assert [p["body"]["task_id"] for p in first["math"]] == sorted(
        [task_a.task_id, task_b.task_id]
    )
    assert [p["cryptographic_seal"]["body_hash"] for p in first["math"]] == [
        p["cryptographic_seal"]["body_hash"] for p in second["math"]
    ]
    assert orchestrator.verify_packet_sequence(first["math"]) is True
    assert all(verify_sealed_packet(packet) for packet in first["math"])


def test_task_graph_rejects_dependency_cycles() -> None:
    orchestrator = _orchestrator()
    left = QuantumTask.create(
        task_id="task-left-0001",
        description="left",
        operation="phi_weighted_consensus",
        payload={"scores": [0.5]},
        dependencies=["task-right-0002"],
    )
    right = QuantumTask.create(
        task_id="task-right-0002",
        description="right",
        operation="phi_weighted_consensus",
        payload={"scores": [0.5]},
        dependencies=["task-left-0001"],
    )

    with pytest.raises(PythiaAgentInvariantError):
        orchestrator.run_task_graph(agent_name="math", tasks=[left, right])


def test_hostile_task_payload_and_shared_state_are_rejected() -> None:
    orchestrator = _orchestrator()
    with pytest.raises(PythiaAgentInvariantError):
        orchestrator.spawn_tasks(
            base_description="hostile",
            operation="phi_weighted_consensus",
            task_payloads=[{"scores": [0.5], "auto_apply": True}],
        )

    task = QuantumTask.create(
        description="safe",
        operation="phi_weighted_consensus",
        payload={"scores": [0.5]},
    )
    with pytest.raises(PythiaAgentInvariantError):
        orchestrator.run_entangled_group(
            agent_name="math", tasks=[task], shared_state={"action": "DEPLOY"}
        )


def test_hostile_executor_output_becomes_sealed_rejection_not_mutation() -> None:
    orchestrator = PythiaAgentOrchestrator()

    def hostile_executor(payload: dict) -> dict:
        return {
            "result": {"ok": True},
            "evidence": {"auto_apply": True, "action": "DEPLOY"},
        }

    orchestrator.register_sub_agent(
        "hostile", hostile_executor, allowed_operations=["external_quantum_job"]
    )
    task = QuantumTask.create(
        description="external", operation="external_quantum_job", payload={"value": 1}
    )
    packets = orchestrator.run_entangled_group(agent_name="hostile", tasks=[task])
    packet = packets[0]

    assert verify_sealed_packet(packet) is True
    assert packet["body"]["status"] == "EXECUTION_REJECTED"
    assert packet["body"]["auto_apply"] is False
    assert packet["body"]["source_modified"] is False
    assert "repair_proposal" in packet["body"]["evidence"]
    assert packet["body"]["evidence"]["repair_proposal"] is None


def test_nonfinite_executor_output_is_rejected_and_sealed() -> None:
    orchestrator = PythiaAgentOrchestrator()

    def bad_executor(payload: dict) -> dict:
        return {
            "result": {"score": float("inf")},
            "evidence": {"operation": "external_quantum_job"},
        }

    orchestrator.register_sub_agent(
        "bad", bad_executor, allowed_operations=["external_quantum_job"]
    )
    task = QuantumTask.create(
        description="external", operation="external_quantum_job", payload={"value": 1}
    )
    packet = orchestrator.run_entangled_group(agent_name="bad", tasks=[task])[0]

    assert verify_sealed_packet(packet) is True
    assert packet["body"]["status"] == "EXECUTION_REJECTED"
    assert "non-finite" in packet["body"]["evidence"]["error_message"]


def test_v1_v2_executor_failure_routes_to_salamander_repair_proposal(
    tmp_path: Path,
) -> None:
    module = tmp_path / "broken_executor.py"
    module.write_text(
        "def quantum_execute(payload):\n"
        "    # TODO: restore V2 quantum path\n"
        "    return {'result': payload}\n",
        encoding="utf-8",
    )

    orchestrator = PythiaAgentOrchestrator()

    def failing_executor(payload: dict) -> dict:
        raise RuntimeError("V2 quantum substrate path failed invariant verification")

    orchestrator.register_sub_agent(
        "v2", failing_executor, allowed_operations=["external_quantum_job"]
    )
    task = QuantumTask.create(
        description="v2 repair",
        operation="external_quantum_job",
        payload={
            "input": 1,
            "repair_target": {
                "module_path": str(module),
                "target_name": "quantum_execute",
            },
        },
    )
    packet = orchestrator.run_entangled_group(agent_name="v2", tasks=[task])[0]

    assert verify_sealed_packet(packet) is True
    assert packet["body"]["status"] == "EXECUTION_REJECTED_REPAIR_STAGED"
    repair = packet["body"]["evidence"]["repair_proposal"]
    assert repair["status"] == "HEALING_PROPOSAL_STAGED"
    assert repair["sovereign_human_gate"] is True
    assert repair["auto_apply"] is False
    assert repair["deployable_without_approval"] is False
    assert repair["packet"]["action"] == "ESCALATE_TO_SOVEREIGN_HUMAN"


def test_packet_tampering_breaks_verification() -> None:
    orchestrator = _orchestrator()
    task = QuantumTask.create(
        description="safe",
        operation="phi_weighted_consensus",
        payload={"scores": [0.5, 0.6]},
    )
    packet = orchestrator.run_entangled_group(agent_name="math", tasks=[task])[0]
    assert verify_sealed_packet(packet) is True

    tampered = dict(packet)
    tampered["body"] = dict(packet["body"])
    tampered["body"]["result"] = {"harmonic_score": 999.0}
    assert verify_sealed_packet(tampered) is False
