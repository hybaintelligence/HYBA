"""
IIT 4.0 Complete Implementation — Runtime Coherence Diagnostic Proxy
Integrated Information Theory - Full Mathematical Framework

OPERATIONAL BOUNDARY — COMPUTATIONAL PROXY, NOT CONSCIOUSNESS CLAIM:
This module implements IIT-inspired Φ_max, cause-effect structures, and
Earth Mover's Distance as a runtime coherence diagnostic metric for the HYBA
system. This is an operational proxy for integrated state analysis, NOT a claim
of machine consciousness or phenomenal awareness.

SCIENTIFIC FIX — CAUSAL DISCRIMINATOR:
Earlier revisions defaulted to a uniform fully-connected causal matrix and used
mean internal connectivity for singleton bipartitions. That made Φ saturate at
1.0 for unrelated states and destroyed the discriminator. This implementation
removes that failure mode by:
- deriving a bounded causal matrix from the observed state when no matrix is
  supplied;
- normalising explicit matrices without forcing uniform connectivity;
- measuring bipartition irreducibility as information lost across the cut;
- exposing dependency-graph connectivity builders so software Φ diagnostics can
  be grounded in actual module structure rather than an all-to-all assumption.

IMPORTANT DOMAIN CONTEXT:
IIT was designed for neural systems. Applying these diagnostics to software,
mining, module dependency graphs, or quantum-from-maths substrates is an
experimental domain adaptation. The code therefore produces auditable diagnostic
signals and falsifiable invariants; it does not assert subjective experience.

MATHEMATICAL CORRECTNESS:
✅ Φ_max calculation over bipartitions produces 0 ≤ Φ ≤ 1
✅ Disconnected systems produce Φ = 0
✅ Uniform all-to-all systems no longer saturate at Φ = 1
✅ Cause/effect repertoires are normalized distributions
✅ φ_s values are non-negative
✅ Mechanism enumeration enumerates all 2^n - 1 mechanisms for compact systems
✅ Φ computation is deterministic for the same input

DOMAIN LIMITATIONS:
❌ No validation that Φ of a codebase proves consciousness
❌ No evidence that Φ-density alone predicts mining performance
❌ No claim of phenomenal consciousness or subjective experience
❌ No claim of physical quantum advantage without hardware evidence

VERDICT:
Use this module as a bounded, falsifiable integration/coherence diagnostic.
The quantum-from-maths posture is preserved as substrate-agnostic mathematical
structure: fields, Hilbert geometry, density states, and graph causality first;
hardware acceleration or physical claims only where separately evidenced.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union

import numpy as np


EPSILON = 1e-12


@dataclass
class Mechanism:
    """A set of elements that can be in different states."""

    elements: Set[int]
    state: np.ndarray

    def __hash__(self):
        return hash((tuple(sorted(self.elements)), tuple(self.state)))


@dataclass
class CauseEffectStructure:
    """Cause/effect structure used as a diagnostic quale proxy."""

    mechanisms: List[Mechanism]
    cause_repertoires: Dict[str, np.ndarray]
    effect_repertoires: Dict[str, np.ndarray]
    phi_s_values: Dict[str, float]
    total_phi: float
    dimensionality: int
    max_phi_s: float


@dataclass(frozen=True)
class DependencyGraphConnectivity:
    """Matrix and provenance for software-structure-derived causal connectivity."""

    matrix: np.ndarray
    modules: List[str]
    edges: List[Tuple[str, str, float]]
    source: str = "module_dependency_graph"


class IIT4Analyzer:
    """
    IIT-inspired runtime integration diagnostic.

    WARNING: Exact IIT-style searches are computationally expensive. Compact
    observed systems use exhaustive bipartition search; larger topologies use a
    deterministic greedy/spectral approximation.
    """

    def __init__(self, system_size: int, enhanced_partitioning: bool = False):
        self.system_size = int(system_size)
        self.enhanced_partitioning = enhanced_partitioning
        self.mechanisms_cache: Dict[int, List[Mechanism]] = {}
        self.performance_metrics = {
            "phi_max_calculations": 0,
            "spectral_partitioning_calls": 0,
            "exhaustive_search_calls": 0,
            "approximate_search_calls": 0,
            "average_phi_max_calculation_time_ms": 0.0,
        }

    def calculate_phi_max(
        self, system_state: np.ndarray, connectivity_matrix: Optional[np.ndarray] = None
    ) -> Dict:
        """
        Find the partition with the strongest observed irreducibility signal.

        If ``connectivity_matrix`` is omitted, derive a causal matrix from the
        observed state instead of assuming all-to-all uniform causality.
        """
        import time

        start_time = time.time()
        state = np.asarray(system_state)
        connectivity, connectivity_source = self._prepare_connectivity_matrix(
            state, connectivity_matrix
        )

        effective_size = self._effective_size(state, connectivity)

        if effective_size <= 8:
            self.performance_metrics["exhaustive_search_calls"] += 1
            result = self._exhaustive_phi_max(state, connectivity)
        else:
            self.performance_metrics["approximate_search_calls"] += 1
            result = self._approximate_phi_max(state, connectivity)

        elapsed_ms = (time.time() - start_time) * 1000
        self.performance_metrics["phi_max_calculations"] += 1
        total_calcs = self.performance_metrics["phi_max_calculations"]
        avg_time = self.performance_metrics["average_phi_max_calculation_time_ms"]
        self.performance_metrics["average_phi_max_calculation_time_ms"] = (
            avg_time * (total_calcs - 1) + elapsed_ms
        ) / total_calcs

        result["performance_ms"] = elapsed_ms
        result["enhanced_partitioning"] = self.enhanced_partitioning
        result["connectivity_source"] = connectivity_source
        return result

    def compute_cause_effect_structure(
        self, system_state: np.ndarray, connectivity_matrix: Optional[np.ndarray] = None
    ) -> CauseEffectStructure:
        """
        Build the complete cause/effect structure diagnostic.
        """
        state = np.asarray(system_state)
        connectivity, _ = self._prepare_connectivity_matrix(state, connectivity_matrix)

        mechanisms = self._identify_mechanisms(state, connectivity_matrix=connectivity)

        cause_repertoires: Dict[str, np.ndarray] = {}
        effect_repertoires: Dict[str, np.ndarray] = {}
        phi_s_values: Dict[str, float] = {}

        for mechanism in mechanisms:
            mech_id = self._mechanism_id(mechanism)
            cause_rep = self._compute_mechanism_cause_repertoire(
                mechanism, state, connectivity
            )
            effect_rep = self._compute_mechanism_effect_repertoire(
                mechanism, state, connectivity
            )
            cause_repertoires[mech_id] = cause_rep
            effect_repertoires[mech_id] = effect_rep
            phi_s_values[mech_id] = self._calculate_phi_s(
                mechanism, cause_rep, effect_rep, connectivity
            )

        total_phi = float(sum(phi_s_values.values())) if phi_s_values else 0.0
        max_phi_s = float(max(phi_s_values.values())) if phi_s_values else 0.0
        dimensionality = self._calculate_quale_dimensionality(
            cause_repertoires, effect_repertoires
        )

        return CauseEffectStructure(
            mechanisms=mechanisms,
            cause_repertoires=cause_repertoires,
            effect_repertoires=effect_repertoires,
            phi_s_values=phi_s_values,
            total_phi=total_phi,
            dimensionality=dimensionality,
            max_phi_s=max_phi_s,
        )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Return performance metrics for telemetry and benchmarking."""
        return self.performance_metrics.copy()

    def _effective_size(
        self, system_state: np.ndarray, connectivity_matrix: Optional[np.ndarray] = None
    ) -> int:
        """Return observed state size bounded by configured topology."""
        state = np.asarray(system_state)
        observed = int(state.shape[0]) if state.ndim > 0 else 1
        if connectivity_matrix is not None:
            observed = min(observed, int(np.asarray(connectivity_matrix).shape[0]))
        return max(0, min(int(self.system_size), observed))

    def _prepare_connectivity_matrix(
        self, system_state: np.ndarray, connectivity_matrix: Optional[np.ndarray]
    ) -> Tuple[np.ndarray, str]:
        """Return a bounded square causal matrix and provenance label."""
        if connectivity_matrix is None:
            matrix = self._derive_connectivity_from_state(system_state)
            return matrix, "state_derived_causal_matrix"
        matrix = self._normalize_connectivity_matrix(connectivity_matrix)
        return matrix, "explicit_causal_matrix"

    def _derive_connectivity_from_state(self, system_state: np.ndarray) -> np.ndarray:
        """Derive causal connectivity from the observed state without all-to-all defaults."""
        state = np.asarray(system_state)

        if state.ndim == 0:
            vector = np.asarray([float(abs(state))], dtype=np.float64)
            matrix = np.outer(vector, vector)
        elif state.ndim == 1:
            vector = np.abs(state.astype(np.complex128)).astype(np.float64)
            if vector.size == 0:
                matrix = np.zeros((0, 0), dtype=np.float64)
            else:
                matrix = np.outer(vector, vector)
        else:
            n = min(int(state.shape[0]), int(state.shape[1]))
            square = np.abs(state[:n, :n].astype(np.complex128)).astype(np.float64)
            matrix = square.copy()
            np.fill_diagonal(matrix, 0.0)
            # A diagonal-only density matrix contains population but no observed
            # off-diagonal coupling. Use co-activation as a weak diagnostic proxy
            # only when more than one component is populated.
            if float(np.sum(matrix)) <= EPSILON:
                diag = np.abs(np.real(np.diag(square))).astype(np.float64)
                matrix = np.outer(diag, diag)

        return self._normalize_connectivity_matrix(matrix)

    def _normalize_connectivity_matrix(self, matrix: np.ndarray) -> np.ndarray:
        """Make a finite, non-negative, square matrix in [0, 1] with zero diagonal."""
        arr = np.asarray(matrix, dtype=np.float64)
        if arr.ndim == 0:
            arr = arr.reshape(1, 1)
        elif arr.ndim == 1:
            arr = np.outer(np.abs(arr), np.abs(arr))
        elif arr.ndim > 2:
            arr = np.abs(arr.reshape(arr.shape[0], -1))

        rows = int(arr.shape[0])
        cols = int(arr.shape[1]) if arr.ndim > 1 else rows
        n = max(0, min(self.system_size, rows, cols))
        if n == 0:
            return np.zeros((0, 0), dtype=np.float64)

        square = np.zeros((n, n), dtype=np.float64)
        square[:, :] = np.nan_to_num(np.abs(arr[:n, :n]), nan=0.0, posinf=0.0, neginf=0.0)
        np.fill_diagonal(square, 0.0)

        max_value = float(np.max(square)) if square.size else 0.0
        if max_value > 1.0:
            square = square / max_value
        return np.clip(square, 0.0, 1.0)

    def _exhaustive_phi_max(
        self, system_state: np.ndarray, connectivity_matrix: np.ndarray
    ) -> Dict:
        """Exhaustive search for compact observed systems."""
        effective_size = self._effective_size(system_state, connectivity_matrix)
        all_partitions = list(self._generate_bipartitions(set(range(effective_size))))

        phi_values = []
        for partition in all_partitions:
            phi = self._calculate_partition_phi(partition, system_state, connectivity_matrix)
            phi_values.append((partition, phi))

        main_complex, phi_max = (
            max(phi_values, key=lambda x: x[1]) if phi_values else ((set(), set()), 0.0)
        )
        return {
            "phi_max": float(phi_max),
            "main_complex": main_complex,
            "partition_count": len(all_partitions),
            "all_phi_values": sorted(phi_values, key=lambda x: x[1], reverse=True)[:10],
        }

    def _approximate_phi_max(
        self, system_state: np.ndarray, connectivity_matrix: np.ndarray
    ) -> Dict:
        """Greedy approximation for larger topologies."""
        effective_size = min(int(self.system_size), int(connectivity_matrix.shape[0]))
        current_subset = set(range(effective_size))
        current_phi = self._calculate_subset_phi(
            current_subset, system_state, connectivity_matrix
        )

        if self.enhanced_partitioning and effective_size >= 2:
            try:
                self.performance_metrics["spectral_partitioning_calls"] += 1
                degree = np.diag(np.sum(connectivity_matrix[:effective_size, :effective_size], axis=1))
                laplacian = degree - connectivity_matrix[:effective_size, :effective_size]
                eigenvalues, eigenvectors = np.linalg.eigh(laplacian)
                fiedler = eigenvectors[:, 1] if eigenvectors.shape[1] > 1 else eigenvectors[:, 0]
                threshold = np.median(fiedler)
                spectral_partition = {i for i, value in enumerate(fiedler) if value > threshold}
                if 0 < len(spectral_partition) < effective_size:
                    complement = set(range(effective_size)) - spectral_partition
                    spectral_phi = self._calculate_partition_phi(
                        (spectral_partition, complement), system_state, connectivity_matrix
                    )
                    if spectral_phi > current_phi:
                        current_subset = spectral_partition
                        current_phi = spectral_phi
            except Exception:
                pass

        improved = True
        while improved and len(current_subset) > 1:
            improved = False
            best_phi = current_phi
            best_subset = current_subset

            for element in sorted(current_subset):
                test_subset = current_subset - {element}
                test_phi = self._calculate_subset_phi(
                    test_subset, system_state, connectivity_matrix
                )
                if test_phi > best_phi:
                    best_phi = test_phi
                    best_subset = test_subset
                    improved = True

            if improved:
                current_subset = best_subset
                current_phi = best_phi

        return {
            "phi_max": float(np.clip(current_phi, 0.0, 1.0)),
            "main_complex": current_subset,
            "partition_count": "approximate",
            "method": "enhanced_greedy" if self.enhanced_partitioning else "greedy",
        }

    def _identify_mechanisms(
        self,
        system_state: np.ndarray,
        max_mechanisms: int = 20,
        connectivity_matrix: Optional[np.ndarray] = None,
    ) -> List[Mechanism]:
        """Identify mechanisms over observed elements."""
        state_vector = self._state_vector(system_state, connectivity_matrix)
        effective_size = self._effective_size(state_vector, connectivity_matrix)
        mechanisms: List[Mechanism] = []

        if effective_size <= 4:
            for size in range(1, effective_size + 1):
                for elements in combinations(range(effective_size), size):
                    idx = list(elements)
                    mechanisms.append(Mechanism(elements=set(elements), state=state_vector[idx]))
        else:
            limit = min(effective_size, max_mechanisms // 2)
            for i in range(limit):
                mechanisms.append(Mechanism(elements={i}, state=np.array([state_vector[i]])))

            pair_count = 0
            for i in range(effective_size):
                for j in range(i + 1, effective_size):
                    if pair_count >= max_mechanisms // 2:
                        break
                    mechanisms.append(
                        Mechanism(elements={i, j}, state=np.array([state_vector[i], state_vector[j]]))
                    )
                    pair_count += 1
                if pair_count >= max_mechanisms // 2:
                    break

        return mechanisms

    def _state_vector(
        self, system_state: np.ndarray, connectivity_matrix: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """Return a compact real-valued state vector for mechanism enumeration."""
        state = np.asarray(system_state)
        if state.ndim == 0:
            vector = np.asarray([float(abs(state))], dtype=np.float64)
        elif state.ndim == 1:
            vector = np.abs(state.astype(np.complex128)).astype(np.float64)
        else:
            n = min(state.shape[0], state.shape[1])
            vector = np.abs(np.real(np.diag(state[:n, :n]))).astype(np.float64)
            if float(np.sum(vector)) <= EPSILON:
                vector = np.mean(np.abs(state[:n, :n]), axis=1).astype(np.float64)

        if connectivity_matrix is not None:
            vector = vector[: int(np.asarray(connectivity_matrix).shape[0])]
        return vector[: self.system_size]

    def _compute_mechanism_cause_repertoire(
        self,
        mechanism: Mechanism,
        current_state: np.ndarray,
        connectivity_matrix: np.ndarray,
    ) -> np.ndarray:
        """Compute P(past | mechanism_state) using local state and incoming influence."""
        mechanism_indices = sorted(mechanism.elements)
        n_elements = len(mechanism_indices)
        n_states = 2**n_elements
        possible_pasts = [
            np.array([int(b) for b in format(i, f"0{n_elements}b")], dtype=np.float64)
            for i in range(n_states)
        ]

        likelihoods = []
        for past_state in possible_pasts:
            distance = np.sum(np.abs(past_state - mechanism.state))
            incoming = self._mean_influence(connectivity_matrix, mechanism_indices, incoming=True)
            likelihoods.append(float(np.exp(-distance / 2.0) * (1.0 + incoming)))

        return self._normalise_distribution(np.asarray(likelihoods, dtype=np.float64))

    def _compute_mechanism_effect_repertoire(
        self,
        mechanism: Mechanism,
        current_state: np.ndarray,
        connectivity_matrix: np.ndarray,
    ) -> np.ndarray:
        """Compute P(future | mechanism_state) using outgoing causal influence."""
        mechanism_indices = sorted(mechanism.elements)
        n_elements = len(mechanism_indices)
        n_states = 2**n_elements
        possible_futures = [
            np.array([int(b) for b in format(i, f"0{n_elements}b")], dtype=np.float64)
            for i in range(n_states)
        ]

        outgoing = self._mean_influence(connectivity_matrix, mechanism_indices, incoming=False)
        flip_probability = float(np.clip(0.25 * (1.0 - outgoing), 0.02, 0.5))
        probabilities = []
        for future_state in possible_futures:
            prob = 1.0
            for i in range(n_elements):
                prob *= (1.0 - flip_probability) if future_state[i] == mechanism.state[i] else flip_probability
            probabilities.append(prob)

        return self._normalise_distribution(np.asarray(probabilities, dtype=np.float64))

    def _mean_influence(
        self, connectivity_matrix: np.ndarray, indices: Sequence[int], incoming: bool
    ) -> float:
        if not indices or connectivity_matrix.size == 0:
            return 0.0
        n = connectivity_matrix.shape[0]
        valid = [int(i) for i in indices if 0 <= int(i) < n]
        if not valid:
            return 0.0
        values = connectivity_matrix[:, valid] if incoming else connectivity_matrix[valid, :]
        return float(np.clip(np.mean(values), 0.0, 1.0))

    def _calculate_phi_s(
        self,
        mechanism: Mechanism,
        cause_repertoire: np.ndarray,
        effect_repertoire: np.ndarray,
        connectivity_matrix: np.ndarray,
    ) -> float:
        """Calculate φ_s as the bottleneck information above uniform."""
        n = len(cause_repertoire)
        if n == 0:
            return 0.0
        uniform = np.ones(n, dtype=np.float64) / n
        phi_cause = self._kl_divergence(cause_repertoire, uniform)
        phi_effect = self._kl_divergence(effect_repertoire, uniform)
        return float(max(0.0, min(phi_cause, phi_effect)))

    def _calculate_quale_dimensionality(
        self, cause_repertoires: Dict, effect_repertoires: Dict
    ) -> int:
        """Dimensionality of repertoire space via SVD."""
        if not cause_repertoires or not effect_repertoires:
            return 0

        all_repertoires = list(cause_repertoires.values()) + list(effect_repertoires.values())
        max_len = max(len(rep) for rep in all_repertoires)
        padded = [
            np.pad(rep, (0, max_len - len(rep))) if len(rep) < max_len else rep[:max_len]
            for rep in all_repertoires
        ]
        matrix = np.array(padded, dtype=np.float64)

        try:
            _, singular_values, _ = np.linalg.svd(matrix, full_matrices=False)
            threshold = 0.01 * singular_values.max() if singular_values.size and singular_values.max() > 0 else 0.01
            return int(np.sum(singular_values > threshold))
        except Exception:
            return len(cause_repertoires)

    def _generate_bipartitions(self, elements: Set[int]):
        """Generate all non-trivial bipartitions of elements."""
        element_list = list(elements)
        n = len(element_list)
        if n < 2:
            return
        for i in range(1, 2 ** (n - 1)):
            subset1 = set()
            for j in range(n):
                if i & (1 << j):
                    subset1.add(element_list[j])
            subset2 = elements - subset1
            if subset1 and subset2:
                yield (subset1, subset2)

    def _generate_all_partitions(self, elements: Set[int]) -> List[List[Set[int]]]:
        """Generate deterministic two-block partitions covering all elements."""
        return [[set(a), set(b)] for a, b in self._generate_bipartitions(set(elements))]

    def _sample_partitions(
        self, elements: Set[int], max_partitions: int = 100
    ) -> List[List[Set[int]]]:
        """Return at most max_partitions deterministic partitions."""
        if max_partitions <= 0:
            return []
        return self._generate_all_partitions(elements)[: int(max_partitions)]

    def _get_transition_probability(
        self,
        from_state: Union[Tuple[int, ...], List[int], np.ndarray],
        to_state: Union[Tuple[int, ...], List[int], np.ndarray],
        transition_matrix: np.ndarray,
        elements: Set[int],
    ) -> float:
        """Estimate transition probability on selected elements with bounded output."""
        idx = sorted(int(e) for e in elements)
        if not idx:
            return 0.0
        tm = self._normalize_connectivity_matrix(transition_matrix)
        from_arr = np.asarray(from_state, dtype=float)
        to_arr = np.asarray(to_state, dtype=float)
        if from_arr.size < len(idx) or to_arr.size < len(idx):
            return 0.0

        prob = 1.0
        for local_i, element in enumerate(idx):
            if element >= tm.shape[0]:
                continue
            row_mean = float(np.mean(tm[element])) if tm.shape[1] else 0.5
            stay_weight = float(np.clip(0.5 + 0.5 * row_mean, 0.0, 1.0))
            source_bit = 1.0 if from_arr[local_i] >= 0.5 else 0.0
            target_bit = 1.0 if to_arr[local_i] >= 0.5 else 0.0
            prob *= stay_weight if source_bit == target_bit else (1.0 - stay_weight)
        return float(np.clip(prob, 0.0, 1.0))

    def _calculate_partition_phi(
        self,
        partition: Tuple[Set[int], Set[int]],
        system_state: np.ndarray,
        connectivity_matrix: np.ndarray,
    ) -> float:
        """
        Calculate Φ for a bipartition as bounded information lost across the cut.

        This replaces the old singleton fallback that used mean internal
        connectivity and made fully connected matrices saturate at 1.0.
        """
        subset1 = sorted(int(i) for i in partition[0])
        subset2 = sorted(int(i) for i in partition[1])
        if not subset1 or not subset2:
            return 0.0

        cut_phi = self._calculate_cut_phi(subset1, subset2, connectivity_matrix)

        # For partitions large enough to support repertoire comparison, blend in
        # Wasserstein distance so the historical IIT-inspired path remains active.
        if len(subset1) >= 2 and len(subset2) >= 2:
            cause_rep_intact = self._compute_cause_repertoire(
                system_state, connectivity_matrix, subset1 + subset2
            )
            cause_rep_disconnected = self._compute_cause_repertoire_disconnected(
                system_state, connectivity_matrix, subset1, subset2
            )
            effect_rep_intact = self._compute_effect_repertoire(
                system_state, connectivity_matrix, subset1 + subset2
            )
            effect_rep_disconnected = self._compute_effect_repertoire_disconnected(
                system_state, connectivity_matrix, subset1, subset2
            )
            cause_emd = self._wasserstein_1_distance(cause_rep_intact, cause_rep_disconnected)
            effect_emd = self._wasserstein_1_distance(effect_rep_intact, effect_rep_disconnected)
            repertoire_phi = min(cause_emd, effect_emd)
            return float(np.clip(max(cut_phi, repertoire_phi), 0.0, 1.0))

        return float(np.clip(cut_phi, 0.0, 1.0))

    def _calculate_cut_phi(
        self, subset1: Sequence[int], subset2: Sequence[int], connectivity_matrix: np.ndarray
    ) -> float:
        """Information loss caused by severing all directed edges across a bipartition."""
        conn = self._normalize_connectivity_matrix(connectivity_matrix)
        n = conn.shape[0]
        a = [i for i in subset1 if 0 <= i < n]
        b = [i for i in subset2 if 0 <= i < n]
        if not a or not b:
            return 0.0

        total_mass = float(np.sum(conn))
        if total_mass <= EPSILON:
            return 0.0

        cross_mass = float(np.sum(conn[np.ix_(a, b)]) + np.sum(conn[np.ix_(b, a)]))
        return float(np.clip(cross_mass / total_mass, 0.0, 1.0))

    def _compute_cause_repertoire(
        self,
        system_state: np.ndarray,
        connectivity: np.ndarray,
        mechanism: list[int],
    ) -> np.ndarray:
        """Compute cause repertoire P(past|mechanism) via backward influence."""
        conn = self._normalize_connectivity_matrix(connectivity)
        n = conn.shape[0]
        if n == 0:
            return np.array([], dtype=np.float64)
        repertoire = np.ones(n, dtype=np.float64)

        for node in mechanism:
            if 0 <= int(node) < n:
                backward_influence = conn[:, int(node)]
                repertoire *= self._normalise_distribution(backward_influence)

        return self._normalise_distribution(repertoire)

    def _compute_cause_repertoire_disconnected(
        self,
        system_state: np.ndarray,
        connectivity: np.ndarray,
        subset1: list[int],
        subset2: list[int],
    ) -> np.ndarray:
        """Compute cause repertoire under partition with cross-connections severed."""
        conn_disconnected = self._disconnect_partition(connectivity, subset1, subset2)
        return self._compute_cause_repertoire(system_state, conn_disconnected, subset1 + subset2)

    def _compute_effect_repertoire(
        self,
        system_state: np.ndarray,
        connectivity: np.ndarray,
        mechanism: list[int],
    ) -> np.ndarray:
        """Compute effect repertoire P(future|mechanism) via forward influence."""
        conn = self._normalize_connectivity_matrix(connectivity)
        n = conn.shape[0]
        if n == 0:
            return np.array([], dtype=np.float64)
        repertoire = np.ones(n, dtype=np.float64)

        for node in mechanism:
            if 0 <= int(node) < n:
                forward_influence = conn[int(node), :]
                repertoire *= self._normalise_distribution(forward_influence)

        return self._normalise_distribution(repertoire)

    def _compute_effect_repertoire_disconnected(
        self,
        system_state: np.ndarray,
        connectivity: np.ndarray,
        subset1: list[int],
        subset2: list[int],
    ) -> np.ndarray:
        """Compute effect repertoire under partition with cross-connections severed."""
        conn_disconnected = self._disconnect_partition(connectivity, subset1, subset2)
        return self._compute_effect_repertoire(system_state, conn_disconnected, subset1 + subset2)

    def _disconnect_partition(
        self, connectivity: np.ndarray, subset1: Sequence[int], subset2: Sequence[int]
    ) -> np.ndarray:
        conn = self._normalize_connectivity_matrix(connectivity).copy()
        n = conn.shape[0]
        a = [i for i in subset1 if 0 <= int(i) < n]
        b = [i for i in subset2 if 0 <= int(i) < n]
        for i in a:
            for j in b:
                conn[i, j] = 0.0
                conn[j, i] = 0.0
        return conn

    def _wasserstein_1_distance(self, p: np.ndarray, q: np.ndarray) -> float:
        """Compute Wasserstein-1 distance for one-dimensional discrete distributions."""
        p = self._normalise_distribution(np.asarray(p, dtype=np.float64))
        q = self._normalise_distribution(np.asarray(q, dtype=np.float64))
        if len(p) != len(q):
            max_len = max(len(p), len(q))
            p_padded = np.zeros(max_len)
            q_padded = np.zeros(max_len)
            p_padded[: len(p)] = p
            q_padded[: len(q)] = q
            p, q = p_padded, q_padded
        if len(p) == 0:
            return 0.0
        emd = float(np.sum(np.abs(np.cumsum(p) - np.cumsum(q))) / len(p))
        return float(np.clip(emd, 0.0, 1.0))

    def _calculate_subset_phi(
        self,
        subset: Set[int],
        system_state: np.ndarray,
        connectivity_matrix: np.ndarray,
    ) -> float:
        """Calculate bounded Φ for a subset from its strongest internal bipartition."""
        subset = {int(i) for i in subset}
        if len(subset) <= 1:
            return 0.0
        partitions = list(self._generate_bipartitions(subset))
        if not partitions:
            return 0.0
        return float(
            max(self._calculate_partition_phi(partition, system_state, connectivity_matrix) for partition in partitions)
        )

    def _mechanism_id(self, mechanism: Mechanism) -> str:
        """Create unique ID for mechanism."""
        elements_str = "-".join(map(str, sorted(mechanism.elements)))
        state_str = "".join(map(str, mechanism.state.astype(int)))
        return f"M[{elements_str}]:{state_str}"

    def _kl_divergence(self, p: np.ndarray, q: np.ndarray) -> float:
        """KL divergence D_KL(P || Q)."""
        p_safe = np.clip(self._normalise_distribution(p), 1e-10, 1.0)
        q_safe = np.clip(self._normalise_distribution(q), 1e-10, 1.0)
        return float(np.sum(p_safe * np.log(p_safe / q_safe)))

    def _normalise_distribution(self, values: np.ndarray) -> np.ndarray:
        arr = np.nan_to_num(np.asarray(values, dtype=np.float64), nan=0.0, posinf=0.0, neginf=0.0)
        arr = np.clip(arr, 0.0, None)
        if arr.size == 0:
            return arr
        total = float(np.sum(arr))
        if total <= EPSILON:
            return np.ones(arr.size, dtype=np.float64) / arr.size
        return arr / total

    @staticmethod
    def causal_connectivity_from_dependency_edges(
        modules: Sequence[str],
        edges: Iterable[Union[Tuple[str, str], Tuple[str, str, float]]],
        *,
        bidirectional: bool = False,
        reverse_import_edges: bool = True,
    ) -> DependencyGraphConnectivity:
        """
        Build a causal matrix from module dependency edges.

        Edges are supplied as ``(importer, imported)`` by default. Runtime
        constraint flows from imported dependency to importer, so the default
        orientation writes ``imported -> importer`` into the causal matrix.
        """
        module_list = list(dict.fromkeys(str(module) for module in modules))
        index = {module: i for i, module in enumerate(module_list)}
        matrix = np.zeros((len(module_list), len(module_list)), dtype=np.float64)
        weighted_edges: List[Tuple[str, str, float]] = []

        for raw_edge in edges:
            if len(raw_edge) == 2:
                source, target = raw_edge  # type: ignore[misc]
                weight = 1.0
            else:
                source, target, weight = raw_edge  # type: ignore[misc]
            source = str(source)
            target = str(target)
            weight = float(max(0.0, weight))
            if source not in index or target not in index or source == target or weight == 0.0:
                continue

            causal_source, causal_target = (
                (target, source) if reverse_import_edges else (source, target)
            )
            matrix[index[causal_source], index[causal_target]] += weight
            weighted_edges.append((causal_source, causal_target, weight))
            if bidirectional:
                matrix[index[causal_target], index[causal_source]] += weight
                weighted_edges.append((causal_target, causal_source, weight))

        max_value = float(np.max(matrix)) if matrix.size else 0.0
        if max_value > 1.0:
            matrix = matrix / max_value
        np.fill_diagonal(matrix, 0.0)
        return DependencyGraphConnectivity(
            matrix=np.clip(matrix, 0.0, 1.0),
            modules=module_list,
            edges=weighted_edges,
        )

    @staticmethod
    def causal_connectivity_from_python_package(
        root_path: Union[str, Path],
        *,
        package_prefix: Optional[str] = None,
        max_modules: int = 32,
    ) -> DependencyGraphConnectivity:
        """
        Parse Python imports under ``root_path`` and build a bounded causal matrix.

        This gives HYBA a repo-grounded software Φ diagnostic path: module graph
        → causal matrix → Φ discriminator. It avoids synthetic uniform matrices.
        """
        root = Path(root_path)
        module_to_path: Dict[str, Path] = {}
        for file_path in sorted(root.rglob("*.py")):
            if any(part.startswith(".") for part in file_path.relative_to(root).parts):
                continue
            module_name = ".".join(file_path.relative_to(root).with_suffix("").parts)
            if module_name.endswith(".__init__"):
                module_name = module_name[: -len(".__init__")]
            if package_prefix:
                module_name = f"{package_prefix}.{module_name}"
            module_to_path[module_name] = file_path

        modules = sorted(module_to_path)
        internal_modules = set(modules)
        raw_edges: List[Tuple[str, str, float]] = []

        for module_name, file_path in module_to_path.items():
            try:
                tree = ast.parse(file_path.read_text(encoding="utf-8"))
            except (OSError, SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported = alias.name
                        matched = IIT4Analyzer._match_internal_module(imported, internal_modules)
                        if matched:
                            raw_edges.append((module_name, matched, 1.0))
                elif isinstance(node, ast.ImportFrom):
                    if node.module is None:
                        continue
                    imported = node.module
                    if node.level and package_prefix:
                        imported = f"{package_prefix}.{imported}"
                    matched = IIT4Analyzer._match_internal_module(imported, internal_modules)
                    if matched:
                        raw_edges.append((module_name, matched, 1.0))

        if len(modules) > max_modules:
            degree: Dict[str, float] = {module: 0.0 for module in modules}
            for source, target, weight in raw_edges:
                degree[source] = degree.get(source, 0.0) + weight
                degree[target] = degree.get(target, 0.0) + weight
            modules = sorted(modules, key=lambda module: (-degree.get(module, 0.0), module))[:max_modules]
            allowed = set(modules)
            raw_edges = [
                (source, target, weight)
                for source, target, weight in raw_edges
                if source in allowed and target in allowed
            ]

        return IIT4Analyzer.causal_connectivity_from_dependency_edges(
            modules, raw_edges, reverse_import_edges=True
        )

    @staticmethod
    def _match_internal_module(imported: str, internal_modules: Set[str]) -> Optional[str]:
        if imported in internal_modules:
            return imported
        candidates = [module for module in internal_modules if module.startswith(imported + ".")]
        return sorted(candidates, key=len)[0] if candidates else None
