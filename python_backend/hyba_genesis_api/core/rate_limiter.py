"""
Simple in-memory rate limiting middleware.

This middleware enforces a maximum number of requests per client IP within a time window.
It's intended as a lightweight mechanism to deter abuse and protect shared resources.
For production deployments, consider using a distributed cache (e.g. Redis) or
API gateway rate limiting.

Environment variables:
- HYBA_RATE_LIMIT_REQUESTS_PER_MINUTE: max requests per window (default: 120)
- HYBA_RATE_LIMIT_WINDOW_SECONDS: window length in seconds (default: 60)
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
        # Determine limits from arguments or environment variables
        self.max_requests = max_requests or int(os.getenv("HYBA_RATE_LIMIT_REQUESTS_PER_MINUTE", "120"))
        self.window = window_seconds or int(os.getenv("HYBA_RATE_LIMIT_WINDOW_SECONDS", "60"))
        # Track request timestamps by client IP
        self._access_log: Dict[str, Deque[float]] = defaultdict(deque)
        logging.info(
            "RateLimiter enabled: %s requests per %s seconds window",
            self.max_requests,
            self.window,
        )

    async def dispatch(self, request: Request, call_next):
        client_host = request.client.host if request.client else "unknown"
        now = time.time()
        timestamps = self._access_log[client_host]

        # Remove timestamps older than the sliding window
        while timestamps and now - timestamps[0] > self.window:
            timestamps.popleft()

        if len(timestamps) >= self.max_requests:
            # Too many requests: reject with 429
            logging.warning(
                "RateLimiter: rejecting request from %s due to rate limit",
                client_host,
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "Too Many Requests"},
            )

        # Record current request and proceed
        timestamps.append(now)
        return await call_next(request)
