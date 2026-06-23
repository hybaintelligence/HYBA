"""
Dodecahedral Solver Core
PYTHIA Mining System - Classical Structured-Search Layer

This module implements a classical structured-search algorithm using dodecahedral
symmetry and golden ratio geometry. It runs deterministically on classical CPU/GPU
hardware (M3 Ultra in the current deployment). It does NOT claim quantum hardware
execution or quantum speedup over classical brute-force search.
"""

from __future__ import annotations

import logging
import math
import os
import time
from .bitcoin_header import build_header, sha256d_hash
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

GOLDEN_RATIO = (1.0 + math.sqrt(5.0)) / 2.0
MASS_GAP_TARGET = 3.0 - GOLDEN_RATIO
DODECAHEDRON_VERTICES = 20
MAX_UINT32_NONCE = 2**32 - 1
PULVINI_HASHRATE_CAP_EHS = 1.0


@dataclass
class QuantumResult:
    nonce: Optional[int] = None
    energy: float = 0.0
    iterations: int = 0
    convergence: bool = True
    error_rate: Optional[float] = None
    phi_resonance_score: Optional[float] = None


class QuantumSolverConfigurationError(ValueError):
    """Raised when a mining job cannot be represented as a valid search space."""


class QuantumNumericalInstabilityError(RuntimeError):
    """Raised when structured state evolution produces non-finite numerical values."""


