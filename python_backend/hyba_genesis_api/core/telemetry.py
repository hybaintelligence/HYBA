"""Structured logging, request telemetry, audit events, and production metrics.

The module is deliberately dependency-light for local/Docker execution while still
emitting Prometheus-compatible metrics and OpenTelemetry-ready request context in
production. It is used as the application evidence layer for the enterprise
production-readiness close-down programme.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import re
import sys
import time
import uuid
from typing import Any, Dict

from fastapi import Request
from pythonjsonlogger import jsonlogger

from prometheus_client import Counter, Gauge, Histogram, generate_latest

_LOW_CARDINALITY_RE = re.compile(r"[^a-zA-Z0-9_.:-]+")


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

AUDIT_EVENT_COUNT = Counter(
    "hyba_audit_events_total",
    "Security and governance audit events emitted by HYBA",
    ["event_type", "outcome"],
)

GOVERNANCE_GATE_STATUS = Gauge(
    "hyba_governance_gate_status",
    "Governance gate status, where 1 means passing/closed and 0 means failing/open",
    ["gate"],
)

ENTERPRISE_READINESS_GAP_STATUS = Gauge(
    "hyba_enterprise_readiness_gap_status",
    "Enterprise readiness gap status encoded as a labelled gauge",
    ["gap", "status"],
)

WORKFLOW_STATUS = Gauge(
    "hyba_workflow_status",
    "Operational workflow status, where 1 means healthy/active and 0 means degraded/inactive",
    ["workflow", "status"],
)

RELIABILITY_CIRCUIT_STATE = Gauge(
    "hyba_reliability_circuit_state",
    "Circuit-breaker state encoded as 0=closed, 1=half_open, 2=open",
    ["circuit"],
)

ACTIVE_REQUESTS = Gauge(
    "active_requests",
    "Currently active HYBA HTTP requests",
)

REQUEST_TOTAL = Counter(
    "request_total",
    "Total HYBA HTTP requests by route and status",
    ["route", "status"],
)

REQUEST_DURATION_SECONDS = Histogram(
    "request_duration_seconds",
    "HYBA HTTP request duration by route in seconds",
    ["route"],
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

_METRICS: Dict[str, Any] = {
    "requests_total": 0,
    "errors_total": 0,
    "last_request": None,
    "startup_time": None,
    "opentelemetry_enabled": False,
    "active_requests": 0,
    "readiness_gaps": {},
    "governance_gates": {},
    "workflows": {},
    "audit_events_total": 0,
}


def _safe_label(value: str, *, default: str = "unknown") -> str:
    """Return a bounded low-cardinality metric label."""

    cleaned = _LOW_CARDINALITY_RE.sub("_", str(value or default).strip())[:80]
    return cleaned or default


def init_logging() -> None:
    """Configure root logging as structured JSON without duplicate handlers."""

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    log_handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(module)s %(message)s "
        "%(request_id)s %(correlation_id)s %(trace_id)s %(span_id)s %(traceparent)s "
        "%(method)s %(path)s %(status_code)s %(duration_ms)s"
    )
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)

    logging.info("Telemetry: Structured JSON logging initialized.")


def init_metrics() -> None:
    """Initialize in-process metrics and optional OpenTelemetry export."""

    _METRICS["startup_time"] = time.time()
    _METRICS["opentelemetry_enabled"] = init_opentelemetry()
    record_governance_gate_status("telemetry_initialized", True)
    logging.info("Telemetry: Performance metrics collector active.")


def init_opentelemetry() -> bool:
    """Enable OpenTelemetry SDK export when installed and configured.

    The runtime remains dependency-light for local tests. Production images can
    install opentelemetry-sdk and opentelemetry-exporter-otlp, then set
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


def record_governance_gate_status(gate: str, passing: bool) -> None:
    """Publish a governance-gate pass/fail metric."""

    safe_gate = _safe_label(gate)
    value = 1 if passing else 0
    GOVERNANCE_GATE_STATUS.labels(safe_gate).set(value)
    _METRICS["governance_gates"][safe_gate] = "passing" if passing else "failing"


def set_enterprise_readiness_gap_status(gap: str, status: str) -> None:
    """Publish the latest status for a production-readiness gap.

    Status is intentionally a label and the gauge is set to 1 for the current
    value. Callers should keep status values low-cardinality, e.g.
    closed_by_code, closed_by_operational_control, documented_but_external_dependency,
    or not_closed.
    """

    safe_gap = _safe_label(gap)
    safe_status = _safe_label(status)
    ENTERPRISE_READINESS_GAP_STATUS.labels(safe_gap, safe_status).set(1)
    _METRICS["readiness_gaps"][safe_gap] = safe_status


