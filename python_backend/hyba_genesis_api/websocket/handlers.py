"""
WebSocket Handlers
HYBA Genesis Platform Real-Time Stream Handlers
"""

from typing import Any, Dict
from datetime import datetime, timezone


class WebSocketHandler:
    """Real-time stream facade.

    The handler deliberately avoids fabricated mining telemetry. Until a caller
    injects a live telemetry provider, it reports an unavailable state that the
    frontend can render honestly.
    """

    def __init__(self, telemetry_provider=None):
        self.telemetry_provider = telemetry_provider

    async def get_current_metrics(self) -> Dict[str, Any]:
        if self.telemetry_provider is not None:
            return await self.telemetry_provider.get_current_metrics()
        return {
            "status": "unavailable",
            "telemetry_source": "not_configured",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "No live websocket telemetry provider configured.",
        }