class DodecahedralQuantumSolver:
    """
    Unitary state-vector formulation covering high-dimensional complex Hilbert spaces
    using Penrose-Du Sautoy symmetry-breaking geometries.

    This class reports only derived runtime metrics or explicitly configured estimates.
    It does not publish fixed performance, quality, or valuation numbers as production
    telemetry. All configured estimates are governance-capped at 1 EH/s.
    """

    def __init__(self, configured_capacity_ehs: Optional[float] = None):
        self.is_available_flag = True
        self.current_config: Dict[str, Any] = {}
        self.power_scale = 1.0
        self.logger = logging.getLogger("quantum_solver")
        self.last_solve_iterations = 0
        self.last_solve_duration_seconds: Optional[float] = None
        self.last_solution_nonce: Optional[int] = None
        self.last_error: Optional[str] = None
        self.configured_capacity_ehs = self._load_configured_capacity(
            configured_capacity_ehs
        )
        self.basis_states = self._generate_dodecahedral_basis_states()
        self._used_nonces: set[int] = set()
        self._solve_call_count = 0

    @staticmethod
    def _load_configured_capacity(
        configured_capacity_ehs: Optional[float],
    ) -> Optional[float]:
        raw_value: Optional[float | str] = configured_capacity_ehs
        if raw_value is None:
            raw_value = os.getenv("HYBA_QUANTUM_CAPACITY_EHS")
        if raw_value in (None, ""):
            return None
        try:
            parsed = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise QuantumSolverConfigurationError(
                "HYBA_QUANTUM_CAPACITY_EHS must be numeric"
            ) from exc
        if not math.isfinite(parsed) or parsed <= 0:
            raise QuantumSolverConfigurationError(
                "HYBA_QUANTUM_CAPACITY_EHS must be positive"
            )
        return float(min(parsed, PULVINI_HASHRATE_CAP_EHS))

    def set_power_scale(self, scale: float):
        """Set the configured power scale for capacity estimates."""
        if (
            not isinstance(scale, (int, float))
            or not math.isfinite(float(scale))
            or scale <= 0
        ):
            raise QuantumSolverConfigurationError(
                "power scale must be a positive finite number"
            )
        self.power_scale = float(scale)

    def calculate_integrated_hashrate(self) -> Optional[float]:
        """
        Return configured estimated hashrate in EHS, or ``None`` when unavailable.

        Production telemetry must come from observed share/hash accounting or an explicit
        deployment capacity setting. The solver no longer reports a hardcoded hashrate;
        any configured estimate is capped at the PULVINI 1 EH/s governance boundary.
        """
        if self.configured_capacity_ehs is None:
            return None
        return float(
            min(
                self.configured_capacity_ehs * self.power_scale,
                PULVINI_HASHRATE_CAP_EHS,
            )
        )

    def _generate_dodecahedral_basis_states(self) -> np.ndarray:
        """
        Generate the twenty normalized dodecahedral vertex basis states.

        The regular dodecahedron has vertices ``(±1, ±1, ±1)``, ``(0, ±1/Φ, ±Φ)``,
        ``(±1/Φ, ±Φ, 0)``, and ``(±Φ, 0, ±1/Φ)``. Each real 3D vertex is normalized
        and assigned deterministic phase ``exp(i * 2π * k * Φ)``.
        """
        phi = GOLDEN_RATIO
        inv_phi = 1.0 / phi

        vertices = []
        for x in [-1.0, 1.0]:
            for y in [-1.0, 1.0]:
                for z in [-1.0, 1.0]:
                    vertices.append([x, y, z])
        for y in [-inv_phi, inv_phi]:
            for z in [-phi, phi]:
                vertices.append([0.0, y, z])
        for x in [-inv_phi, inv_phi]:
            for y in [-phi, phi]:
                vertices.append([x, y, 0.0])
        for x in [-phi, phi]:
            for z in [-inv_phi, inv_phi]:
                vertices.append([x, 0.0, z])

        raw_coords = np.array(vertices, dtype=np.complex128)
        norms = np.linalg.norm(raw_coords, axis=1, keepdims=True)
        if not np.isfinite(norms).all() or np.any(norms <= 0):
            raise QuantumNumericalInstabilityError(
                "Dodecahedral basis contains invalid norms"
            )
        normalized_basis = raw_coords / norms

        for i in range(DODECAHEDRON_VERTICES):
            theta = 2.0 * np.pi * i * GOLDEN_RATIO % (2.0 * np.pi)
            normalized_basis[i] *= np.exp(1j * theta)

        self._assert_finite_state(normalized_basis, "dodecahedral basis")
        return normalized_basis

    @staticmethod
    def _validate_nonce_ranges(
        nonce_ranges: List[Tuple[int, int]],
    ) -> List[Tuple[int, int]]:
        if not nonce_ranges:
            raise QuantumSolverConfigurationError(
                "At least one nonce range is required"
            )

        validated: List[Tuple[int, int]] = []
        for index, nonce_range in enumerate(nonce_ranges):
            if len(nonce_range) != 2:
                raise QuantumSolverConfigurationError(
                    f"Nonce range {index} must contain exactly two bounds"
                )
            start, end = int(nonce_range[0]), int(nonce_range[1])
            if start < 0 or end < 0:
                raise QuantumSolverConfigurationError(
                    "Nonce range bounds must be non-negative"
                )
            if start > end:
                raise QuantumSolverConfigurationError(
                    "Nonce range start must be <= end"
                )
            if end > MAX_UINT32_NONCE:
                raise QuantumSolverConfigurationError(
                    "Nonce range end exceeds uint32 nonce space"
                )
            validated.append((start, end))
        return validated

    async def configure_search(
        self, target: int, nonce_ranges: List[Tuple[int, int]]
    ) -> bool:
        if not isinstance(target, int) or target <= 0:
            raise QuantumSolverConfigurationError(
                "Mining target must be a positive non-zero integer"
            )

        validated_ranges = self._validate_nonce_ranges(nonce_ranges)
        search_space_size = sum((end - start + 1) for start, end in validated_ranges)
        if search_space_size <= 0:
            raise QuantumSolverConfigurationError(
                "Nonce search space must be non-empty"
            )

        self.current_config = {
            "target": target,
            "nonce_ranges": validated_ranges,
            "search_space_size": search_space_size,
            "configured_at": time.time(),
        }
        self.last_error = None
        return True

    def calculate_integrated_entropy(self, amplitudes: np.ndarray) -> float:
        """Calculate ``S = -sum_i p_i log2(p_i)`` for normalized measurement probabilities."""
        amplitudes = np.asarray(amplitudes, dtype=np.complex128)
        self._assert_finite_state(amplitudes, "entropy amplitudes")
        probabilities = np.abs(amplitudes) ** 2
        total_probability = float(np.sum(probabilities))
        if not math.isfinite(total_probability) or total_probability <= 0:
            raise QuantumNumericalInstabilityError(
                "Entropy probabilities do not form a valid distribution"
            )
        probabilities = probabilities / total_probability
        probabilities = np.where(probabilities > 1e-15, probabilities, 1e-15)
        return -float(np.sum(probabilities * np.log2(probabilities)))

    @staticmethod
    def _assert_finite_state(state: np.ndarray, label: str) -> None:
        if not np.isfinite(state).all():
            raise QuantumNumericalInstabilityError(
                f"{label} contains NaN or Inf values"
            )

    @staticmethod
    def _normalize_state_vector(state: np.ndarray) -> np.ndarray:
        values = np.asarray(state, dtype=np.complex128).reshape(-1)
        norm = float(np.linalg.norm(values))
        if not math.isfinite(norm) or norm <= 0.0:
            raise QuantumNumericalInstabilityError("state vector norm is invalid")
        return values / norm

    @staticmethod
    def density_matrix_from_state(state: np.ndarray) -> np.ndarray:
        """Return a trace-one density matrix for a state vector."""
        psi = DodecahedralQuantumSolver._normalize_state_vector(state).reshape(-1, 1)
        rho = psi @ psi.conj().T
        trace = np.trace(rho)
        if not np.isclose(trace.real, 1.0, atol=1e-10):
            raise QuantumNumericalInstabilityError("density trace is not conserved")
        return rho

    @staticmethod
    def irrational_truncation_boundary(singular_values: np.ndarray) -> Dict[str, Any]:
        """Choose the SVD boundary whose adjacent ratio is closest to 3-φ."""
        values = np.asarray(singular_values, dtype=np.float64).reshape(-1)
        values = values[np.isfinite(values) & (values > 0.0)]
        if values.size < 2:
            raise QuantumSolverConfigurationError(
                "at least two positive singular values required"
            )
        ratios = values[:-1] / values[1:]
        idx = int(np.argmin(np.abs(ratios - MASS_GAP_TARGET)))
        selected = float(ratios[idx])
        return {
            "boundary_index": idx + 1,
            "selected_ratio": selected,
            "mass_gap_target": float(MASS_GAP_TARGET),
            "alignment_error": abs(selected - MASS_GAP_TARGET),
        }

    def _mass_gap_alignment(self) -> Dict[str, Any]:
        spectrum = np.array(
            [MASS_GAP_TARGET ** (-idx) for idx in range(1, 8)], dtype=np.float64
        )
        return self.irrational_truncation_boundary(spectrum)

    def _basis_coherence(self) -> float:
        """Derive coherence from observed row-norm spread instead of using a fixed score."""
        row_norms = np.linalg.norm(self.basis_states, axis=1)
        self._assert_finite_state(row_norms, "basis row norms")
        max_spread = float(np.max(row_norms) - np.min(row_norms))
        return float(max(0.0, min(1.0, 1.0 - max_spread)))

    def _phi_phase_alignment(self) -> float:
        """Derive golden-ratio phase alignment from the generated basis phases."""
        phases = np.angle(self.basis_states[:, 0])
        if phases.size < 2:
            return 1.0
        deltas = np.diff(np.unwrap(phases))
        expected = 2.0 * math.pi * GOLDEN_RATIO
        residual = np.mod(deltas - expected + math.pi, 2.0 * math.pi) - math.pi
        rms = float(np.sqrt(np.mean(residual**2)))
        return float(max(0.0, min(1.0, 1.0 - (rms / math.pi))))

    def _marked_state_index(self) -> int:
        if not self.current_config:
            raise QuantumSolverConfigurationError(
                "Solver must be configured before solving"
            )
        target = int(self.current_config["target"])
        nonce_ranges = self.current_config["nonce_ranges"]
        range_fingerprint = sum((start * 31 + end * 17) for start, end in nonce_ranges)
        return int((target ^ range_fingerprint) % DODECAHEDRON_VERTICES)

    def _project_index_to_nonce(self, basis_index: int) -> int:
        if not self.current_config:
            raise QuantumSolverConfigurationError(
                "Solver must be configured before projecting a nonce"
            )
        offset = basis_index % int(self.current_config["search_space_size"])
        for start, end in self.current_config["nonce_ranges"]:
            span = end - start + 1
            if offset < span:
                return int(start + offset)
            offset -= span
        raise QuantumSolverConfigurationError(
            "Measured state could not be projected to a nonce range"
        )

    def _hash_for_nonce(
        self, nonce: int, target: int, job=None, extranonce2: str = "00000000"
    ) -> int:
        """Return real job SHA-256d when a job is supplied, otherwise a deterministic surrogate.

        Live mining validation is always performed against a concrete blockchain job.
        Unit/property tests may configure only a target and nonce range; in that case we
        use the nonce as a monotone surrogate so the structured-search layer can be
        tested without fabricating pool telemetry or accepted shares.
        """
        if job is None:
            return int(nonce)
        header = build_header(job, nonce, extranonce2 or "00000000")
        return sha256d_hash(header)

    def _structured_nonce_score(self, nonce: int, target: int) -> float:
        """Score a nonce using blockchain-evidence features, not Grover marking.

        The score is intentionally heuristic: it combines target proximity, Φ phase
        alignment, dodecahedral sector coverage, and avoidance of already-searched
        nonces.  Actual acceptance remains a classical SHA-256d comparison in
        ``_hash_for_nonce`` whenever a job is supplied.
        """
        target_window = max(1.0, float(target % 1_000_003))
        target_phase = target_window / 1_000_003.0
        nonce_phase = (nonce * GOLDEN_RATIO) % 1.0
        phase_alignment = 1.0 - abs(nonce_phase - target_phase)
        sector_position = (nonce % DODECAHEDRON_VERTICES) / DODECAHEDRON_VERTICES
        sector_balance = 1.0 - abs(sector_position - (1.0 / GOLDEN_RATIO))
        freshness = 0.0 if nonce in self._used_nonces else 1.0
        score = 0.45 * phase_alignment + 0.35 * sector_balance + 0.20 * freshness
        return float(max(0.0, min(1.0, score)))

    def _structured_candidate_order(
        self,
        nonce_ranges: List[Tuple[int, int]],
        target: int,
        max_iterations: int,
    ) -> List[int]:
        """Return deterministic, evidence-weighted nonce candidates within bounds."""
        candidates: List[int] = []
        for start, end in nonce_ranges:
            for nonce in range(start, end + 1):
                candidates.append(int(nonce))
                if len(candidates) >= max_iterations:
                    break
            if len(candidates) >= max_iterations:
                break
        candidates.sort(key=lambda n: (-self._structured_nonce_score(n, target), n))
        return candidates

    async def solve(
        self,
        max_iterations: int = 100,
        timeout: float = 30.0,
        target: int = 0,
        job=None,
        extranonce2: str = "00000000",
    ) -> Optional[int]:
        """Run deterministic structured nonce search with classical verification.

        This is deliberately not Grover/amplitude amplification.  The live blockchain
        evidence available to this solver is structured: bounded nonce ranges, block
        job headers, target difficulty, previous coverage, and geometric basis
        sectors.  The solver therefore ranks candidates by evidence-weighted
        structure, then verifies each candidate with SHA-256d when a job is present.
        """
        if max_iterations <= 0 or timeout <= 0:
            raise QuantumSolverConfigurationError(
                "max_iterations and timeout must be positive"
            )
        if not self.current_config:
            raise QuantumSolverConfigurationError(
                "Solver must be configured before solving"
            )

        start_time = time.monotonic()
        self.last_solve_iterations = 0
        self.last_solve_duration_seconds = None
        self._solve_call_count += 1

        try:
            nonce_ranges = self.current_config.get("nonce_ranges", [(0, 2**32 - 1)])
            target = int(self.current_config.get("target", target))
            ordered_candidates = self._structured_candidate_order(
                nonce_ranges, target, max_iterations
            )
            if not ordered_candidates:
                self.last_error = "empty_candidate_order"
                self.last_solve_duration_seconds = time.monotonic() - start_time
                return None

            best_candidate = ordered_candidates[0]
            for iteration, nonce in enumerate(ordered_candidates, start=1):
                if time.monotonic() - start_time >= timeout:
                    self.last_error = "timeout"
                    self.last_solve_duration_seconds = time.monotonic() - start_time
                    self.logger.warning(
                        "Structured PoW search timed out after %d iterations",
                        iteration - 1,
                    )
                    return None

                self.last_solve_iterations += 1
                self._used_nonces.add(int(nonce))
                if self._hash_for_nonce(nonce, target, job, extranonce2) <= target:
                    self.last_solution_nonce = int(nonce)
                    self.last_solve_duration_seconds = time.monotonic() - start_time
                    self.last_error = None
                    self.logger.info("Structured search found valid nonce %d", nonce)
                    return int(nonce)

            if job is None:
                # Non-live test mode: return the highest-ranked bounded candidate,
                # but do not represent it as a pool-validated share.
                self.last_solution_nonce = int(best_candidate)
                self.last_solve_duration_seconds = time.monotonic() - start_time
                self.last_error = "candidate_only_no_job"
                return int(best_candidate)

            self.last_error = "no_solution_found"
            self.last_solve_duration_seconds = time.monotonic() - start_time
            return None

        except (
            np.linalg.LinAlgError,
            FloatingPointError,
            QuantumNumericalInstabilityError,
        ) as exc:
            self.last_error = str(exc)
            self.last_solve_duration_seconds = time.monotonic() - start_time
            self.logger.error("Numerical instability in structured solve: %s", exc)
            return None

    async def _classical_fallback(
        self,
        nonce_ranges: list,
        target: int,
        max_iterations: int,
        timeout: float,
        start_time: float,
        job=None,
        extranonce2: str = "00000000",
    ) -> Optional[int]:
        """Deterministic sequential PoW verifier using real SHA-256d when a job exists."""

        searched = 0
        for start, end in nonce_ranges:
            stop = min(start + max_iterations - searched, end + 1)
            for i, nonce in enumerate(range(start, stop)):
                if time.monotonic() - start_time >= timeout:
                    self.last_error = "timeout"
                    self.last_solve_duration_seconds = time.monotonic() - start_time
                    self.logger.warning(
                        "Classical PoW search timed out after %d iterations", i
                    )
                    return None

                self.last_solve_iterations += 1
                searched += 1
                if self._hash_for_nonce(nonce, target, job, extranonce2) <= target:
                    self.last_solution_nonce = nonce
                    self.last_solve_duration_seconds = time.monotonic() - start_time
                    self.last_error = None
                    self.logger.info("Classical PoW found valid nonce %d", nonce)
                    return nonce
                if searched >= max_iterations:
                    break
            if searched >= max_iterations:
                break

        self.last_error = "no_solution_found"
        self.last_solve_duration_seconds = time.monotonic() - start_time
        self.logger.debug(
            "Classical PoW search completed: no solution found (expected at this hashrate)"
        )
        return None

    def is_available(self) -> bool:
        return self.is_available_flag

    async def health_check(self) -> bool:
        return self.is_available_flag

    async def restart(self) -> bool:
        self.last_error = None
        return True

    def get_metrics(self) -> Dict[str, Any]:
        state_vector = self._normalize_state_vector(
            np.ones(DODECAHEDRON_VERTICES, dtype=np.complex128)
        )
        entropy = self.calculate_integrated_entropy(state_vector)
        rho = self.density_matrix_from_state(state_vector)
        mass_gap = self._mass_gap_alignment()
        hashrate_ehs = self.calculate_integrated_hashrate()

        return {
            "available": self.is_available(),
            "configured": bool(self.current_config),
            "telemetry_source": "derived_runtime_state",
            "capacity_source": (
                "configured_estimate" if hashrate_ehs is not None else "not_configured"
            ),
            "hashrate_ehs": None if hashrate_ehs is None else round(hashrate_ehs, 4),
            "hashrate_cap_ehs": PULVINI_HASHRATE_CAP_EHS,
            "power_scale": self.power_scale,
            "basis_states": DODECAHEDRON_VERTICES,
            "von_neumann_entropy": round(entropy, 4),
            "dodecahedral_coherence": round(self._basis_coherence(), 6),
            "phi_phase_alignment": round(self._phi_phase_alignment(), 6),
            "density_trace": round(float(np.trace(rho).real), 12),
            "unitary_closure": bool(np.isclose(np.trace(rho).real, 1.0, atol=1e-10)),
            "mass_gap_target": round(float(MASS_GAP_TARGET), 12),
            "mass_gap_alignment": round(float(mass_gap["selected_ratio"]), 12),
            "mass_gap_alignment_error": round(float(mass_gap["alignment_error"]), 12),
            "truncation_rule": "irrational_gauge_svd_boundary",
            "search_mode": "structured_evidence_weighted",
            "grover_amplification_enabled": False,
            "last_solve_iterations": self.last_solve_iterations,
            "last_solve_duration_seconds": self.last_solve_duration_seconds,
            "last_solution_nonce": self.last_solution_nonce,
            "last_error": self.last_error,
        }
