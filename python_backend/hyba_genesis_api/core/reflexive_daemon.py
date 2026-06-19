"""Asynchronous heartbeat for explicitly enabled reflexive closure cycles."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List

from hyba_genesis_api.core.recursive_closure import RecursiveClosure
from hyba_genesis_api.core.reflexive_controller import ReflexiveController

LOGGER = logging.getLogger(__name__)


class IntelligenceHeartbeat:
    """Autonomic heartbeat that runs closure cycles only when explicitly started."""

    def __init__(self, controller: ReflexiveController, closure: RecursiveClosure):
        self.controller = controller
        self.closure = closure
        self.is_active = False
        self.history: List[Dict[str, Any]] = []

    async def pulse(self, interval_seconds: float = 60.0, max_pulses: int | None = None) -> None:
        """Run governed closure cycles asynchronously without blocking callers."""

        if interval_seconds < 0:
            raise ValueError("interval_seconds must be non-negative")
        self.is_active = True
        pulses = 0
        while self.is_active:
            result = self.closure.sync_learning()
            self.history.append(result)
            LOGGER.info("Intelligence heartbeat pulse", extra={"heartbeat": result["status"]})
            pulses += 1
            if max_pulses is not None and pulses >= max_pulses:
                self.stop()
                break
            await asyncio.sleep(interval_seconds)

    def stop(self) -> None:
        self.is_active = False

    def snapshot(self) -> Dict[str, Any]:
        return {
            "is_active": self.is_active,
            "pulses": len(self.history),
            "history": list(self.history),
        }
