"""Production PYTHIA agent orchestration over HYBA's mathematical substrate.

This module is intentionally not a skeleton. It implements a bounded,
deterministic, evidence-sealed orchestration layer for PYTHIA agents:

- task spawning with payload and finite-value validation;
- built-in mathematical quantum-native operations (phi consensus, Ising energy,
  amplitude/QAE-style estimation, density-matrix invariant checks);
- support for injected Pythagoras/PULVINI/METIS executors via a strict adapter;
- parallel execution with deterministic output ordering;
- entangled/shared context hashing without mutable shared-state leakage;
- cryptographic result sealing and packet verification;
- fail-closed executor handling;
- Salamander repair proposal staging when V1/V2 executor paths break;
- adversarial guardrails against auto-apply, direct deployment, Stable Core
  mutation, NaN/Infinity, hostile executor output, and packet tampering.

No function in this module applies source changes, deploys code, commits files,
mines, or bypasses sovereign approval. PYTHIA acts by spawning work and sealing
outcomes; repair is routed to Salamander as a sovereign-gated proposal.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import math
import re
from statistics import fmean, pvariance
from typing import Any, Callable, Iterable, Literal, Mapping, Sequence
import uuid

from pythia_self_healing import (
    DamageReport,
    ImmutableInvariantGuard,
    SalamanderRegenerator,
    SelfHealingReactor,
)
from pythia_self_healing.autonomic_organism_governor import AutonomicInvariantError


TaskStatus = Literal[
    "EXECUTION_STAGED",
    "EXECUTION_REJECTED_REPAIR_STAGED",
    "EXECUTION_REJECTED",
]

_ALLOWED_OPERATIONS = {
    "phi_weighted_consensus",
    "ising_energy",
    "amplitude_expectation",
    "density_matrix_invariants",
    "external_quantum_job",
}

_FORBIDDEN_ACTIONS = {
    "APPLY",
    "AUTO_APPLY",
    "DEPLOY",
    "MERGE",
    "COMMIT",
    "MUTATE_STABLE_CORE",
    "SUBMIT_SHARE",
    "MINE",
}

_FORBIDDEN_TRUE_FLAGS = {
    "auto_apply",
    "automatic_application",
    "deployable_without_approval",
    "source_modified",
    "stable_core_modified",
    "direct_deploy",
    "mining_enabled",
    "pool_submit",
}

_TASK_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{8,96}$")


class PythiaAgentInvariantError(ValueError):
    """Raised when agent orchestration invariants are violated."""


class AgentExecutionError(RuntimeError):
    """Raised by executor adapters when a task cannot produce valid evidence."""


class PythiaAgentInvariantGuard:
    """Guard for task, result, and sealed-packet invariants."""

    def __init__(self) -> None:
        self._proposal_guard = ImmutableInvariantGuard()

    def assert_safe_payload(self, payload: Any, *, context: str) -> None:
        violations = self._find_violations(payload)
        if violations:
            raise PythiaAgentInvariantError(
                f"{context}: invariant violations detected: {violations}"
            )
        self._assert_json_and_finite(payload, context=context)

    def assert_result_mapping(self, result: Mapping[str, Any], *, context: str) -> None:
        self.assert_safe_payload(result, context=context)
        if "result" not in result and "evidence" not in result:
            raise PythiaAgentInvariantError(
                f"{context}: executor result must expose result/evidence"
            )

    def seal(self, body: Mapping[str, Any], *, context: str) -> dict[str, Any]:
        self.assert_safe_payload(body, context=context)
        seal_body = {
            "algorithm": "SHA-256",
            "body_hash": _sha256(body),
            "context": context,
            "timestamp": _utc_now(),
            "immutable_guard_active": True,
        }
        seal_body["seal"] = _sha256(seal_body)
        return seal_body

    def _find_violations(
        self, value: Any, *, path: str = "$", violations: list[str] | None = None
    ) -> list[str]:
        if violations is None:
            violations = []
        if isinstance(value, Mapping):
            for key, item in value.items():
                key_text = str(key)
                child = f"{path}.{key_text}"
                if key_text in _FORBIDDEN_TRUE_FLAGS and item is True:
                    violations.append(f"{child}=True")
                if (
                    key_text
                    in {
                        "sovereign_human_gate",
                        "human_sovereign_required",
                        "immutable_guard_active",
                    }
                    and item is False
                ):
                    violations.append(f"{child}=False")
                if (
                    key_text == "action"
                    and isinstance(item, str)
                    and item.upper() in _FORBIDDEN_ACTIONS
                ):
                    violations.append(f"{child}={item}")
                self._find_violations(item, path=child, violations=violations)
        elif isinstance(value, Sequence) and not isinstance(
            value, (str, bytes, bytearray)
        ):
            for index, item in enumerate(value):
                self._find_violations(
                    item, path=f"{path}[{index}]", violations=violations
                )
        return violations

    def _assert_json_and_finite(self, value: Any, *, context: str) -> None:
        try:
            json.dumps(value, sort_keys=True, default=str, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise PythiaAgentInvariantError(
                f"{context}: payload must be JSON-safe and finite: {exc}"
            ) from exc
        self._assert_finite_recursive(value, context=context)

    def _assert_finite_recursive(
        self, value: Any, *, context: str, path: str = "$"
    ) -> None:
        if isinstance(value, float):
            if not math.isfinite(value):
                raise PythiaAgentInvariantError(
                    f"{context}: non-finite float at {path}"
                )
        elif isinstance(value, int) and not isinstance(value, bool):
            return
        elif isinstance(value, Mapping):
            for key, item in value.items():
                self._assert_finite_recursive(
                    item, context=context, path=f"{path}.{key}"
                )
        elif isinstance(value, Sequence) and not isinstance(
            value, (str, bytes, bytearray)
        ):
            for index, item in enumerate(value):
                self._assert_finite_recursive(
                    item, context=context, path=f"{path}[{index}]"
                )


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        default=str,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bounded_workers(value: int, *, limit: int) -> int:
    if not isinstance(value, int) or value < 1 or value > limit:
        raise PythiaAgentInvariantError(f"max_workers must be in [1, {limit}]")
    return value


def _safe_float(value: Any, *, name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise PythiaAgentInvariantError(f"{name} must be finite")
    return number


def _as_number_list(
    value: Any, *, name: str, minimum: int = 1, maximum: int = 4096
) -> list[float]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise PythiaAgentInvariantError(f"{name} must be a numeric sequence")
    if not (minimum <= len(value) <= maximum):
        raise PythiaAgentInvariantError(
            f"{name} length must be in [{minimum}, {maximum}]"
        )
    values = [
        _safe_float(item, name=f"{name}[{index}]") for index, item in enumerate(value)
    ]
    return values


@dataclass(frozen=True)
class QuantumTask:
    """A bounded quantum-native task PYTHIA can execute or delegate."""

    task_id: str
    description: str
    operation: str
    payload: dict[str, Any]
    dependencies: tuple[str, ...] = ()
    created_at: str = field(default_factory=_utc_now)

    @classmethod
    def create(
        cls,
        *,
        description: str,
        operation: str,
        payload: Mapping[str, Any],
        dependencies: Iterable[str] = (),
        task_id: str | None = None,
    ) -> "QuantumTask":
        body = {
            "description": description,
            "operation": operation,
            "payload": dict(payload),
            "dependencies": sorted(str(dep) for dep in dependencies),
            "nonce": uuid.uuid4().hex if task_id is None else task_id,
        }
        generated_id = task_id or f"qt-{_sha256(body)[:24]}"
        task = cls(
            task_id=generated_id,
            description=description,
            operation=operation,
            payload=dict(payload),
            dependencies=tuple(sorted(str(dep) for dep in dependencies)),
        )
        task.validate()
        return task

    def validate(self, *, guard: PythiaAgentInvariantGuard | None = None) -> None:
        guard = guard or PythiaAgentInvariantGuard()
        if not _TASK_ID_RE.match(self.task_id):
            raise PythiaAgentInvariantError(
                "task_id must be stable, printable, and 8-96 chars"
            )
        if not self.description.strip():
            raise PythiaAgentInvariantError("description is required")
        if self.operation not in _ALLOWED_OPERATIONS:
            raise PythiaAgentInvariantError(f"unsupported operation: {self.operation}")
        guard.assert_safe_payload(self.payload, context=f"task:{self.task_id}")

    def executor_payload(
        self, shared_state: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        payload = dict(self.payload)
        payload["operation"] = self.operation
        if shared_state is not None:
            payload["shared_state"] = dict(shared_state)
        return payload


@dataclass(frozen=True)
class QuantumResult:
    """Unsealed task result before deterministic chain sealing."""

    task: QuantumTask
    agent_name: str
    status: TaskStatus
    result: Any
    evidence: dict[str, Any]
    shared_state_hash: str
    created_at: str = field(default_factory=_utc_now)

    def sealed(
        self,
        *,
        previous_hash: str = "GENESIS",
        guard: PythiaAgentInvariantGuard | None = None,
    ) -> dict[str, Any]:
        guard = guard or PythiaAgentInvariantGuard()
        body = {
            "task_id": self.task.task_id,
            "agent_name": self.agent_name,
            "operation": self.task.operation,
            "description": self.task.description,
            "status": self.status,
            "result": self.result,
            "evidence": self.evidence,
            "shared_state_hash": self.shared_state_hash,
            "previous_hash": previous_hash,
            "created_at": self.created_at,
            "sovereign_human_gate": True,
            "auto_apply": False,
            "source_modified": False,
            "stable_core_modified": False,
        }
        seal = guard.seal(body, context=f"PYTHIA task {self.task.task_id}")
        packet = {
            "packet_id": f"PYTHIA-QTASK-{self.task.task_id}",
            "timestamp": self.created_at,
            "type": "PYTHIA_AGENT_QUANTUM_TASK_RESULT",
            "status": self.status,
            "body": body,
            "cryptographic_seal": seal,
            "action": (
                "RETURN_SEALED_EVIDENCE"
                if self.status == "EXECUTION_STAGED"
                else "ESCALATE_TO_SALAMANDER_REPAIR_REVIEW"
            ),
            "sovereign_human_gate": True,
            "auto_apply": False,
        }
        guard.assert_safe_payload(packet, context=f"sealed packet {self.task.task_id}")
        return packet


class PythiaMathematicalQuantumExecutor:
    """Built-in deterministic mathematical executor for PYTHIA tasks.

    This is a production fallback/adapter, not a mock. It implements finite,
    auditable mathematical operations that mirror HYBA's substrate patterns and
    can sit beside external Pythagoras/PULVINI/METIS executors.
    """

    PHI = (1.0 + 5.0**0.5) / 2.0

    def __call__(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        operation = payload.get("operation")
        if operation == "phi_weighted_consensus":
            return self._phi_weighted_consensus(payload)
        if operation == "ising_energy":
            return self._ising_energy(payload)
        if operation == "amplitude_expectation":
            return self._amplitude_expectation(payload)
        if operation == "density_matrix_invariants":
            return self._density_matrix_invariants(payload)
        raise AgentExecutionError(
            f"built-in executor does not implement operation {operation!r}"
        )

    def _phi_weighted_consensus(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        scores = _as_number_list(
            payload.get("scores"), name="scores", minimum=1, maximum=4096
        )
        for index, score in enumerate(scores):
            if not 0.0 <= score <= 1.0:
                raise PythiaAgentInvariantError(f"scores[{index}] must be in [0, 1]")
        exponent = _safe_float(payload.get("phi_exponent", 1.0), name="phi_exponent")
        mean_score = fmean(scores)
        raw_weights = [
            self.PHI ** (exponent * (1.0 - abs(score - mean_score))) for score in scores
        ]
        total = sum(raw_weights)
        weights = [weight / total for weight in raw_weights]
        harmonic_score = sum(score * weight for score, weight in zip(scores, weights))
        coherence = 1.0 - min(1.0, pvariance(scores) if len(scores) > 1 else 0.0)
        result = {
            "harmonic_score": harmonic_score,
            "coherence": coherence,
            "weights": weights,
            "mean_score": mean_score,
            "phi": self.PHI,
        }
        return {
            "result": result,
            "evidence": {
                "operation": "phi_weighted_consensus",
                "weight_sum": sum(weights),
                "finite": True,
                "mathematical_invariant": "weights_normalize_to_one_and_scores_remain_bounded",
            },
        }

    def _ising_energy(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        fields = payload.get("fields", {})
        couplers = payload.get("couplers", {})
        if not isinstance(fields, Mapping) or not isinstance(couplers, Mapping):
            raise PythiaAgentInvariantError("fields and couplers must be mappings")
        spin_state = payload.get("spin_state")
        if spin_state is None:
            bitstring = str(payload.get("bitstring", ""))
            if not bitstring or any(bit not in "01" for bit in bitstring):
                raise PythiaAgentInvariantError("bitstring must contain only 0/1")
            spins = {
                f"z{index}": 1 if bit == "1" else -1
                for index, bit in enumerate(bitstring)
            }
        else:
            if not isinstance(spin_state, Mapping):
                raise PythiaAgentInvariantError("spin_state must be a mapping")
            spins = {str(key): int(value) for key, value in spin_state.items()}
            if any(value not in {-1, 1} for value in spins.values()):
                raise PythiaAgentInvariantError("spin_state values must be -1 or +1")
        constant = _safe_float(payload.get("constant", 0.0), name="constant")
        energy = constant
        for key, coeff in fields.items():
            energy += _safe_float(coeff, name=f"fields[{key}]") * spins.get(str(key), 0)
        for key, coeff in couplers.items():
            match = re.fullmatch(r"z(\d+)z(\d+)", str(key))
            if not match:
                raise PythiaAgentInvariantError(f"invalid coupler key: {key}")
            left, right = f"z{match.group(1)}", f"z{match.group(2)}"
            energy += (
                _safe_float(coeff, name=f"couplers[{key}]")
                * spins.get(left, 0)
                * spins.get(right, 0)
            )
        return {
            "result": {"energy": energy, "spin_state": spins},
            "evidence": {
                "operation": "ising_energy",
                "hamiltonian_form": "H = c + Σ h_i Z_i + Σ J_ij Z_i Z_j",
                "finite": math.isfinite(energy),
            },
        }

    def _amplitude_expectation(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        samples = _as_number_list(
            payload.get("samples"), name="samples", minimum=2, maximum=100_000
        )
        epsilon = _safe_float(
            payload.get("precision_epsilon", 0.01), name="precision_epsilon"
        )
        if not 0.0 < epsilon <= 1.0:
            raise PythiaAgentInvariantError("precision_epsilon must be in (0, 1]")
        mean = fmean(samples)
        variance = pvariance(samples)
        classical_samples = max(
            1, math.ceil(max(variance, 1e-12) / (epsilon * epsilon))
        )
        qae_oracle_calls = max(1, math.ceil(math.sqrt(classical_samples)))
        return {
            "result": {
                "expectation": mean,
                "variance": variance,
                "classical_samples_for_epsilon": classical_samples,
                "qae_oracle_calls_for_epsilon": qae_oracle_calls,
                "quadratic_speedup_factor": classical_samples / qae_oracle_calls,
            },
            "evidence": {
                "operation": "amplitude_expectation",
                "speedup_class": "quadratic_sampling_accounting",
                "finite": True,
            },
        }

    def _density_matrix_invariants(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        matrix = payload.get("matrix")
        if (
            not isinstance(matrix, Sequence)
            or isinstance(matrix, (str, bytes, bytearray))
            or not matrix
        ):
            raise PythiaAgentInvariantError(
                "matrix must be a non-empty square sequence"
            )
        n = len(matrix)
        rows: list[list[complex]] = []
        for i, row in enumerate(matrix):
            if (
                not isinstance(row, Sequence)
                or isinstance(row, (str, bytes, bytearray))
                or len(row) != n
            ):
                raise PythiaAgentInvariantError("matrix must be square")
            parsed_row: list[complex] = []
            for j, value in enumerate(row):
                parsed_row.append(self._parse_complex(value, name=f"matrix[{i}][{j}]"))
            rows.append(parsed_row)
        hermitian_error = max(
            abs(rows[i][j] - rows[j][i].conjugate()) for i in range(n) for j in range(n)
        )
        trace = sum(rows[i][i] for i in range(n))
        trace_error = abs(trace.real - 1.0) + abs(trace.imag)
        diagonal_min = min(rows[i][i].real for i in range(n))
        psd_proxy = diagonal_min >= -1e-9
        invariant_ok = hermitian_error <= 1e-9 and trace_error <= 1e-9 and psd_proxy
        return {
            "result": {
                "dimension": n,
                "hermitian_error": hermitian_error,
                "trace_error": trace_error,
                "diagonal_min": diagonal_min,
                "density_matrix_invariant_ok": invariant_ok,
            },
            "evidence": {
                "operation": "density_matrix_invariants",
                "note": "PSD proxy checks diagonal non-negativity; exhaustive PSD can be supplied by substrate executor.",
                "finite": True,
            },
        }

    @staticmethod
    def _parse_complex(value: Any, *, name: str) -> complex:
        if isinstance(value, int | float):
            real = _safe_float(value, name=name)
            return complex(real, 0.0)
        if (
            isinstance(value, Sequence)
            and not isinstance(value, (str, bytes, bytearray))
            and len(value) == 2
        ):
            return complex(
                _safe_float(value[0], name=f"{name}.real"),
                _safe_float(value[1], name=f"{name}.imag"),
            )
        raise PythiaAgentInvariantError(f"{name} must be numeric or [real, imag]")


class PythiaSubAgent:
    """A bounded executor adapter for PYTHIA quantum-native tasks."""

    def __init__(
        self,
        *,
        name: str,
        quantum_executor: Callable[[dict[str, Any]], Mapping[str, Any]],
        allowed_operations: Iterable[str] | None = None,
        guard: PythiaAgentInvariantGuard | None = None,
    ) -> None:
        if not name.strip():
            raise PythiaAgentInvariantError("agent name is required")
        self.name = name
        self.quantum_executor = quantum_executor
        self.allowed_operations = set(allowed_operations or _ALLOWED_OPERATIONS)
        self.guard = guard or PythiaAgentInvariantGuard()

    def execute(
        self, task: QuantumTask, shared_state: Mapping[str, Any] | None = None
    ) -> QuantumResult:
        task.validate(guard=self.guard)
        if task.operation not in self.allowed_operations:
            raise PythiaAgentInvariantError(
                f"agent {self.name} cannot execute {task.operation}"
            )
        if shared_state is not None:
            self.guard.assert_safe_payload(
                shared_state, context=f"shared_state:{task.task_id}"
            )
        payload = task.executor_payload(shared_state=shared_state)
        raw = self.quantum_executor(payload)
        if not isinstance(raw, Mapping):
            raise AgentExecutionError("quantum executor must return a mapping")
        self.guard.assert_result_mapping(raw, context=f"executor_result:{task.task_id}")
        result = raw.get("result", raw)
        evidence = dict(raw.get("evidence", {}))
        evidence.setdefault("executor", self.name)
        evidence.setdefault("operation", task.operation)
        evidence.setdefault("input_hash", _sha256(payload))
        evidence.setdefault("result_hash", _sha256(result))
        evidence.setdefault(
            "product_boundary", "pythia_agent_quantum_execution_not_mining"
        )
        return QuantumResult(
            task=task,
            agent_name=self.name,
            status="EXECUTION_STAGED",
            result=result,
            evidence=evidence,
            shared_state_hash=_sha256(shared_state or {}),
        )


class PythiaAgentOrchestrator:
    """Production PYTHIA orchestrator for sealed, quantum-native agent work."""

    def __init__(
        self, *, max_workers_limit: int = 16, max_payload_bytes: int = 262_144
    ) -> None:
        self.sub_agents: dict[str, PythiaSubAgent] = {}
        self.max_workers_limit = max_workers_limit
        self.max_payload_bytes = max_payload_bytes
        self.guard = PythiaAgentInvariantGuard()
        self.repair_reactor = SelfHealingReactor(SalamanderRegenerator())

    def register_builtin_agent(self, name: str = "pythia-math-substrate") -> None:
        self.register_sub_agent(name, PythiaMathematicalQuantumExecutor())

    def register_sub_agent(
        self,
        name: str,
        quantum_executor: Callable[[dict[str, Any]], Mapping[str, Any]],
        *,
        allowed_operations: Iterable[str] | None = None,
    ) -> None:
        self.sub_agents[name] = PythiaSubAgent(
            name=name,
            quantum_executor=quantum_executor,
            allowed_operations=allowed_operations,
            guard=self.guard,
        )

    def spawn_tasks(
        self,
        *,
        base_description: str,
        operation: str,
        task_payloads: Iterable[Mapping[str, Any]],
    ) -> list[QuantumTask]:
        tasks = [
            QuantumTask.create(
                description=base_description, operation=operation, payload=payload
            )
            for payload in task_payloads
        ]
        for task in tasks:
            if (
                len(_canonical_json(task.payload).encode("utf-8"))
                > self.max_payload_bytes
            ):
                raise PythiaAgentInvariantError(
                    f"task payload too large: {task.task_id}"
                )
        return tasks

    def run_entangled_group(
        self,
        *,
        agent_name: str,
        tasks: Sequence[QuantumTask],
        shared_state: Mapping[str, Any] | None = None,
        max_workers: int = 4,
    ) -> list[dict[str, Any]]:
        if agent_name not in self.sub_agents:
            raise PythiaAgentInvariantError(f"unknown sub-agent: {agent_name}")
        if not tasks:
            return []
        _bounded_workers(max_workers, limit=self.max_workers_limit)
        if shared_state is not None:
            self.guard.assert_safe_payload(
                shared_state, context="entangled_shared_state"
            )
        agent = self.sub_agents[agent_name]
        results: list[QuantumResult] = []
        with ThreadPoolExecutor(max_workers=min(max_workers, len(tasks))) as executor:
            futures = {
                executor.submit(
                    self._execute_or_repair, agent, task, shared_state
                ): task.task_id
                for task in tasks
            }
            for future in as_completed(futures):
                results.append(future.result())
        return self._seal_ordered(results)

    def run_multi_agent_parallel(
        self,
        agent_task_map: Mapping[str, Sequence[QuantumTask]],
        *,
        shared_state: Mapping[str, Any] | None = None,
        max_workers: int = 8,
    ) -> dict[str, list[dict[str, Any]]]:
        _bounded_workers(max_workers, limit=self.max_workers_limit)
        if shared_state is not None:
            self.guard.assert_safe_payload(
                shared_state, context="multi_agent_shared_state"
            )
        unknown = sorted(set(agent_task_map) - set(self.sub_agents))
        if unknown:
            raise PythiaAgentInvariantError(f"unknown sub-agents: {unknown}")
        output: dict[str, list[dict[str, Any]]] = {
            name: [] for name in sorted(agent_task_map)
        }
        with ThreadPoolExecutor(
            max_workers=min(max_workers, max(1, len(agent_task_map)))
        ) as executor:
            futures = {
                executor.submit(
                    self.run_entangled_group,
                    agent_name=name,
                    tasks=list(tasks),
                    shared_state=shared_state,
                    max_workers=max_workers,
                ): name
                for name, tasks in sorted(agent_task_map.items())
            }
            for future in as_completed(futures):
                output[futures[future]] = future.result()
        return output

    def run_task_graph(
        self,
        *,
        agent_name: str,
        tasks: Sequence[QuantumTask],
        shared_state: Mapping[str, Any] | None = None,
        max_workers: int = 4,
    ) -> list[dict[str, Any]]:
        ordered = self._topological_sort(tasks)
        completed: dict[str, dict[str, Any]] = {}
        packets: list[dict[str, Any]] = []
        for task in ordered:
            dependency_context = {
                dep: completed[dep]["cryptographic_seal"]["body_hash"]
                for dep in task.dependencies
            }
            merged_state = dict(shared_state or {})
            merged_state["dependency_context"] = dependency_context
            packet = self.run_entangled_group(
                agent_name=agent_name,
                tasks=[task],
                shared_state=merged_state,
                max_workers=max_workers,
            )[0]
            completed[task.task_id] = packet
            packets.append(packet)
        return packets

    def verify_packet_sequence(self, packets: Sequence[Mapping[str, Any]]) -> bool:
        previous = "GENESIS"
        for packet in sorted(
            packets, key=lambda item: str(item.get("body", {}).get("task_id", ""))
        ):
            if not verify_sealed_packet(packet):
                return False
            if packet["body"].get("previous_hash") != previous:
                return False
            previous = packet["cryptographic_seal"]["body_hash"]
        return True

    def _execute_or_repair(
        self,
        agent: PythiaSubAgent,
        task: QuantumTask,
        shared_state: Mapping[str, Any] | None,
    ) -> QuantumResult:
        try:
            return agent.execute(task, shared_state=shared_state)
        except Exception as exc:  # fail-closed into sealed evidence, not silent crash
            repair_proposal = self._stage_repair(task, exc)
            evidence = {
                "operation": task.operation,
                "executor": agent.name,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "repair_proposal": repair_proposal,
                "finite": True,
                "product_boundary": "pythia_agent_failure_to_salamander_repair_not_auto_apply",
            }
            return QuantumResult(
                task=task,
                agent_name=agent.name,
                status=(
                    "EXECUTION_REJECTED_REPAIR_STAGED"
                    if repair_proposal
                    else "EXECUTION_REJECTED"
                ),
                result=None,
                evidence=evidence,
                shared_state_hash=_sha256(shared_state or {}),
            )

    def _stage_repair(self, task: QuantumTask, exc: Exception) -> dict[str, Any] | None:
        target = task.payload.get("repair_target")
        if not isinstance(target, Mapping):
            return None
        module_path = target.get("module_path")
        target_name = target.get("target_name")
        if not module_path or not target_name:
            return None
        report = DamageReport(
            {
                "needs_repair": True,
                "issues": [
                    f"PYTHIA executor failure: {type(exc).__name__}",
                    str(exc),
                    "V1/V2 quantum path failure routed to Salamander sovereign repair proposal",
                ],
                "suggested_goal": "Repair failed PYTHIA quantum executor path while preserving all invariants",
                "architecture_impact": "LOCAL_LIMB",
                "metrics_before": {"executor_status": "failed"},
                "metrics_target": {"executor_status": "sealed_valid_execution"},
            }
        )
        proposal = self.repair_reactor.heal_damage(
            report, str(module_path), str(target_name)
        )
        proposal["deployable_without_approval"] = False
        return proposal

    def _seal_ordered(self, results: Sequence[QuantumResult]) -> list[dict[str, Any]]:
        ordered = sorted(results, key=lambda result: result.task.task_id)
        packets: list[dict[str, Any]] = []
        previous = "GENESIS"
        for result in ordered:
            packet = result.sealed(previous_hash=previous, guard=self.guard)
            previous = packet["cryptographic_seal"]["body_hash"]
            packets.append(packet)
        return packets

    @staticmethod
    def _topological_sort(tasks: Sequence[QuantumTask]) -> list[QuantumTask]:
        by_id = {task.task_id: task for task in tasks}
        if len(by_id) != len(tasks):
            raise PythiaAgentInvariantError("task graph contains duplicate task IDs")
        for task in tasks:
            missing = set(task.dependencies) - set(by_id)
            if missing:
                raise PythiaAgentInvariantError(
                    f"task {task.task_id} has missing dependencies: {sorted(missing)}"
                )
        temporary: set[str] = set()
        permanent: set[str] = set()
        ordered: list[QuantumTask] = []

        def visit(task_id: str) -> None:
            if task_id in permanent:
                return
            if task_id in temporary:
                raise PythiaAgentInvariantError(
                    "task graph contains a dependency cycle"
                )
            temporary.add(task_id)
            for dep in by_id[task_id].dependencies:
                visit(dep)
            temporary.remove(task_id)
            permanent.add(task_id)
            ordered.append(by_id[task_id])

        for task_id in sorted(by_id):
            visit(task_id)
        return ordered


def verify_sealed_packet(packet: Mapping[str, Any]) -> bool:
    try:
        body = packet["body"]
        seal = packet["cryptographic_seal"]
        if (
            seal.get("algorithm") != "SHA-256"
            or seal.get("immutable_guard_active") is not True
        ):
            return False
        return seal.get("body_hash") == _sha256(body)
    except Exception:
        return False
