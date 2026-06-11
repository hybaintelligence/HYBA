"""
WebSocket Handlers
HYBA Genesis Platform Real-Time Stream Handlers
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from pythia_mining.metrics_store import get_metrics_store

LOGGER = logging.getLogger(__name__)


class WebSocketHandler:
    """Expose only activity-derived mining telemetry over realtime channels."""

    async def get_current_metrics(self) -> Dict[str, Any]:
        """Return persisted mining metrics or an explicit not-connected state.

        The realtime stream must never invent hashrate, share rates, quantum speedups,
        or pool counts. Every numeric value below is derived from persisted pool/share
        activity collected by the mining runtime.
        """

        try:
            pools = get_metrics_store().get_all_pool_metrics()
        except Exception as exc:
            LOGGER.exception("Failed to load websocket mining metrics")
            return {
                "status": "error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "metrics_store_error",
                "error": {
                    "type": exc.__class__.__name__,
                    "message": str(exc),
                },
            }

        active_pools = [pool for pool in pools if pool.last_pool_event_timestamp is not None]
        submitted = sum(pool.shares_submitted for pool in pools)
        accepted = sum(pool.shares_accepted for pool in pools)
        rejected = sum(pool.shares_rejected for pool in pools)
        acceptance_rate = accepted / submitted if submitted else None
        latencies = [pool.avg_latency_ms for pool in pools if pool.avg_latency_ms is not None]

        return {
            "status": "ok" if pools else "not_connected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "persisted_mining_activity",
            "hashrate": None,
            "shares_submitted": submitted,
            "shares_accepted": accepted,
            "shares_rejected": rejected,
            "acceptance_rate": acceptance_rate,
            "active_pools": len(active_pools),
            "avg_latency_ms": (sum(latencies) / len(latencies)) if latencies else None,
            "consciousness_level": None,
            "phi_resonance": None,
            "quantum_speedup": None,
            "message": None if pools else "No persisted mining activity is available yet.",
        }
