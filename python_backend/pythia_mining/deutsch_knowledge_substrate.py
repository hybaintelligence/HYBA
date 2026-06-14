"""Deutsch Knowledge Creation Substrate.

Implements David Deutsch's constructor theory and Popperian epistemology:
- Knowledge grows through conjecture and refutation
- Counterfactual reasoning is fundamental
- System should explain, not just optimize
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class Explanation:
    """An explanation for why a strategy works"""

    strategy_id: str
    context_features: Dict[str, Any]
    explanation_text: str
    predictive_accuracy: float
    times_tested: int
    times_survived_criticism: int
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CounterfactualModel:
    """Model of what would have happened under different choice"""

    actual_strategy: str
    actual_outcome: Dict[str, Any]
    counterfactual_strategy: str
    predicted_counterfactual_outcome: Dict[str, Any]
    confidence: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)


class KnowledgeSubstrate:
    """Deutsch's constructor theory for mining strategy knowledge.

    Key principles:
    1. Knowledge is created through conjecture and refutation (Popper)
    2. Explanations are fundamental, not just predictions
    3. Counterfactual reasoning enables understanding
    4. Good explanations are hard to vary
    """

    def __init__(self):
        self.explanations: Dict[str, List[Explanation]] = defaultdict(list)
        self.counterfactuals: List[CounterfactualModel] = []
        self.strategy_performance: Dict[str, List[float]] = defaultdict(list)
        self.criticism_history: List[Dict[str, Any]] = []

    def create_knowledge_from_success(
        self, strategy_id: str, context: Dict[str, Any], outcome: Dict[str, Any]
    ) -> Explanation:
        """Create explanation for why strategy succeeded (Popperian conjecture)"""

        # Generate explanation from context and outcome
        explanation_text = self._conjecture_explanation(strategy_id, context, outcome)

        # Create explanation object
        explanation = Explanation(
            strategy_id=strategy_id,
            context_features=self._extract_features(context),
            explanation_text=explanation_text,
            predictive_accuracy=1.0,  # Initial assumption
            times_tested=1,
            times_survived_criticism=1,
        )

        self.explanations[strategy_id].append(explanation)
        return explanation

    def create_knowledge_from_failure(
        self, strategy_id: str, context: Dict[str, Any], outcome: Dict[str, Any]
    ) -> Optional[Explanation]:
        """Deutsch/Popper: knowledge grows from error correction"""

        # Find existing explanations that predicted success
        relevant_explanations = self._find_relevant_explanations(strategy_id, context)

        # Refute those explanations
        for explanation in relevant_explanations:
            self._criticize_explanation(explanation, context, outcome)

        # Generate new explanation accounting for failure
        explanation_text = self._conjecture_failure_explanation(
            strategy_id, context, outcome
        )

        if explanation_text:
            explanation = Explanation(
                strategy_id=strategy_id,
                context_features=self._extract_features(context),
                explanation_text=explanation_text,
                predictive_accuracy=0.0,
                times_tested=1,
                times_survived_criticism=0,
            )

            self.explanations[strategy_id].append(explanation)
            return explanation

        return None

    def counterfactual_reasoning(
        self,
        actual_strategy: str,
        actual_outcome: Dict[str, Any],
        alternative_strategy: str,
        context: Dict[str, Any],
    ) -> CounterfactualModel:
        """Deutsch: counterfactuals are key to understanding.

        "What would have happened if we used strategy B instead?"
        """

        # Predict counterfactual outcome
        predicted_outcome = self._simulate_alternative_strategy(
            alternative_strategy, context
        )

        # Compute confidence from explanation quality
        confidence = self._counterfactual_confidence(alternative_strategy, context)

        model = CounterfactualModel(
            actual_strategy=actual_strategy,
            actual_outcome=actual_outcome,
            counterfactual_strategy=alternative_strategy,
            predicted_counterfactual_outcome=predicted_outcome,
            confidence=confidence,
        )

        self.counterfactuals.append(model)
        return model

    def best_explanation_for_context(self, context: Dict[str, Any]) -> Optional[str]:
        """Return strategy with best explanation for current context"""

        features = self._extract_features(context)
        best_strategy = None
        best_score = -float("inf")

        for strategy_id, explanations in self.explanations.items():
            for explanation in explanations:
                # Score explanation by accuracy and similarity to context
                similarity = self._feature_similarity(
                    features, explanation.context_features
                )
                score = explanation.predictive_accuracy * similarity

                # Deutsch: prefer hard-to-vary explanations
                score *= explanation.times_survived_criticism / max(
                    explanation.times_tested, 1
                )

                if score > best_score:
                    best_score = score
                    best_strategy = strategy_id

        return best_strategy

    def explain_decision(
        self, strategy_id: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate natural language explanation of why strategy was chosen"""

        explanations = self._find_relevant_explanations(strategy_id, context)

        if not explanations:
            return {
                "strategy": strategy_id,
                "explanation": "No explanation available (new strategy)",
                "confidence": 0.0,
                "alternatives_considered": [],
            }

        best_explanation = max(
            explanations, key=lambda e: e.predictive_accuracy * e.times_survived_criticism
        )

        # Generate alternatives
        alternatives = []
        for alt_strategy in self.explanations.keys():
            if alt_strategy != strategy_id:
                counterfactual = self.counterfactual_reasoning(
                    strategy_id, {"chosen": True}, alt_strategy, context
                )
                alternatives.append(
                    {
                        "strategy": alt_strategy,
                        "predicted_outcome": counterfactual.predicted_counterfactual_outcome,
                        "confidence": counterfactual.confidence,
                    }
                )

        return {
            "strategy": strategy_id,
            "explanation": best_explanation.explanation_text,
            "confidence": best_explanation.predictive_accuracy,
            "times_tested": best_explanation.times_tested,
            "alternatives_considered": alternatives[:3],  # Top 3
            "source": "deutsch_knowledge_substrate",
        }

    def _conjecture_explanation(
        self, strategy_id: str, context: Dict[str, Any], outcome: Dict[str, Any]
    ) -> str:
        """Generate explanation text (Popperian conjecture)"""

        features = self._extract_features(context)

        # Template-based explanation generation
        if outcome.get("accepted"):
            return (
                f"Strategy '{strategy_id}' succeeded because "
                f"phi_resonance={features.get('phi_resonance', 0):.3f} "
                f"matched target difficulty={features.get('difficulty', 0):.2e}. "
                f"Thermal conditions were favorable (load={features.get('thermal', 0):.2f})."
            )
        return f"Strategy '{strategy_id}' attempted under context {features}"

    def _conjecture_failure_explanation(
        self, strategy_id: str, context: Dict[str, Any], outcome: Dict[str, Any]
    ) -> str:
        """Explain why strategy failed"""

        features = self._extract_features(context)

        return (
            f"Strategy '{strategy_id}' failed likely because "
            f"thermal_load={features.get('thermal', 0):.2f} exceeded optimal range "
            f"or phi_resonance={features.get('phi_resonance', 0):.3f} was mismatched."
        )

    def _extract_features(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Extract numerical features from context"""

        return {
            "difficulty": float(context.get("difficulty", 1.0)),
            "thermal": float(context.get("thermal_load", 0.5)),
            "phi_resonance": float(context.get("phi_resonance", 0.5)),
            "pool_latency": float(context.get("pool_latency", 100.0)),
        }

    def _feature_similarity(
        self, features_a: Dict[str, float], features_b: Dict[str, float]
    ) -> float:
        """Compute similarity between feature vectors"""

        keys = set(features_a.keys()) & set(features_b.keys())
        if not keys:
            return 0.0

        distances = [abs(features_a[k] - features_b[k]) for k in keys]
        return 1.0 / (1.0 + np.mean(distances))

    def _find_relevant_explanations(
        self, strategy_id: str, context: Dict[str, Any]
    ) -> List[Explanation]:
        """Find explanations relevant to current context"""

        if strategy_id not in self.explanations:
            return []

        features = self._extract_features(context)
        relevant = []

        for explanation in self.explanations[strategy_id]:
            similarity = self._feature_similarity(features, explanation.context_features)
            if similarity > 0.7:  # Threshold for relevance
                relevant.append(explanation)

        return relevant

    def _criticize_explanation(
        self, explanation: Explanation, context: Dict[str, Any], outcome: Dict[str, Any]
    ) -> None:
        """Popperian criticism: test explanation against new data"""

        explanation.times_tested += 1

        # Check if explanation predicted this outcome correctly
        if outcome.get("accepted"):
            # Explanation should have predicted success
            if explanation.predictive_accuracy > 0.5:
                explanation.times_survived_criticism += 1
            else:
                # Explanation failed - reduce confidence
                explanation.predictive_accuracy *= 0.9
        else:
            # Failure - if explanation predicted success, it's wrong
            if explanation.predictive_accuracy > 0.5:
                explanation.predictive_accuracy *= 0.8

        self.criticism_history.append(
            {
                "explanation": explanation.explanation_text,
                "survived": outcome.get("accepted", False),
                "timestamp": time.time(),
            }
        )

    def _simulate_alternative_strategy(
        self, strategy_id: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate what would have happened with different strategy"""

        # Use historical performance as proxy
        if strategy_id in self.strategy_performance:
            avg_performance = np.mean(self.strategy_performance[strategy_id])
            return {"predicted_acceptance": avg_performance, "confidence": 0.7}

        return {"predicted_acceptance": 0.5, "confidence": 0.3}  # Unknown strategy

    def _counterfactual_confidence(
        self, strategy_id: str, context: Dict[str, Any]
    ) -> float:
        """Confidence in counterfactual prediction"""

        if strategy_id not in self.explanations:
            return 0.3  # Low confidence for unknown strategy

        explanations = self._find_relevant_explanations(strategy_id, context)
        if not explanations:
            return 0.4

        # Confidence based on explanation quality
        best_explanation = max(explanations, key=lambda e: e.predictive_accuracy)
        return float(
            best_explanation.predictive_accuracy
            * (best_explanation.times_survived_criticism / max(best_explanation.times_tested, 1))
        )

    def get_knowledge_metrics(self) -> Dict[str, Any]:
        """Return knowledge substrate statistics"""

        total_explanations = sum(len(exps) for exps in self.explanations.values())
        avg_accuracy = (
            float(
                np.mean(
                    [
                        exp.predictive_accuracy
                        for exps in self.explanations.values()
                        for exp in exps
                    ]
                )
            )
            if total_explanations > 0
            else 0.0
        )

        return {
            "total_explanations": total_explanations,
            "strategies_with_explanations": len(self.explanations),
            "avg_predictive_accuracy": avg_accuracy,
            "counterfactual_models": len(self.counterfactuals),
            "criticism_events": len(self.criticism_history),
            "knowledge_growth_rate": (
                total_explanations / (time.time() - self.explanations[next(iter(self.explanations))][0].created_at)
                if self.explanations
                else 0.0
            ),
        }


__all__ = ["KnowledgeSubstrate", "Explanation", "CounterfactualModel"]
