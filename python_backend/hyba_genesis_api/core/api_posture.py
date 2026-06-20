"""Enterprise API posture controls for the HYBA Genesis backend.

This module provides the production-hardening envelope around the FastAPI
surface: request IDs, standard JSON error bodies, response security headers,
body-size protection, and lightweight in-process rate limiting for edge or
single-container deployments.

It deliberately does not replace upstream infrastructure controls such as API
Gateway, Cloud Armor/WAF, mTLS, IAM, or service mesh policy. Instead, it gives
HYBA a fail-closed application-layer baseline so the API behaves consistently in
local, Docker, and cloud runtimes.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any, Callable, Dict, Tuple

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status
from starlette.responses import Response


@dataclass(frozen=True)
class EnterpriseAPIConfig:
    """Runtime API posture settings loaded from environment variables."""

    environment: str
    request_limit_per_minute: int
    max_body_bytes: int
    hsts_enabled: bool
    rate_limit_enabled: bool
    csp_enabled: bool
    sanitize_production_errors: bool

    @classmethod
    def from_env(cls) -> "EnterpriseAPIConfig":
        environment = os.getenv("NODE_ENV", os.getenv("HYBA_ENV", "development")).lower()
        return cls(
            environment=environment,
            request_limit_per_minute=int(os.getenv("HYBA_API_RATE_LIMIT_PER_MINUTE", "120")),
            max_body_bytes=int(os.getenv("HYBA_API_MAX_BODY_BYTES", str(2 * 1024 * 1024))),
            hsts_enabled=os.getenv("HYBA_API_HSTS", "true").lower() == "true"
            and environment == "production",
            rate_limit_enabled=os.getenv("HYBA_API_RATE_LIMIT_ENABLED", "true").lower() == "true",
            csp_enabled=os.getenv("HYBA_API_CSP_ENABLED", "true").lower() == "true",
            sanitize_production_errors=os.getenv(
                "HYBA_API_SANITIZE_PRODUCTION_ERRORS", "true"
            ).lower()
            == "true"
            and environment == "production",
        )


def _request_id(request: Request) -> str:
    return (
        request.headers.get("x-request-id")
        or request.headers.get("x-correlation-id")
        or f"req-{time.time_ns()}"
    )


def enterprise_error_payload(
    *, code: str, message: str, request_id: str, status_code: int
) -> Dict[str, Any]:
    """Return the standard HYBA API error envelope."""

    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "status_code": status_code,
            "request_id": request_id,
        },
    }


def _safe_http_message(exc: HTTPException, config: EnterpriseAPIConfig) -> str:
    if not config.sanitize_production_errors:
        detail = exc.detail
        if isinstance(detail, dict):
            raw_message = detail.get("message", detail)
            return str(raw_message) if not isinstance(raw_message, str) else raw_message
        return str(detail)
    if exc.status_code >= 500:
        return "Internal server error. Reference the request_id in operator logs."
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return "Authentication required or invalid."
    if exc.status_code == status.HTTP_403_FORBIDDEN:
        return "Forbidden."
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        return "Not found."
    return "Request rejected. Reference the request_id in operator logs."


def apply_enterprise_security_headers(
    response: Response, request_id: str, config: EnterpriseAPIConfig
) -> None:
    """Attach security and traceability headers to every API response."""

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    if config.csp_enabled:
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
    if config.hsts_enabled:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"


class InMemoryRateLimiter:
    """Small fixed-window limiter for single-process API posture.

    This is intentionally simple and deterministic. Enterprise deployments
    should still enforce distributed limits at the gateway/WAF layer; this class
    is the application-level backstop.
    """

    def __init__(self, limit_per_minute: int):
        if limit_per_minute < 1:
            raise ValueError("limit_per_minute must be positive")
        self.limit_per_minute = limit_per_minute
        self._lock = Lock()
        self._windows: Dict[str, Tuple[int, int]] = {}

    def allow(self, client_key: str, now: float | None = None) -> bool:
        current = int((now if now is not None else time.time()) // 60)
        with self._lock:
            window, count = self._windows.get(client_key, (current, 0))
            if window != current:
                window, count = current, 0
            count += 1
            self._windows[client_key] = (window, count)
            # Opportunistic pruning prevents unbounded memory growth in long-running workers.
            stale = [
                key
                for key, (seen_window, _seen_count) in self._windows.items()
                if seen_window < current - 1
            ]
            for key in stale:
                self._windows.pop(key, None)
            return count <= self.limit_per_minute


def _client_key(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def install_enterprise_api_posture(app: FastAPI, config: EnterpriseAPIConfig | None = None) -> None:
    """Install HYBA's enterprise API posture controls on a FastAPI app."""

    config = config or EnterpriseAPIConfig.from_env()
    limiter = InMemoryRateLimiter(config.request_limit_per_minute)

    @app.middleware("http")
    async def enterprise_api_posture_middleware(request: Request, call_next: Callable[..., Any]):
        request_id = _request_id(request)
        request.state.request_id = request_id

        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > config.max_body_bytes:
            response = JSONResponse(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                content=enterprise_error_payload(
                    code="request_body_too_large",
                    message="Request body exceeds HYBA_API_MAX_BODY_BYTES.",
                    request_id=request_id,
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                ),
            )
            apply_enterprise_security_headers(response, request_id, config)
            return response

        if config.rate_limit_enabled and not limiter.allow(_client_key(request)):
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=enterprise_error_payload(
                    code="rate_limit_exceeded",
                    message="Request rate limit exceeded.",
                    request_id=request_id,
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                ),
            )
            response.headers["Retry-After"] = "60"
            apply_enterprise_security_headers(response, request_id, config)
            return response

        response = await call_next(request)
        apply_enterprise_security_headers(response, request_id, config)
        return response

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        request_id = getattr(request.state, "request_id", _request_id(request))
        detail = exc.detail
        code = "http_error"
        if isinstance(detail, dict):
            code = str(detail.get("error", code))
        response = JSONResponse(
            status_code=exc.status_code,
            content=enterprise_error_payload(
                code=code,
                message=_safe_http_message(exc, config),
                request_id=request_id,
                status_code=exc.status_code,
            ),
        )
        apply_enterprise_security_headers(response, request_id, config)
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", _request_id(request))

        # Convert validation errors to JSON-serializable format and keep them out
        # of production responses unless explicitly disabled for local debugging.
        errors = []
        if not config.sanitize_production_errors:
            for error in exc.errors():
                error_dict = {
                    "type": error.get("type"),
                    "loc": list(error.get("loc", [])),
                    "msg": str(error.get("msg", "")),
                    "input": str(error.get("input", ""))[:100],
                }
                if "ctx" in error:
                    error_dict["ctx"] = {k: str(v) for k, v in error["ctx"].items()}
                errors.append(error_dict)

        payload = enterprise_error_payload(
            code="validation_error",
            message="Request validation failed.",
            request_id=request_id,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
        if errors:
            payload["details"] = errors
        response = JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload)
        apply_enterprise_security_headers(response, request_id, config)
        return response
