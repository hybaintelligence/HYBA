"""
Centralized Error Monitoring and Logging System
Provides comprehensive error tracking, aggregation, and alerting
"""

from __future__ import annotations

import json
import logging
import os
import threading
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional

from core.error_handling import (
    HybaError,
    ErrorCategory,
    ErrorSeverity,
    error_logger,
)


class ErrorMetrics:
    """Track error metrics for monitoring"""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.error_history: deque = deque(maxlen=max_history)
        self.error_by_category: Dict[ErrorCategory, int] = defaultdict(int)
        self.error_by_severity: Dict[ErrorSeverity, int] = defaultdict(int)
        self.last_errors: deque = deque(maxlen=10)
        self.lock = threading.Lock()

    def record_error(self, error: HybaError):
        """Record an error occurrence"""
        with self.lock:
            self.error_counts[error.code] += 1
            self.error_by_category[error.category] += 1
            self.error_by_severity[error.severity] += 1
            self.error_history.append(
                {
                    "error_id": error.error_id,
                    "code": error.code,
                    "category": error.category.value,
                    "severity": error.severity.value,
                    "timestamp": error.timestamp.isoformat(),
                    "message": error.message,
                }
            )
            self.last_errors.append(error)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current error metrics"""
        with self.lock:
            return {
                "total_errors": sum(self.error_counts.values()),
                "unique_errors": len(self.error_counts),
                "error_counts": dict(self.error_counts),
                "errors_by_category": {
                    cat.value: count for cat, count in self.error_by_category.items()
                },
                "errors_by_severity": {
                    sev.value: count for sev, count in self.error_by_severity.items()
                },
                "recent_errors": [
                    {
                        "error_id": error.error_id,
                        "code": error.code,
                        "message": error.message,
                        "timestamp": error.timestamp.isoformat(),
                    }
                    for error in list(self.last_errors)
                ],
            }

    def get_error_rate(self, window_minutes: int = 5) -> float:
        """Calculate error rate over time window"""
        with self.lock:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
            recent_errors = [
                e
                for e in self.error_history
                if datetime.fromisoformat(e["timestamp"]) >= cutoff
            ]
            return len(recent_errors) / window_minutes if window_minutes > 0 else 0


class ErrorAlerting:
    """Error alerting and notification system"""

    def __init__(self):
        self.alert_rules: List[Callable[[ErrorMetrics], Optional[str]]] = []
        self.alert_handlers: List[Callable[[str, Dict[str, Any]], None]] = []
        self.logger = logging.getLogger(__name__)

    def add_alert_rule(self, rule: Callable[[ErrorMetrics], Optional[str]]):
        """Add an alert rule"""
        self.alert_rules.append(rule)

    def add_alert_handler(self, handler: Callable[[str, Dict[str, Any]], None]):
        """Add an alert handler"""
        self.alert_handlers.append(handler)

    def check_alerts(self, metrics: ErrorMetrics) -> List[str]:
        """Check all alert rules and return triggered alerts"""
        alerts = []
        for rule in self.alert_rules:
            try:
                alert = rule(metrics)
                if alert:
                    alerts.append(alert)
                    self._send_alert(alert, metrics.get_metrics())
            except Exception as e:
                self.logger.error(f"Error checking alert rule: {e}")
        return alerts

    def _send_alert(self, alert: str, metrics: Dict[str, Any]):
        """Send alert to all handlers"""
        for handler in self.alert_handlers:
            try:
                handler(alert, metrics)
            except Exception as e:
                self.logger.error(f"Error in alert handler: {e}")


class ErrorMonitoringService:
    """Centralized error monitoring service"""

    def __init__(self):
        self.metrics = ErrorMetrics()
        self.alerting = ErrorAlerting()
        self.logger = logging.getLogger(__name__)
        self._setup_default_alerts()

    def _setup_default_alerts(self):
        """Setup default alerting rules"""

        # High error rate alert
        def high_error_rate(metrics: ErrorMetrics) -> Optional[str]:
            rate = metrics.get_error_rate(window_minutes=1)
            if rate > 10:  # More than 10 errors per minute
                return f"HIGH_ERROR_RATE: {rate:.1f} errors/minute"
            return None

        # Critical error alert
        def critical_error(metrics: ErrorMetrics) -> Optional[str]:
            critical_count = metrics.error_by_severity.get(ErrorSeverity.CRITICAL, 0)
            if critical_count > 0:
                return f"CRITICAL_ERROR: {critical_count} critical errors detected"
            return None

        # High severity error alert
        def high_severity_error(metrics: ErrorMetrics) -> Optional[str]:
            high_count = metrics.error_by_severity.get(ErrorSeverity.HIGH, 0)
            if high_count > 5:
                return f"HIGH_SEVERITY_ERROR: {high_count} high severity errors"
            return None

        self.alerting.add_alert_rule(high_error_rate)
        self.alerting.add_alert_rule(critical_error)
        self.alerting.add_alert_rule(high_severity_error)

        # Default console alert handler
        def console_alert_handler(alert: str, metrics: Dict[str, Any]):
            self.logger.warning(f"ALERT: {alert}")
            self.logger.warning(f"Current metrics: {json.dumps(metrics, indent=2)}")

        self.alerting.add_alert_handler(console_alert_handler)

    def record_error(self, error: HybaError):
        """Record an error and check for alerts"""
        self.metrics.record_error(error)
        alerts = self.alerting.check_alerts(self.metrics)
        if alerts:
            self.logger.warning(f"Triggered alerts: {alerts}")

    def get_monitoring_data(self) -> Dict[str, Any]:
        """Get comprehensive monitoring data"""
        return {
            "metrics": self.metrics.get_metrics(),
            "error_rate_1min": self.metrics.get_error_rate(1),
            "error_rate_5min": self.metrics.get_error_rate(5),
            "error_rate_15min": self.metrics.get_error_rate(15),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def export_metrics(self, filepath: Optional[str] = None) -> str:
        """Export metrics to file or return as JSON string"""
        data = self.get_monitoring_data()
        json_str = json.dumps(data, indent=2)

        if filepath:
            try:
                with open(filepath, "w") as f:
                    f.write(json_str)
                self.logger.info(f"Metrics exported to {filepath}")
            except Exception as e:
                self.logger.error(f"Failed to export metrics: {e}")

        return json_str


class ErrorAggregator:
    """Aggregate errors from multiple sources"""

    def __init__(self):
        self.sources: Dict[str, ErrorMonitoringService] = {}
        self.logger = logging.getLogger(__name__)

    def register_source(self, name: str, service: ErrorMonitoringService):
        """Register an error monitoring source"""
        self.sources[name] = service
        self.logger.info(f"Registered error monitoring source: {name}")

    def get_aggregated_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics from all sources"""
        aggregated = {
            "sources": {},
            "total_errors": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        for name, service in self.sources.items():
            source_metrics = service.get_monitoring_data()
            aggregated["sources"][name] = source_metrics
            aggregated["total_errors"] += source_metrics["metrics"]["total_errors"]

        return aggregated

    def record_error(self, source: str, error: HybaError):
        """Record error from specific source"""
        if source in self.sources:
            self.sources[source].record_error(error)
        else:
            self.logger.warning(f"Unknown error source: {source}")


# Global error monitoring service instance
error_monitoring_service = ErrorMonitoringService()

# Global error aggregator instance
error_aggregator = ErrorAggregator()

# Register the main monitoring service with the aggregator
error_aggregator.register_source("main", error_monitoring_service)


def setup_error_logging_integration():
    """Integrate error monitoring with existing error logger"""
    original_log_error = error_logger.log_error

    def enhanced_log_error(
        error,
        context=None,
        user_id=None,
        request_id=None,
    ):
        # Call original logging
        original_log_error(error, context, user_id, request_id)

        # Record in monitoring system if it's a HybaError
        if isinstance(error, HybaError):
            error_monitoring_service.record_error(error)

    error_logger.log_error = enhanced_log_error


# Auto-setup integration on import
setup_error_logging_integration()
