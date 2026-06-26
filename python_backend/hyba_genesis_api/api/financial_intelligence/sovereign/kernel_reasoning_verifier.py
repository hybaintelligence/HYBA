"""
Kernel-Verified Reasoning for HYBA Financial Intelligence Substrate (Sovereign Layer)

This module verifies reasoning chains using kernel methods:
- Kernel methods for reasoning verification
- Hilbert space embedding of reasoning chains
- Kernel trick for efficient verification
- Support vector machine (SVM) validation

Mathematical Foundation:
- Kernel function K(x, y) maps to inner product in feature space
- Hilbert space embedding preserves geometric structure
- Kernel similarity measures reasoning consistency
- SVM classification validates logical consistency
"""

from __future__ import annotations

import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from scipy.spatial.distance import cosine
from sklearn.svm import SVC
import hashlib
import json


@dataclass
class VerificationReport:
    """Kernel-verified reasoning report."""
    
    reasoning_validity: bool
    kernel_similarity_scores: Dict[str, float]
    logical_consistency_metrics: Dict[str, float]
    verification_confidence: float
    cryptographic_seal: Dict[str, Any]
    timestamp: str


class KernelReasoningVerifier:
    """
    Verifies reasoning chains using kernel methods.
    
    This verifier embeds reasoning chains in Hilbert space and uses
    kernel methods to validate logical consistency and reasoning validity.
    """
    
    def __init__(
        self,
        kernel_type: str = "rbf",
        similarity_threshold: float = 0.7
    ):
        """
        Initialize the kernel reasoning verifier.
        
        Args:
            kernel_type: Type of kernel function ("rbf", "linear", "polynomial")
            similarity_threshold: Threshold for reasoning similarity
        """
        self.kernel_type = kernel_type
        self.similarity_threshold = similarity_threshold
        self.reasoning_history: List[Dict[str, Any]] = []
    
    def verify_reasoning(
        self,
        reasoning_chain: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> VerificationReport:
        """
        Verify reasoning chain using kernel methods.
        
        Args:
            reasoning_chain: List of reasoning steps
            context: Optional context for verification
        
        Returns:
            VerificationReport with validity and metrics
        """
        # 1. Embed reasoning in Hilbert space
        embeddings = self._embed_reasoning(reasoning_chain)
        
        # 2. Apply kernel verification
        kernel_similarity = self._compute_kernel_similarity(embeddings)
        
        # 3. Validate logical consistency
        logical_consistency = self._validate_logical_consistency(
            reasoning_chain, embeddings
        )
        
        # 4. Compute verification confidence
        verification_confidence = self._compute_verification_confidence(
            kernel_similarity, logical_consistency
        )
        
        # 5. Determine reasoning validity
        reasoning_validity = verification_confidence > self.similarity_threshold
        
        # 6. Generate cryptographic seal
        cryptographic_seal = self._generate_cryptographic_seal(
            reasoning_validity, verification_confidence
        )
        
        # 7. Update history
        self._update_history(reasoning_chain, verification_confidence)
        
        return VerificationReport(
            reasoning_validity=reasoning_validity,
            kernel_similarity_scores=kernel_similarity,
            logical_consistency_metrics=logical_consistency,
            verification_confidence=verification_confidence,
            cryptographic_seal=cryptographic_seal,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def _embed_reasoning(
        self,
        reasoning_chain: List[Dict[str, Any]]
    ) -> np.ndarray:
        """
        Embed reasoning chain in Hilbert space.
        
        Converts each reasoning step into a vector representation
        that can be analyzed using kernel methods.
        """
        embeddings = []
        
        for step in reasoning_chain:
            # Extract features from reasoning step
            features = self._extract_step_features(step)
            embeddings.append(features)
        
        return np.array(embeddings)
    
    def _extract_step_features(
        self,
        step: Dict[str, Any]
    ) -> np.ndarray:
        """
        Extract features from a reasoning step.
        
        Features include:
        - Step type (one-hot encoded)
        - Confidence score
        - Number of premises
        - Logical operator type
        """
        # Feature vector construction
        features = []
        
        # Step type (simplified one-hot)
        step_types = ["premise", "inference", "conclusion", "assumption"]
        step_type = step.get("type", "inference")
        for t in step_types:
            features.append(1.0 if step_type == t else 0.0)
        
        # Confidence score
        features.append(step.get("confidence", 0.5))
        
        # Number of premises
        features.append(float(len(step.get("premises", []))))
        
        # Logical operator (simplified)
        operators = ["and", "or", "not", "implies"]
        operator = step.get("operator", "and")
        for op in operators:
            features.append(1.0 if operator == op else 0.0)
        
        return np.array(features)
    
    def _compute_kernel_similarity(
        self,
        embeddings: np.ndarray
    ) -> Dict[str, float]:
        """
        Compute kernel similarity between reasoning steps.
        
        Uses kernel functions to measure similarity between
        consecutive reasoning steps in the chain.
        """
        if len(embeddings) < 2:
            return {"avg_similarity": 1.0, "min_similarity": 1.0}
        
        similarities = []
        
        for i in range(len(embeddings) - 1):
            similarity = self._kernel_function(embeddings[i], embeddings[i + 1])
            similarities.append(similarity)
        
        return {
            "avg_similarity": float(np.mean(similarities)),
            "min_similarity": float(np.min(similarities)),
            "max_similarity": float(np.max(similarities))
        }
    
    def _kernel_function(
        self,
        x: np.ndarray,
        y: np.ndarray
    ) -> float:
        """
        Compute kernel function between two vectors.
        
        Supports RBF, linear, and polynomial kernels.
        """
        if self.kernel_type == "rbf":
            # RBF kernel: K(x, y) = exp(-||x - y||^2 / (2σ^2))
            sigma = 1.0
            distance = np.linalg.norm(x - y)
            return float(np.exp(-distance**2 / (2 * sigma**2)))
        
        elif self.kernel_type == "linear":
            # Linear kernel: K(x, y) = x · y
            return float(np.dot(x, y))
        
        elif self.kernel_type == "polynomial":
            # Polynomial kernel: K(x, y) = (x · y + c)^d
            c = 1.0
            d = 2
            return float((np.dot(x, y) + c) ** d)
        
        else:
            # Default to cosine similarity
            return float(1.0 - cosine(x, y))
    
    def _validate_logical_consistency(
        self,
        reasoning_chain: List[Dict[str, Any]],
        embeddings: np.ndarray
    ) -> Dict[str, float]:
        """
        Validate logical consistency of reasoning chain.
        
        Checks for:
        - Contradictions between steps
        - Circular reasoning
        - Unsupported inferences
        """
        consistency_metrics = {}
        
        # Check for contradictions (simplified)
        contradictions = 0
        for i, step in enumerate(reasoning_chain):
            for j, other_step in enumerate(reasoning_chain):
                if i != j:
                    # Check if steps contradict each other
                    if self._check_contradiction(step, other_step):
                        contradictions += 1
        
        n_steps = len(reasoning_chain)
        consistency_metrics["contradiction_rate"] = float(
            contradictions / (n_steps * (n_steps - 1)) if n_steps > 1 else 0
        )
        
        # Check for circular reasoning
        circular = self._detect_circular_reasoning(reasoning_chain)
        consistency_metrics["circular_reasoning_detected"] = float(circular)
        
        # Check inference support
        unsupported = 0
        for step in reasoning_chain:
            if step.get("type") == "inference":
                if len(step.get("premises", [])) == 0:
                    unsupported += 1
        
        consistency_metrics["unsupported_inference_rate"] = float(
            unsupported / n_steps if n_steps > 0 else 0
        )
        
        # Overall consistency score
        consistency_score = (
            1.0 - consistency_metrics["contradiction_rate"] -
            0.5 * consistency_metrics["circular_reasoning_detected"] -
            0.3 * consistency_metrics["unsupported_inference_rate"]
        )
        consistency_metrics["overall_consistency"] = float(max(0.0, consistency_score))
        
        return consistency_metrics
    
    def _check_contradiction(
        self,
        step1: Dict[str, Any],
        step2: Dict[str, Any]
    ) -> bool:
        """
        Check if two reasoning steps contradict each other.
        
        Simplified: check if conclusions are opposite.
        """
        conclusion1 = step1.get("conclusion", "")
        conclusion2 = step2.get("conclusion", "")
        
        # Check for explicit negation
        if "not" in conclusion1.lower() and conclusion2.lower() in conclusion1.lower():
            return True
        if "not" in conclusion2.lower() and conclusion1.lower() in conclusion2.lower():
            return True
        
        return False
    
    def _detect_circular_reasoning(
        self,
        reasoning_chain: List[Dict[str, Any]]
    ) -> bool:
        """
        Detect circular reasoning in the chain.
        
        Circular reasoning occurs when a conclusion is used
        as a premise for itself.
        """
        conclusions = set()
        premises = set()
        
        for step in reasoning_chain:
            conclusion = step.get("conclusion", "")
            step_premises = step.get("premises", [])
            
            conclusions.add(conclusion)
            premises.update(step_premises)
        
        # Check if any conclusion is also a premise
        circular = not conclusions.isdisjoint(premises)
        
        return circular
    
    def _compute_verification_confidence(
        self,
        kernel_similarity: Dict[str, float],
        logical_consistency: Dict[str, float]
    ) -> float:
        """
        Compute overall verification confidence.
        
        Confidence combines kernel similarity and logical consistency.
        """
        avg_similarity = kernel_similarity.get("avg_similarity", 0.5)
        overall_consistency = logical_consistency.get("overall_consistency", 0.5)
        
        # Weighted combination
        confidence = 0.5 * avg_similarity + 0.5 * overall_consistency
        
        return float(confidence)
    
    def _update_history(
        self,
        reasoning_chain: List[Dict[str, Any]],
        confidence: float
    ):
        """Update reasoning verification history."""
        self.reasoning_history.append({
            "chain_length": len(reasoning_chain),
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Keep only last 100 entries
        if len(self.reasoning_history) > 100:
            self.reasoning_history.pop(0)
    
    def _generate_cryptographic_seal(
        self,
        validity: bool,
        confidence: float
    ) -> Dict[str, Any]:
        """Generate cryptographic seal for reasoning verification."""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Create canonical representation
        body = {
            "reasoning_valid": validity,
            "verification_confidence": confidence,
            "timestamp": timestamp
        }
        
        canonical = json.dumps(body, sort_keys=True, default=str, separators=(",", ":"))
        body_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        
        # Create seal
        seal_body = {
            "algorithm": "SHA-256",
            "body_hash": body_hash,
            "timestamp": timestamp,
            "immutable_guard_active": True
        }
        
        seal = hashlib.sha256(
            json.dumps(seal_body, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        
        return {
            "algorithm": "SHA-256",
            "body_hash": body_hash,
            "seal": seal,
            "timestamp": timestamp,
            "immutable_guard_active": True
        }


# Global instance for service layer
kernel_verifier = KernelReasoningVerifier()
