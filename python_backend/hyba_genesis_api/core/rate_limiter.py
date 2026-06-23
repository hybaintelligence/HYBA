"""
In-memory rate limiting middleware with sliding window and stale-IP eviction.

Enforces a maximum number of requests per client IP within a time window.
For production deployments with multiple instances, use Redis or API gateway
rate limiting in addition to this middleware.

Environment variables:
- HYBA_RATE_LIMIT_REQUESTS_PER_MINUTE: max requests per window (default: 120)
- HYBA_RATE_LIMIT_WINDOW_SECONDS: window length in seconds (default: 60)
- HYBA_RATE_LIMIT_EVICTION_INTERVAL_SECONDS: how often to sweep stale IPs (default: 300)
"""

from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging


class RateLimiter(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int | None = None, window_seconds: int | None = None):
        super().__init__(app)
        self.max_requests = max_requests or int(
            os.getenv("HYBA_RATE_LIMIT_REQUESTS_PER_MINUTE", "120")
        )
        self.window = window_seconds or int(os.getenv("HYBA_RATE_LIMIT_WINDOW_SECONDS", "60"))
        self._eviction_interval = float(
            os.getenv("HYBA_RATE_LIMIT_EVICTION_INTERVAL_SECONDS", "300")
        )
        self._access_log: Dict[str, Deque[float]] = defaultdict(deque)
        self._last_eviction: float = time.time()
        logging.info(
            "RateLimiter enabled: %s requests per %s seconds window",
            self.max_requests,
            self.window,
        )

    def _evict_stale_ips(self, now: float) -> None:
        """Remove IPs whose entire deque falls outside the current window.

        Without this, every unique IP that ever hit the server would remain in
        memory permanently, causing unbounded growth under normal traffic.
        """
        if now - self._last_eviction < self._eviction_interval:
            return
        stale = [
            ip
            for ip, ts in self._access_log.items()
            if not ts or now - ts[-1] > self.window
        ]
        for ip in stale:
            del self._access_log[ip]
        self._last_eviction = now
        if stale:
            logging.debug("RateLimiter: evicted %d stale IP entries", len(stale))

    async def dispatch(self, request: Request, call_next):
        client_host = request.client.host if request.client else "unknown"
        now = time.time()

        self._evict_stale_ips(now)

        timestamps = self._access_log[client_host]

        # Slide the window forward
        while timestamps and now - timestamps[0] > self.window:
            timestamps.popleft()

        if len(timestamps) >= self.max_requests:
            retry_after = int(self.window - (now - timestamps[0])) + 1
            logging.warning(
                "RateLimiter: rejecting request from %s (retry after %ds)",
                client_host,
                retry_after,
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "Too Many Requests", "retry_after_seconds": retry_after},
                headers={"Retry-After": str(retry_after)},
            )

        timestamps.append(now)
        return await call_next(request)
