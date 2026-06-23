"""
Comprehensive Error Handling for HYBA Backend
Provides centralized error handling, classification, and recovery mechanisms
"""

from __future__ import annotations

import enum
import logging
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Type, Union

from fastapi import HTTPException, status
from pydantic import BaseModel

LOGGER = logging.getLogger(__name__)


# ── Error Categories ──────────────────────────────────────────────────────────

class ErrorCategory(enum.Enum):
    NETWORK = "network"
    API = "api"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATABASE = "database"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    INTERNAL = "internal"
    EXTERNAL_SERVICE = "external_service"
    UNKNOWN = "unknown"


class ErrorSeverity(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ── Base Error Classes ────────────────────────────────────────────────────────

class HybaError(Exception):
    """Base error class for all HYBA application errors"""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        code: Optional[str] = None,
        status_code: int = 500,
        context: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
        retryable: bool = False,
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.code = code or self.__class__.__name__
        self.status_code = status_code
        self.context = context or {}
        self.recoverable = recoverable
        self.retryable = retryable
        self.error_id = str(uuid.uuid4())
        self.timestamp = datetime.now(timezone.utc)
        self.stack_trace = traceback.format_exc()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses.

        Includes error_id for operator log correlation and omits stack_trace
        from the response body to prevent internal detail leakage.
        """
        return {
            "error_id": self.error_id,
            "code": self.code,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "status_code": self.status_code,
            "context": self.context,
            "recoverable": self.recoverable,
            "retryable": self.retryable,
            "timestamp": self.timestamp.isoformat(),
        }

    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException with correlation headers."""
        return HTTPException(
            status_code=self.status_code,
            detail=self.to_dict(),
            headers={"x-error-id": self.error_id},
        )


class NetworkError(HybaError):
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            status_code=503,
            retryable=True,
            **kwargs
        )


class ApiError(HybaError):
    def __init__(self, message: str, status_code: int = 500, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.API,
            severity=ErrorSeverity.MEDIUM,
            status_code=status_code,
            **kwargs
        )


class ValidationError(HybaError):
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            status_code=400,
            recoverable=False,
            retryable=False,
            **kwargs
        )


class AuthenticationError(HybaError):
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            status_code=401,
            recoverable=False,
            retryable=False,
            **kwargs
        )


class AuthorizationError(HybaError):
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.HIGH,
            status_code=403,
            recoverable=False,
            retryable=False,
            **kwargs
        )


class DatabaseError(HybaError):
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            status_code=500,
            **kwargs
        )


class TimeoutError(HybaError):
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            status_code=504,
            retryable=True,
            **kwargs
        )


class RateLimitError(HybaError):
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            status_code=429,
            retryable=True,
            **kwargs
        )


class ExternalServiceError(HybaError):
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.HIGH,
            status_code=502,
            **kwargs
        )


# ── Error Classification ────────────────────────────────────────────────────

def classify_error(error: Exception) -> HybaError:
    """Classify a generic exception into appropriate HybaError type"""
    if isinstance(error, HybaError):
        return error
    
    message = str(error)
    
    # Check error message patterns for classification
    message_lower = message.lower()
    
    if "network" in message_lower or "connection" in message_lower or "fetch" in message_lower:
        return NetworkError(message, context={"original_error": type(error).__name__})
    
    if "timeout" in message_lower or "timed out" in message_lower:
        return TimeoutError(message, context={"original_error": type(error).__name__})
    
    if "validation" in message_lower or "invalid" in message_lower or "required" in message_lower:
        return ValidationError(message, context={"original_error": type(error).__name__})
    
    if "auth" in message_lower or "unauthorized" in message_lower or "forbidden" in message_lower:
        return AuthenticationError(message, context={"original_error": type(error).__name__})
    
    if "permission" in message_lower or "access denied" in message_lower:
        return AuthorizationError(message, context={"original_error": type(error).__name__})
    
    if "rate limit" in message_lower or "too many requests" in message_lower:
        return RateLimitError(message, context={"original_error": type(error).__name__})
    
    if "database" in message_lower or "db" in message_lower or "sql" in message_lower:
        return DatabaseError(message, context={"original_error": type(error).__name__})
    
    # Default classification
    return HybaError(
        message,
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.MEDIUM,
        context={"original_error": type(error).__name__}
    )


# ── Error Logging ───────────────────────────────────────────────────────────

class ErrorLogger:
    """Centralized error logging with structured output"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def log_error(
        self,
        error: Union[HybaError, Exception],
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        """Log error with structured context"""
        if not isinstance(error, HybaError):
            error = classify_error(error)
        
        log_context = {
            "error_id": error.error_id,
            "code": error.code,
            "category": error.category.value,
            "severity": error.severity.value,
            "user_id": user_id,
            "request_id": request_id,
            **error.context,
            **(context or {})
        }
        
        # Choose appropriate log level based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(error.message, extra=log_context, exc_info=True)
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(error.message, extra=log_context, exc_info=True)
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(error.message, extra=log_context)
        else:
            self.logger.info(error.message, extra=log_context)


# Global error logger instance
error_logger = ErrorLogger()


# ── Error Handlers ───────────────────────────────────────────────────────────

def handle_error(
    error: Union[HybaError, Exception],
    context: Optional[Dict[str, Any]] = None,
    raise_http: bool = True,
) -> HTTPException:
    """Classify, log, and convert an error to an HTTPException.

    Always returns an HTTPException so callers can do `raise handle_error(...)`
    regardless of `raise_http`. When `raise_http=False` the caller receives the
    exception object without it being raised, which is useful for side-effect
    logging in fire-and-forget paths.
    """
    if not isinstance(error, HybaError):
        error = classify_error(error)

    error_logger.log_error(error, context)
    return error.to_http_exception()


# ── Decorators ──────────────────────────────────────────────────────────────

def with_error_handling(
    default_return: Any = None,
    error_category: ErrorCategory = ErrorCategory.INTERNAL,
    error_message: str = "An error occurred",
):
    """Decorator for adding error handling to functions"""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HybaError:
                raise  # Re-raise already classified errors
            except Exception as e:
                error = HybaError(
                    error_message,
                    category=error_category,
                    context={"function": func.__name__, "original_error": str(e)}
                )
                error_logger.log_error(error)
                if default_return is not None:
                    return default_return
                raise
        return wrapper
    return decorator


def async_with_error_handling(
    default_return: Any = None,
    error_category: ErrorCategory = ErrorCategory.INTERNAL,
    error_message: str = "An error occurred",
):
    """Decorator for adding error handling to async functions"""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HybaError:
                raise  # Re-raise already classified errors
            except Exception as e:
                error = HybaError(
                    error_message,
                    category=error_category,
                    context={"function": func.__name__, "original_error": str(e)}
                )
                error_logger.log_error(error)
                if default_return is not None:
                    return default_return
                raise
        return wrapper
    return decorator


# ── Response Models ──────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Standard error response model"""
    error_id: str
    code: str
    message: str
    category: str
    severity: str
    status_code: int
    context: Dict[str, Any] = {}
    recoverable: bool
    retryable: bool
    timestamp: str
    
    @classmethod
    def from_error(cls, error: HybaError) -> "ErrorResponse":
        return cls(**error.to_dict())
