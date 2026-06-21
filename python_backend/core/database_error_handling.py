"""
Database Error Handling Module
Provides comprehensive error handling for database operations
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional, TypeVar, Union

from sqlalchemy.exc import (
    DatabaseError,
    IntegrityError,
    InterfaceError,
    OperationalError,
    ProgrammingError,
    SQLAlchemyError,
)

from core.error_handling import (
    DatabaseError as HybaDatabaseError,
    ValidationError,
    handle_error,
    HybaError,
)

LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


class DatabaseErrorHandler:
    """Centralized database error handling"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def handle_sqlalchemy_error(
        self,
        error: SQLAlchemyError,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> HybaDatabaseError:
        """Convert SQLAlchemy errors to HybaDatabaseError"""
        error_context = {
            "operation": operation,
            "original_error_type": type(error).__name__,
            **(context or {})
        }
        
        if isinstance(error, IntegrityError):
            return HybaDatabaseError(
                f"Database integrity constraint violation: {str(error)}",
                context=error_context,
                recoverable=False,
                retryable=False,
            )
        elif isinstance(error, OperationalError):
            return HybaDatabaseError(
                f"Database operational error: {str(error)}",
                context=error_context,
                recoverable=True,
                retryable=True,
            )
        elif isinstance(error, ProgrammingError):
            return HybaDatabaseError(
                f"Database programming error: {str(error)}",
                context=error_context,
                recoverable=False,
                retryable=False,
            )
        elif isinstance(error, InterfaceError):
            return HybaDatabaseError(
                f"Database interface error: {str(error)}",
                context=error_context,
                recoverable=True,
                retryable=True,
            )
        else:
            return HybaDatabaseError(
                f"Database error: {str(error)}",
                context=error_context,
                recoverable=True,
                retryable=True,
            )


# Global database error handler instance
db_error_handler = DatabaseErrorHandler()


@contextmanager
def handle_database_errors(
    operation: str,
    context: Optional[Dict[str, Any]] = None,
    raise_on_error: bool = True,
):
    """Context manager for handling database errors"""
    try:
        yield
    except SQLAlchemyError as e:
        error = db_error_handler.handle_sqlalchemy_error(e, operation, context)
        handle_error(error, raise_http=False)
        
        if raise_on_error:
            raise error
    except Exception as e:
        error = HybaDatabaseError(
            f"Unexpected database error: {str(e)}",
            context={"operation": operation, **(context or {})},
        )
        handle_error(error, raise_http=False)
        
        if raise_on_error:
            raise error


def with_database_error_handling(
    operation: str,
    default_return: Optional[T] = None,
    context: Optional[Dict[str, Any]] = None,
):
    """Decorator for adding database error handling to functions"""
    
    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, None]]:
        def wrapper(*args, **kwargs) -> Union[T, None]:
            try:
                return func(*args, **kwargs)
            except SQLAlchemyError as e:
                error = db_error_handler.handle_sqlalchemy_error(
                    e, operation, {**context, "function": func.__name__}
                )
                handle_error(error, raise_http=False)
                
                if default_return is not None:
                    return default_return
                raise error
            except Exception as e:
                error = HybaDatabaseError(
                    f"Unexpected database error in {func.__name__}: {str(e)}",
                    context={"operation": operation, **(context or {})},
                )
                handle_error(error, raise_http=False)
                
                if default_return is not None:
                    return default_return
                raise error
        return wrapper
    return decorator


def async_with_database_error_handling(
    operation: str,
    default_return: Optional[T] = None,
    context: Optional[Dict[str, Any]] = None,
):
    """Decorator for adding database error handling to async functions"""
    
    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, None]]:
        async def wrapper(*args, **kwargs) -> Union[T, None]:
            try:
                return await func(*args, **kwargs)
            except SQLAlchemyError as e:
                error = db_error_handler.handle_sqlalchemy_error(
                    e, operation, {**context, "function": func.__name__}
                )
                handle_error(error, raise_http=False)
                
                if default_return is not None:
                    return default_return
                raise error
            except Exception as e:
                error = HybaDatabaseError(
                    f"Unexpected database error in {func.__name__}: {str(e)}",
                    context={"operation": operation, **(context or {})},
                )
                handle_error(error, raise_http=False)
                
                if default_return is not None:
                    return default_return
                raise error
        return wrapper
    return decorator


class SafeDatabaseOperations:
    """Safe database operations with comprehensive error handling"""
    
    @staticmethod
    def execute_query(
        db_session,
        query: Any,
        operation: str = "execute_query",
        context: Optional[Dict[str, Any]] = None,
    ):
        """Safely execute a database query"""
        with handle_database_errors(operation, context):
            return db_session.execute(query)
    
    @staticmethod
    def commit_session(
        db_session,
        operation: str = "commit",
        context: Optional[Dict[str, Any]] = None,
    ):
        """Safely commit a database session"""
        with handle_database_errors(operation, context):
            db_session.commit()
    
    @staticmethod
    def rollback_session(
        db_session,
        operation: str = "rollback",
        context: Optional[Dict[str, Any]] = None,
    ):
        """Safely rollback a database session"""
        try:
            db_session.rollback()
        except Exception as e:
            handle_error(
                HybaDatabaseError(f"Failed to rollback session: {str(e)}"),
                context={"operation": operation, **(context or {})},
                raise_http=False
            )
    
    @staticmethod
    def close_session(
        db_session,
        operation: str = "close_session",
        context: Optional[Dict[str, Any]] = None,
    ):
        """Safely close a database session"""
        try:
            db_session.close()
        except Exception as e:
            handle_error(
                HybaDatabaseError(f"Failed to close session: {str(e)}"),
                context={"operation": operation, **(context or {})},
                raise_http=False
            )
