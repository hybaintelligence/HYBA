"""Persisted ontological memory for peak deterministic reflection states."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


class CrystallineRegistry:
    """Persist peak Φ states as mathematical artifacts, not source edits."""

    def __init__(self, filepath: str | Path | None = None):
        configured = (
            filepath
            or os.getenv("HYBA_ONTOLOGICAL_STATE_PATH")
            or os.getenv("HYBA_ONTOLOGICAL_PERSISTENCE_PATH")
        )
        self.filepath = Path(configured) if configured else Path("logs/ontological_state.json")

    def save_peak_state(self, phi: float, weights: Dict[str, Any]) -> Dict[str, Any]:
        """Store only the most resonant state seen so far."""

        current = self.load_best_reality()
        if current and float(current.get("phi", 0.0)) > float(phi):
            return current
        state = {
            "phi": round(float(phi), 6),
            "weights": dict(weights),
            "seal": "PHI_CERTIFIED",
            "persistence": "mathematical_artifact_no_source_write",
        }
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.filepath.write_text(json.dumps(state, sort_keys=True, indent=2), encoding="utf-8")
        return state

    def persist(self, phi: float, weights: Dict[str, Any]) -> Dict[str, Any]:
        """Compatibility alias for save_peak_state."""

        return self.save_peak_state(phi, weights)

    def retrieve_grace(self) -> Dict[str, Any]:
        """Compatibility alias for load_best_reality."""

        return self.load_best_reality()

    def load_best_reality(self) -> Dict[str, Any]:
        if not self.filepath.exists():
            return {}
        try:
            payload = json.loads(self.filepath.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}
