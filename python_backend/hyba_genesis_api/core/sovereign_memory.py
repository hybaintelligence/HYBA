"""Sovereign Memory Layer.

Ensures the memory substrate is truly sovereign:
- φ-fold compression integrity (lossless round-trip)
- No foreign-trained embeddings
- Entropy bounds maintained
- Memory operations are deterministic and auditable

Sovereignty in computation is meaningless if memory comes from foreign sources.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass(frozen=True)
class MemoryAttestation:
    """Proof of sovereign memory property."""

    property_name: str
    passed: bool
    message: str
    evidence_hash: str
    details: Dict[str, Any]


class SovereignMemoryValidator:
    """Validates that memory operations maintain sovereignty."""

    def __init__(self):
        self._phi = (1.0 + math.sqrt(5.0)) / 2.0
        self._phi_inv = 1.0 / self._phi

    def verify_phi_fold_integrity(
        self,
        *,
        original_data: np.ndarray,
        folded_data: np.ndarray,
        unfolded_data: np.ndarray,
        tolerance: float = 1e-14,
    ) -> MemoryAttestation:
        """Verify φ-fold compression maintains lossless properties.

        Sovereignty requires that compression does not introduce foreign
        approximations or lossy steps. φ-fold must be reversible.

        Args:
            original_data: Original data before folding
            folded_data: Data after φ-fold compression
            unfolded_data: Data after unfolding (should match original)
            tolerance: Numerical tolerance for floating-point comparison

        Returns:
            MemoryAttestation with proof of integrity
        """
        original_flat = original_data.flatten()
        unfolded_flat = unfolded_data.flatten()

        # Check round-trip fidelity
        if len(original_flat) != len(unfolded_flat):
            return MemoryAttestation(
                property_name="phi_fold_integrity",
                passed=False,
                message="φ-fold round-trip failed: shape mismatch",
                evidence_hash=hashlib.sha256(
                    json.dumps(
                        {
                            "original_shape": original_data.shape,
                            "unfolded_shape": unfolded_data.shape,
                        },
                        default=str,
                    ).encode()
                ).hexdigest(),
                details={
                    "original_shape": original_data.shape,
                    "unfolded_shape": unfolded_data.shape,
                    "error": "shape_mismatch",
                },
            )

        max_error = float(np.max(np.abs(original_flat - unfolded_flat)))
        passed = max_error <= tolerance

        evidence = {
            "max_error": max_error,
            "tolerance": tolerance,
            "passed": passed,
            "original_dtype": str(original_data.dtype),
            "folded_size": folded_data.nbytes,
            "compression_ratio": original_data.nbytes / folded_data.nbytes if folded_data.nbytes > 0 else 0,
        }
        evidence_str = json.dumps(evidence, default=str, sort_keys=True)
        evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()

        return MemoryAttestation(
            property_name="phi_fold_integrity",
            passed=passed,
            message=f"{'✅ PASS' if passed else '❌ FAIL'}: φ-fold round-trip max_error = {max_error:.2e} vs tolerance {tolerance:.2e}",
            evidence_hash=evidence_hash,
            details=evidence,
        )

    def verify_round_trip_losslessness(
        self,
        *,
        forward_transform: callable,
        inverse_transform: callable,
        test_data: np.ndarray,
        num_trials: int = 100,
        tolerance: float = 1e-14,
    ) -> MemoryAttestation:
        """Verify a memory transform is lossless across multiple round-trips.

        Sovereignty requires deterministic, reversible operations. No
        randomness, approximation, or information loss.

        Args:
            forward_transform: Function to compress/transform data
            inverse_transform: Function to decompress/untransform
            test_data: Data to test on
            num_trials: Number of round-trip trials
            tolerance: Acceptable numerical error

        Returns:
            MemoryAttestation
        """
        max_errors = []
        failures = []

        for trial in range(num_trials):
            try:
                transformed = forward_transform(test_data)
                reconstructed = inverse_transform(transformed)

                error = float(np.max(np.abs(test_data.flatten() - reconstructed.flatten())))
                max_errors.append(error)

                if error > tolerance:
                    failures.append(
                        f"Trial {trial}: error {error:.2e} exceeds tolerance"
                    )
            except Exception as e:
                failures.append(f"Trial {trial}: {str(e)}")

        passed = len(failures) == 0 and all(e <= tolerance for e in max_errors)
        max_error_overall = max(max_errors) if max_errors else 0.0

        evidence = {
            "num_trials": num_trials,
            "trials_passed": num_trials - len(failures),
            "max_error_across_trials": max_error_overall,
            "tolerance": tolerance,
            "failures": failures[:5],  # Report first 5 failures
        }
        evidence_str = json.dumps(evidence, default=str, sort_keys=True)
        evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()

        return MemoryAttestation(
            property_name="round_trip_losslessness",
            passed=passed,
            message=f"{'✅ PASS' if passed else '❌ FAIL'}: {num_trials - len(failures)}/{num_trials} round-trip trials, max_error = {max_error_overall:.2e}",
            evidence_hash=evidence_hash,
            details=evidence,
        )

    def verify_entropy_bounds(
        self,
        *,
        data: np.ndarray,
        min_entropy: float = 0.1,
        max_entropy: float = 7.9,
    ) -> MemoryAttestation:
        """Verify memory entropy is within sovereign bounds.

        Foreign systems may inject:
        - Near-zero entropy (suspicious compression)
        - Maximum entropy (randomness injection)

        Sovereign memory should have natural entropy bounds.

        Args:
            data: Data to analyze
            min_entropy: Minimum acceptable entropy (bits/element)
            max_entropy: Maximum acceptable entropy (bits/element)

        Returns:
            MemoryAttestation
        """
        flat_data = data.flatten()

        # Compute empirical entropy
        if len(flat_data) == 0:
            return MemoryAttestation(
                property_name="entropy_bounds",
                passed=False,
                message="Cannot compute entropy on empty data",
                evidence_hash="",
                details={"error": "empty_data"},
            )

        # Normalize to [0, 1] for entropy calculation
        data_min = np.min(flat_data)
        data_max = np.max(flat_data)
        if data_max == data_min:
            normalized = np.zeros_like(flat_data)
        else:
            normalized = (flat_data - data_min) / (data_max - data_min)

        # Histogram-based entropy
        bins = 256
        hist, _ = np.histogram(normalized, bins=bins, range=(0, 1))
        hist = hist / np.sum(hist)  # Normalize
        hist = hist[hist > 0]  # Remove zeros
        entropy = -np.sum(hist * np.log2(hist))

        # Entropy should be between min and max (in bits)
        passed = min_entropy <= entropy <= max_entropy

        evidence = {
            "computed_entropy": entropy,
            "min_bound": min_entropy,
            "max_bound": max_entropy,
            "data_range": (float(data_min), float(data_max)),
            "data_shape": data.shape,
        }
        evidence_str = json.dumps(evidence, default=str, sort_keys=True)
        evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()

        return MemoryAttestation(
            property_name="entropy_bounds",
            passed=passed,
            message=f"{'✅ PASS' if passed else '❌ FAIL'}: entropy = {entropy:.3f} bits, bounds = [{min_entropy}, {max_entropy}]",
            evidence_hash=evidence_hash,
            details=evidence,
        )

    def verify_no_foreign_embeddings(
        self,
        *,
        embedding_source: Optional[str] = None,
        embedding_model: Optional[str] = None,
    ) -> MemoryAttestation:
        """Verify memory does not depend on foreign-trained embeddings.

        Forbidden sources:
        - OpenAI
        - Google
        - HuggingFace
        - Anthropic
        - Any vendor-trained latent space

        Args:
            embedding_source: Claimed source of embeddings
            embedding_model: Claimed embedding model name

        Returns:
            MemoryAttestation
        """
        forbidden_sources = {
            "openai",
            "google",
            "huggingface",
            "anthropic",
            "cohere",
            "replicate",
            "aleph-alpha",
        }
        forbidden_models = {
            "text-embedding-3",
            "bert",
            "gpt",
            "palm",
            "llama2",
            "mistral",
            "claude",
            "embeddings-gecko",
        }

        violations = []

        if embedding_source:
            if any(f in embedding_source.lower() for f in forbidden_sources):
                violations.append(
                    f"Foreign embedding source detected: {embedding_source}"
                )

        if embedding_model:
            if any(f in embedding_model.lower() for f in forbidden_models):
                violations.append(
                    f"Foreign embedding model detected: {embedding_model}"
                )

        passed = len(violations) == 0

        evidence = {
            "embedding_source": embedding_source,
            "embedding_model": embedding_model,
            "violations": violations,
        }
        evidence_str = json.dumps(evidence, default=str, sort_keys=True)
        evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()

        return MemoryAttestation(
            property_name="no_foreign_embeddings",
            passed=passed,
            message=f"{'✅ PASS' if passed else '❌ FAIL'}: embedding source check - {len(violations)} violations",
            evidence_hash=evidence_hash,
            details=evidence,
        )

    def verify_deterministic_operations(
        self,
        *,
        operation: callable,
        test_input: np.ndarray,
        num_runs: int = 10,
    ) -> MemoryAttestation:
        """Verify memory operations are deterministic (reproducible).

        Sovereignty requires no randomness in core operations.
        Same input should produce identical output every time.

        Args:
            operation: Function to test
            test_input: Test data
            num_runs: Number of iterations

        Returns:
            MemoryAttestation
        """
        results = []
        for _ in range(num_runs):
            try:
                result = operation(test_input.copy())
                results.append(result)
            except Exception as e:
                return MemoryAttestation(
                    property_name="deterministic_operations",
                    passed=False,
                    message=f"Operation raised exception: {str(e)}",
                    evidence_hash="",
                    details={"error": str(e)},
                )

        # Check all results are identical
        first_result = results[0]
        identical = True
        for result in results[1:]:
            try:
                if not np.allclose(first_result.flatten(), result.flatten(), atol=1e-15):
                    identical = False
                    break
            except Exception:
                identical = False
                break

        passed = identical

        evidence = {
            "num_runs": num_runs,
            "deterministic": identical,
        }
        evidence_str = json.dumps(evidence, default=str, sort_keys=True)
        evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()

        return MemoryAttestation(
            property_name="deterministic_operations",
            passed=passed,
            message=f"{'✅ PASS' if passed else '❌ FAIL'}: {num_runs} runs {'all identical' if identical else 'produced different results'}",
            evidence_hash=evidence_hash,
            details=evidence,
        )


__all__ = [
    "MemoryAttestation",
    "SovereignMemoryValidator",
]
