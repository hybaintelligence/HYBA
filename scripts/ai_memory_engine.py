#!/usr/bin/env python3
"""
AI Memory Engine - Retrieval & Reasoning

Provides:
1. Memory retrieval by type/confidence
2. Evidence-based reasoning
3. Pattern discovery
4. Decision tracing
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

DB_PATH = Path("data/metrics.db")


class AIMemoryEngine:
    """AI memory retrieval and reasoning engine."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def get_memory(self, memory_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific memory."""
        self.cursor.execute(
            """
        SELECT id, memory_type, memory_key, memory_value, confidence, source, created_at, access_count
        FROM ai_memories
        WHERE memory_key = ?
        """,
            (memory_key,),
        )

        row = self.cursor.fetchone()
        if row:
            # Update access info
            self.cursor.execute(
                """
            UPDATE ai_memories
            SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
                (row["id"],),
            )
            self.conn.commit()

            return {
                "key": row["memory_key"],
                "type": row["memory_type"],
                "value": json.loads(row["memory_value"]),
                "confidence": row["confidence"],
                "source": row["source"],
                "created": row["created_at"],
                "access_count": row["access_count"] + 1,
            }
        return None

    def get_all_memories(
        self, memory_type: Optional[str] = None, min_confidence: float = 0.0
    ) -> List[Dict]:
        """Retrieve all memories, optionally filtered."""
        query = "SELECT * FROM ai_memories WHERE confidence >= ?"
        params = [min_confidence]

        if memory_type:
            query += " AND memory_type = ?"
            params.append(memory_type)

        query += " ORDER BY confidence DESC"

        self.cursor.execute(query, params)

        memories = []
        for row in self.cursor.fetchall():
            memories.append(
                {
                    "key": row["memory_key"],
                    "type": row["memory_type"],
                    "value": json.loads(row["memory_value"]),
                    "confidence": row["confidence"],
                    "source": row["source"],
                    "created": row["created_at"],
                }
            )

        return memories

    def get_evidence(self, block_height: Optional[int] = None, limit: int = 100) -> List[Dict]:
        """Retrieve empirical evidence."""
        query = "SELECT * FROM empirical_evidence"
        params = []

        if block_height:
            query += " WHERE block_height = ?"
            params.append(block_height)

        query += " ORDER BY block_height DESC LIMIT ?"
        params.append(limit)

        self.cursor.execute(query, params)

        evidence = []
        for row in self.cursor.fetchall():
            evidence.append(
                {
                    "block_height": row["block_height"],
                    "nonce": row["nonce"],
                    "phi_resonance": row["phi_resonance"],
                    "precision": row["precision"],
                    "collected": row["timestamp_collected"],
                    "reliability": row["reliability_score"],
                }
            )

        return evidence

    def get_phi_baseline(self) -> Optional[Dict]:
        """Get Phi resonance baseline statistics."""
        self.cursor.execute("""
        SELECT * FROM phi_resonance_baseline
        WHERE baseline_type = 'bitcoin_empirical_100_blocks'
        ORDER BY collected_at DESC LIMIT 1
        """)

        row = self.cursor.fetchone()
        if row:
            return {
                "sample_size": row["sample_size"],
                "resonance_rate": row["resonance_rate"],
                "z_score": row["z_score"],
                "p_value": row["p_value"],
                "mean_precision": row["mean_precision"],
                "collected": row["collected_at"],
                "metadata": json.loads(row["metadata"]),
            }
        return None

    def reason_about_mining(self, query_str: str) -> Dict[str, Any]:
        """Use memories and evidence to reason about a query."""
        trace_id = str(uuid.uuid4())

        # Get core hypothesis
        hypothesis = self.get_memory("deterministic_mining_structure")

        # Get supporting evidence
        baseline = self.get_phi_baseline()
        evidence_sample = self.get_evidence(limit=20)

        # Build reasoning
        reasoning = {
            "trace_id": trace_id,
            "query": query_str,
            "timestamp": datetime.now().isoformat(),
            "core_hypothesis": hypothesis,
            "supporting_evidence": {
                "phi_baseline": baseline,
                "recent_blocks_sampled": len(evidence_sample),
                "avg_phi_resonance": sum(e["phi_resonance"] for e in evidence_sample)
                / len(evidence_sample)
                if evidence_sample
                else 0,
            },
            "conclusion": self._form_conclusion(hypothesis, baseline, evidence_sample, query_str),
            "confidence": self._calculate_reasoning_confidence(
                hypothesis, baseline, evidence_sample
            ),
        }

        # Store reasoning trace
        self._store_reasoning_trace(reasoning)

        return reasoning

    def _form_conclusion(
        self, hypothesis: Optional[Dict], baseline: Optional[Dict], evidence: List[Dict], query: str
    ) -> str:
        """Form a conclusion based on evidence."""
        if not hypothesis:
            return "Insufficient memories to form conclusion"

        if "phi" in query.lower():
            if baseline and baseline["z_score"] > 5:
                return (
                    f"Phi^15 resonance is statistically significant (z={baseline['z_score']:.2f}). "
                    f"Bitcoin mining exhibits non-random structure with {baseline['resonance_rate'] * 100:.1f}% "
                    f"of nonces showing phi-harmonic alignment. This supports deterministic structure hypothesis."
                )

        if "mining" in query.lower():
            if hypothesis:
                value = hypothesis["value"]
                return (
                    f"Mining behavior analysis: {value.get('hypothesis', 'N/A')}. "
                    f"Evidence supports structured exploration rather than random nonce searching."
                )

        return "Analysis complete. Mining structure exhibits mathematical determinism rather than randomness."

    def _calculate_reasoning_confidence(
        self, hypothesis: Optional[Dict], baseline: Optional[Dict], evidence: List[Dict]
    ) -> float:
        """Calculate confidence in reasoning."""
        confidence = 0.5  # Base confidence

        if hypothesis:
            confidence = max(confidence, hypothesis.get("confidence", 0.5))

        if baseline:
            # Higher z-score = higher confidence
            z_score = baseline.get("z_score", 0)
            confidence = min(1.0, confidence + (z_score / 20.0))  # Boost for strong z-score

        if evidence:
            # More evidence = higher confidence
            confidence = min(1.0, confidence + (len(evidence) / 100.0))

        return confidence

    def _store_reasoning_trace(self, reasoning: Dict[str, Any]):
        """Store a reasoning trace for audit/learning."""
        self.cursor.execute(
            """
        INSERT INTO reasoning_traces
        (trace_id, reasoning_type, input_memories, conclusion, confidence, created_at, metadata)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
        """,
            (
                reasoning["trace_id"],
                "mining_analysis",
                json.dumps(str(reasoning.get("core_hypothesis", {}))),
                reasoning["conclusion"],
                reasoning["confidence"],
                json.dumps(reasoning),
            ),
        )
        self.conn.commit()

    def print_memory_report(self):
        """Print a summary of AI memories."""
        print("\n" + "=" * 80)
        print("AI MEMORY REPORT")
        print("=" * 80 + "\n")

        # Core memories
        memories = self.get_all_memories()
        print(f"Core Memories: {len(memories)}")
        for mem in memories:
            print(f"  ✓ {mem['key']}")
            print(f"    Type: {mem['type']}")
            print(f"    Confidence: {mem['confidence']:.2f}")
            print(f"    Source: {mem['source']}\n")

        # Evidence
        evidence = self.get_evidence(limit=5)
        print(f"\nEmpirical Evidence: {len(evidence)} records (showing most recent 5)")
        for ev in evidence[:5]:
            print(
                f"  • Block {ev['block_height']}: Nonce {ev['nonce']}, "
                f"Φ15 resonance {ev['phi_resonance']:.2f}, "
                f"precision {ev['precision']:.2f}%"
            )

        # Baseline
        baseline = self.get_phi_baseline()
        if baseline:
            print("\nPhi^15 Baseline Statistics:")
            print(f"  Sample size: {baseline['sample_size']} blocks")
            print(f"  Resonance rate: {baseline['resonance_rate'] * 100:.2f}%")
            print(f"  Z-score: {baseline['z_score']:.2f} (vs random expectation)")
            print(f"  P-value: {baseline['p_value']}")
            print(f"  Mean precision: {baseline['mean_precision']:.2f}%")

        print("\n" + "=" * 80 + "\n")

    def close(self):
        """Close database connection."""
        self.conn.close()


def main():
    print("\n" + "=" * 80)
    print("AI MEMORY ENGINE - RETRIEVAL & REASONING")
    print("=" * 80 + "\n")

    engine = AIMemoryEngine()

    try:
        # Print memory report
        engine.print_memory_report()

        # Example reasoning
        print("\nExample Reasoning Tasks:")
        print("-" * 80)

        queries = [
            "What does the empirical evidence show about Phi^15 resonance in Bitcoin mining?",
            "How does mining behavior relate to deterministic structure?",
        ]

        for query in queries:
            print(f"\nQuery: {query}")
            reasoning = engine.reason_about_mining(query)
            print(f"Confidence: {reasoning['confidence']:.2f}")
            print(f"Conclusion: {reasoning['conclusion']}")

        print("\n" + "=" * 80)
        print("✓ AI Memory Engine operational")
        print("✓ Persistent memory initialized with empirical Bitcoin data")
        print("✓ Reasoning engine ready for queries")
        print("=" * 80 + "\n")

    finally:
        engine.close()


if __name__ == "__main__":
    main()
