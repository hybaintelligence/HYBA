"""Structured logging, request telemetry, and performance metrics (Prometheus and in-process)."""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
import time
from typing import Any, Dict

from fastapi import Request
from pythonjsonlogger import jsonlogger

# Prometheus metrics
from prometheus_client import Counter, Gauge, Histogram, generate_latest

# Define Prometheus counters and histograms with labels.
REQUEST_COUNT = Counter(
    "hyba_requests_total",
    "Total HTTP requests handled by HYBA",
    ["method", "endpoint", "http_status"],
)

REQUEST_LATENCY = Histogram(
    "hyba_request_duration_seconds",
    "Latency of HTTP requests in seconds",
    ["endpoint"],
    buckets=(0.005, 0.05, 0.2, 1, 5, 10),
)

ERROR_COUNT = Counter(
    "hyba_errors_total",
    "Total HTTP requests resulting in 5xx errors",
    ["endpoint"],
)

BILLING_USAGE_UNITS = Counter(
    "hyba_billing_usage_units_total",
    "Billable usage units accepted by HYBA commercial APIs",
    ["tenant_hash", "product", "tier"],
)

BILLING_ESTIMATED_CHARGES = Counter(
    "hyba_billing_estimated_charges_usd_total",
    "Estimated usage charges accepted by HYBA commercial APIs in USD",
    ["tenant_hash", "product", "tier"],
)

BILLING_QUOTA_REJECTIONS = Counter(
    "hyba_billing_quota_rejections_total",
    "Commercial API requests rejected by monthly quota enforcement",
    ["tenant_hash", "quota", "tier"],
)

BILLING_QUOTA_REMAINING = Gauge(
    "hyba_billing_quota_remaining",
    "Remaining monthly quota after accepted commercial API metering",
    ["tenant_hash", "quota", "tier"],
)

# In-process metrics for simple debugging
_METRICS: Dict[str, Any] = {
    "requests_total": 0,
    "errors_total": 0,
    "last_request": None,
    "startup_time": None,
}


def init_logging() -> None:
    """Configure root logging as structured JSON without duplicate handlers."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # Clear existing handlers to avoid duplicate logs when running under uvicorn reload
    logger.handlers.clear()

    log_handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(method)s %(path)s %(status_code)s %(duration_ms)s"
    )
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)

    logging.info("Telemetry: Structured JSON logging initialized.")


def init_metrics() -> None:
    """Initialize the in-process performance metrics collector and optional OpenTelemetry."""
    _METRICS["startup_time"] = time.time()
    _METRICS["opentelemetry_enabled"] = init_opentelemetry()
    logging.info("Telemetry: Performance metrics collector active.")


def init_opentelemetry() -> bool:
    """Enable OpenTelemetry SDK export when installed and configured.

    The runtime remains dependency-light for local tests. Production images can install
    opentelemetry-sdk and opentelemetry-exporter-otlp, then set
    OTEL_EXPORTER_OTLP_ENDPOINT to emit traces to a collector.
    """
    if not os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        return False
    required = (
        "opentelemetry",
        "opentelemetry.sdk",
        "opentelemetry.exporter.otlp.proto.http.trace_exporter",
    )
    if any(importlib.util.find_spec(module) is None for module in required):
        logging.warning("Telemetry: OpenTelemetry endpoint configured but SDK/exporter packages are unavailable.")
        return False

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({"service.name": os.getenv("OTEL_SERVICE_NAME", "hyba-genesis-api")})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    logging.info("Telemetry: OpenTelemetry OTLP tracing initialized.")
    return True


def get_metrics() -> Dict[str, Any]:
    """Return current in-process metrics."""
    return dict(_METRICS)


def get_prometheus_metrics() -> bytes:
    """Return Prometheus metrics data suitable for /metrics endpoint."""
    return generate_latest()


async def telemetry_middleware(request: Request, call_next):
    """Log request/response telemetry, record metrics, and count errors."""
    request_id = request.headers.get("x-request-id", f"req-{time.time_ns()}")
    start = time.perf_counter()
    status_code = 500
    exception_seen = False
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["x-request-id"] = request_id
        return response
    except Exception:
        exception_seen = True
        # Log exception with structured context
        logging.exception(
            "Telemetry: Request failed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": round((time.perf_counter() - start) * 1000, 3),
            },
        )
        raise
    finally:
        duration_ms = round((time.perf_counter() - start) * 1000, 3)
        # Update in-process metrics
        if status_code >= 500 or exception_seen:
            _METRICS["errors_total"] += 1
        _METRICS["requests_total"] += 1
        _METRICS["last_request"] = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "duration_ms": duration_ms,
        }
        logging.info("Telemetry: Request completed", extra=_METRICS["last_request"])
        # Update Prometheus metrics
        endpoint = request.url.path
        # Use string for status_code label to avoid type issues
        REQUEST_COUNT.labels(request.method, endpoint, str(status_code)).inc()
        REQUEST_LATENCY.labels(endpoint).observe(duration_ms / 1000.0)
        if status_code >= 500 or exception_seen:
            ERROR_COUNT.labels(endpoint).inc()


def record_billing_usage(tenant_hash: str, product: str, tier: str, units: int, estimated_charge_usd: float) -> None:
    """Record accepted low-cardinality commercial billing metrics."""
    safe_units = max(0, int(units))
    BILLING_USAGE_UNITS.labels(tenant_hash, product, tier).inc(safe_units)
    if estimated_charge_usd > 0:
        BILLING_ESTIMATED_CHARGES.labels(tenant_hash, product, tier).inc(estimated_charge_usd)


def record_billing_quota_rejection(tenant_hash: str, quota: str, tier: str) -> None:
    """Record a fail-closed quota rejection without exposing raw tenant identifiers."""
    BILLING_QUOTA_REJECTIONS.labels(tenant_hash, quota, tier).inc()


def set_billing_quota_remaining(tenant_hash: str, tier: str, requests_remaining: int, compute_remaining: int) -> None:
    """Publish current remaining monthly request and compute-unit quota gauges."""
    BILLING_QUOTA_REMAINING.labels(tenant_hash, "requests", tier).set(max(0, requests_remaining))
    BILLING_QUOTA_REMAINING.labels(tenant_hash, "compute_units", tier).set(max(0, compute_remaining))