def set_workflow_status(workflow: str, status: str, healthy: bool) -> None:
    """Publish operational workflow health."""

    safe_workflow = _safe_label(workflow)
    safe_status = _safe_label(status)
    WORKFLOW_STATUS.labels(safe_workflow, safe_status).set(1 if healthy else 0)
    _METRICS["workflows"][safe_workflow] = {"status": safe_status, "healthy": bool(healthy)}


def record_audit_event(event_type: str, outcome: str, **fields: Any) -> None:
    """Emit a structured audit event and increment its Prometheus counter."""

    safe_event = _safe_label(event_type)
    safe_outcome = _safe_label(outcome)
    AUDIT_EVENT_COUNT.labels(safe_event, safe_outcome).inc()
    _METRICS["audit_events_total"] += 1
    logging.info(
        "Audit event",
        extra={
            "event_type": safe_event,
            "outcome": safe_outcome,
            **{k: str(v)[:256] for k, v in fields.items()},
        },
    )


def set_reliability_circuit_state(circuit: str, state: str) -> None:
    """Publish a circuit-breaker state metric."""

    encoded = {"closed": 0, "half_open": 1, "open": 2}.get(state, 2)
    RELIABILITY_CIRCUIT_STATE.labels(_safe_label(circuit)).set(encoded)


def _correlation_id(request: Request, request_id: str) -> str:
    return (
        request.headers.get("x-correlation-id")
        or request.headers.get("x-request-id")
        or request_id
    )


async def telemetry_middleware(request: Request, call_next):
    """Log request/response telemetry, propagate trace context, and count errors."""

    request_id = request.headers.get("x-request-id") or f"req-{uuid.uuid4().hex}"
    correlation_id = _correlation_id(request, request_id)
    incoming_traceparent = request.headers.get("traceparent", "")
    trace_id = uuid.uuid4().hex
    span_id = uuid.uuid4().hex[:16]
    if incoming_traceparent:
        parts = incoming_traceparent.split("-")
        if len(parts) >= 4:
            trace_id = parts[1]
            span_id = parts[2]
    traceparent = incoming_traceparent or f"00-{trace_id}-{span_id}-01"
    request.state.request_id = request_id
    request.state.correlation_id = correlation_id
    request.state.traceparent = traceparent
    request.state.trace_id = trace_id
    request.state.span_id = span_id

    ACTIVE_REQUESTS.inc()
    _METRICS["active_requests"] += 1
    start = time.perf_counter()
    status_code = 500
    exception_seen = False
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["x-request-id"] = request_id
        response.headers["x-correlation-id"] = correlation_id
        response.headers["x-trace-id"] = trace_id
        response.headers["traceparent"] = traceparent
        return response
    except Exception:
        exception_seen = True
        logging.exception(
            "Telemetry: Request failed",
            extra={
                "request_id": request_id,
                "correlation_id": correlation_id,
                "traceparent": traceparent,
                "trace_id": trace_id,
                "span_id": span_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": round((time.perf_counter() - start) * 1000, 3),
            },
        )
        raise
    finally:
        duration_ms = round((time.perf_counter() - start) * 1000, 3)
        ACTIVE_REQUESTS.dec()
        _METRICS["active_requests"] = max(0, int(_METRICS.get("active_requests", 0)) - 1)
        if status_code >= 500 or exception_seen:
            _METRICS["errors_total"] += 1
        _METRICS["requests_total"] += 1
        _METRICS["last_request"] = {
            "request_id": request_id,
            "correlation_id": correlation_id,
            "traceparent": traceparent,
            "trace_id": trace_id,
            "span_id": span_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "duration_ms": duration_ms,
        }
        logging.info("Telemetry: Request completed", extra=_METRICS["last_request"])
        endpoint = request.url.path
        REQUEST_COUNT.labels(request.method, endpoint, str(status_code)).inc()
        REQUEST_LATENCY.labels(endpoint).observe(duration_ms / 1000.0)
        REQUEST_TOTAL.labels(endpoint, str(status_code)).inc()
        REQUEST_DURATION_SECONDS.labels(endpoint).observe(duration_ms / 1000.0)
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
