"""
HYBA SDK Exceptions
Custom exceptions for the HYBA SDK
"""

from typing import Optional, Dict, Any


class HybaApiError(Exception):
    """Base exception for HYBA API errors"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {super().__str__()}"
        return super().__str__()


class AuthenticationError(HybaApiError):
    """Raised when API key is invalid or expired"""

    def __init__(self, message: str = "Invalid API key", **kwargs):
        super().__init__(message, status_code=401, **kwargs)


class QuotaExceededError(HybaApiError):
    """Raised when API quota is exceeded"""

    def __init__(
        self,
        message: str = "Quota exceeded",
        quota_info: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        super().__init__(message, status_code=429, **kwargs)
        self.quota_info = quota_info or {}

    def __str__(self) -> str:
        base = super().__str__()
        if self.quota_info:
            reset = self.quota_info.get("reset_at", "unknown")
            base += f" (resets at {reset})"
        return base


class ServiceNotFoundError(HybaApiError):
    """Raised when service is not found"""

    def __init__(self, service_id: str, **kwargs):
        message = f"Service not found: {service_id}"
        super().__init__(message, status_code=404, **kwargs)
        self.service_id = service_id


class ValidationError(HybaApiError):
    """Raised when request validation fails"""

    def __init__(
        self, message: str, validation_errors: Optional[Dict[str, Any]] = None, **kwargs
    ):
        super().__init__(message, status_code=422, **kwargs)
        self.validation_errors = validation_errors or {}

    def __str__(self) -> str:
        base = super().__str__()
        if self.validation_errors:
            errors = "; ".join(f"{k}: {v}" for k, v in self.validation_errors.items())
            base += f" ({errors})"
        return base


class RateLimitError(HybaApiError):
    """Raised when rate limit is exceeded"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(message, status_code=429, **kwargs)
        self.retry_after = retry_after

    def __str__(self) -> str:
        base = super().__str__()
        if self.retry_after:
            base += f" (retry after {self.retry_after}s)"
        return base


class ServiceStateError(HybaApiError):
    """Raised when service is in invalid state for operation"""

    def __init__(self, service_id: str, current_state: str, operation: str, **kwargs):
        message = (
            f"Cannot {operation} service {service_id}: "
            f"currently in state '{current_state}'"
        )
        super().__init__(message, status_code=409, **kwargs)
        self.service_id = service_id
        self.current_state = current_state
        self.operation = operation


class WebhookError(HybaApiError):
    """Raised when webhook delivery fails"""

    def __init__(self, message: str, webhook_id: Optional[str] = None, **kwargs):
        super().__init__(message, status_code=500, **kwargs)
        self.webhook_id = webhook_id


class TimeoutError(HybaApiError):
    """Raised when operation times out"""

    def __init__(
        self,
        message: str = "Operation timed out",
        timeout_seconds: Optional[float] = None,
        **kwargs,
    ):
        super().__init__(message, status_code=504, **kwargs)
        self.timeout_seconds = timeout_seconds
