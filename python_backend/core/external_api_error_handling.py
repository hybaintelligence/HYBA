"""
External API Error Handling Module
Provides comprehensive error handling for external API calls and connectors
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Dict, Optional, TypeVar, Union

import aiohttp
import requests
from requests.exceptions import (
    ConnectionError as RequestsConnectionError,
    Timeout as RequestsTimeout,
    RequestException,
)

from core.error_handling import (
    NetworkError,
    TimeoutError as HybaTimeoutError,
    ExternalServiceError,
    RateLimitError,
    handle_error,
    HybaError,
    ErrorCategory,
    ErrorSeverity,
)

LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


class ExternalAPIErrorHandler:
    """Centralized external API error handling"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def handle_requests_error(
        self,
        error: RequestException,
        service_name: str,
        url: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> HybaError:
        """Convert requests exceptions to HybaError"""
        error_context = {
            "service": service_name,
            "url": url,
            "original_error_type": type(error).__name__,
            **(context or {})
        }
        
        if isinstance(error, RequestsTimeout):
            return HybaTimeoutError(
                f"Request to {service_name} timed out: {str(error)}",
                context=error_context,
            )
        elif isinstance(error, RequestsConnectionError):
            return NetworkError(
                f"Failed to connect to {service_name}: {str(error)}",
                context=error_context,
            )
        else:
            return ExternalServiceError(
                f"External API error from {service_name}: {str(error)}",
                context=error_context,
            )
    
    def handle_aiohttp_error(
        self,
        error: Exception,
        service_name: str,
        url: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> HybaError:
        """Convert aiohttp exceptions to HybaError"""
        error_context = {
            "service": service_name,
            "url": url,
            "original_error_type": type(error).__name__,
            **(context or {})
        }
        
        error_str = str(error).lower()
        
        if "timeout" in error_str or "timed out" in error_str:
            return HybaTimeoutError(
                f"Request to {service_name} timed out: {str(error)}",
                context=error_context,
            )
        elif "connection" in error_str or "connect" in error_str:
            return NetworkError(
                f"Failed to connect to {service_name}: {str(error)}",
                context=error_context,
            )
        elif "429" in error_str or "rate limit" in error_str:
            return RateLimitError(
                f"Rate limit exceeded for {service_name}: {str(error)}",
                context=error_context,
            )
        else:
            return ExternalServiceError(
                f"External API error from {service_name}: {str(error)}",
                context=error_context,
            )


# Global external API error handler instance
external_api_error_handler = ExternalAPIErrorHandler()


class SafeExternalAPICalls:
    """Safe external API calls with comprehensive error handling"""
    
    @staticmethod
    def get(
        url: str,
        service_name: str,
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        raise_on_error: bool = True,
    ) -> Optional[requests.Response]:
        """Safely perform GET request"""
        try:
            response = requests.get(
                url,
                timeout=timeout,
                headers=headers,
                params=params,
            )
            
            # Check for rate limiting
            if response.status_code == 429:
                error = RateLimitError(
                    f"Rate limit exceeded for {service_name}",
                    context={"service": service_name, "url": url, **(context or {})},
                )
                handle_error(error, raise_http=False)
                if raise_on_error:
                    raise error
                return None
            
            # Check for other HTTP errors
            if not response.ok:
                error = ExternalServiceError(
                    f"HTTP error from {service_name}: {response.status_code}",
                    context={
                        "service": service_name,
                        "url": url,
                        "status_code": response.status_code,
                        **(context or {})
                    },
                )
                handle_error(error, raise_http=False)
                if raise_on_error:
                    raise error
                return None
            
            return response
            
        except RequestException as e:
            error = external_api_error_handler.handle_requests_error(
                e, service_name, url, context
            )
            handle_error(error, raise_http=False)
            if raise_on_error:
                raise error
            return None
        except Exception as e:
            error = ExternalServiceError(
                f"Unexpected error calling {service_name}: {str(e)}",
                context={"service": service_name, "url": url, **(context or {})},
            )
            handle_error(error, raise_http=False)
            if raise_on_error:
                raise error
            return None
    
    @staticmethod
    def post(
        url: str,
        service_name: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None,
        context: Optional[Dict[str, Any]] = None,
        raise_on_error: bool = True,
    ) -> Optional[requests.Response]:
        """Safely perform POST request"""
        try:
            response = requests.post(
                url,
                data=data,
                json=json,
                timeout=timeout,
                headers=headers,
            )
            
            # Check for rate limiting
            if response.status_code == 429:
                error = RateLimitError(
                    f"Rate limit exceeded for {service_name}",
                    context={"service": service_name, "url": url, **(context or {})},
                )
                handle_error(error, raise_http=False)
                if raise_on_error:
                    raise error
                return None
            
            # Check for other HTTP errors
            if not response.ok:
                error = ExternalServiceError(
                    f"HTTP error from {service_name}: {response.status_code}",
                    context={
                        "service": service_name,
                        "url": url,
                        "status_code": response.status_code,
                        **(context or {})
                    },
                )
                handle_error(error, raise_http=False)
                if raise_on_error:
                    raise error
                return None
            
            return response
            
        except RequestException as e:
            error = external_api_error_handler.handle_requests_error(
                e, service_name, url, context
            )
            handle_error(error, raise_http=False)
            if raise_on_error:
                raise error
            return None
        except Exception as e:
            error = ExternalServiceError(
                f"Unexpected error calling {service_name}: {str(e)}",
                context={"service": service_name, "url": url, **(context or {})},
            )
            handle_error(error, raise_http=False)
            if raise_on_error:
                raise error
            return None
    
    @staticmethod
    async def async_get(
        url: str,
        service_name: str,
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        raise_on_error: bool = True,
    ) -> Optional[aiohttp.ClientResponse]:
        """Safely perform async GET request"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    headers=headers,
                    params=params,
                ) as response:
                    # Check for rate limiting
                    if response.status == 429:
                        error = RateLimitError(
                            f"Rate limit exceeded for {service_name}",
                            context={"service": service_name, "url": url, **(context or {})},
                        )
                        handle_error(error, raise_http=False)
                        if raise_on_error:
                            raise error
                        return None
                    
                    # Check for other HTTP errors
                    if not response.ok:
                        error = ExternalServiceError(
                            f"HTTP error from {service_name}: {response.status}",
                            context={
                                "service": service_name,
                                "url": url,
                                "status_code": response.status,
                                **(context or {})
                            },
                        )
                        handle_error(error, raise_http=False)
                        if raise_on_error:
                            raise error
                        return None
                    
                    return response
                    
        except asyncio.TimeoutError as e:
            error = HybaTimeoutError(
                f"Request to {service_name} timed out: {str(e)}",
                context={"service": service_name, "url": url, **(context or {})},
            )
            handle_error(error, raise_http=False)
            if raise_on_error:
                raise error
            return None
        except aiohttp.ClientError as e:
            error = external_api_error_handler.handle_aiohttp_error(
                e, service_name, url, context
            )
            handle_error(error, raise_http=False)
            if raise_on_error:
                raise error
            return None
        except Exception as e:
            error = ExternalServiceError(
                f"Unexpected error calling {service_name}: {str(e)}",
                context={"service": service_name, "url": url, **(context or {})},
            )
            handle_error(error, raise_http=False)
            if raise_on_error:
                raise error
            return None
    
    @staticmethod
    async def async_post(
        url: str,
        service_name: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None,
        context: Optional[Dict[str, Any]] = None,
        raise_on_error: bool = True,
    ) -> Optional[aiohttp.ClientResponse]:
        """Safely perform async POST request"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    data=data,
                    json=json,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    headers=headers,
                ) as response:
                    # Check for rate limiting
                    if response.status == 429:
                        error = RateLimitError(
                            f"Rate limit exceeded for {service_name}",
                            context={"service": service_name, "url": url, **(context or {})},
                        )
                        handle_error(error, raise_http=False)
                        if raise_on_error:
                            raise error
                        return None
                    
                    # Check for other HTTP errors
                    if not response.ok:
                        error = ExternalServiceError(
                            f"HTTP error from {service_name}: {response.status}",
                            context={
                                "service": service_name,
                                "url": url,
                                "status_code": response.status,
                                **(context or {})
                            },
                        )
                        handle_error(error, raise_http=False)
                        if raise_on_error:
                            raise error
                        return None
                    
                    return response
                    
        except asyncio.TimeoutError as e:
            error = HybaTimeoutError(
                f"Request to {service_name} timed out: {str(e)}",
                context={"service": service_name, "url": url, **(context or {})},
            )
            handle_error(error, raise_http=False)
            if raise_on_error:
                raise error
            return None
        except aiohttp.ClientError as e:
            error = external_api_error_handler.handle_aiohttp_error(
                e, service_name, url, context
            )
            handle_error(error, raise_http=False)
            if raise_on_error:
                raise error
            return None
        except Exception as e:
            error = ExternalServiceError(
                f"Unexpected error calling {service_name}: {str(e)}",
                context={"service": service_name, "url": url, **(context or {})},
            )
            handle_error(error, raise_http=False)
            if raise_on_error:
                raise error
            return None


def with_external_api_error_handling(
    service_name: str,
    default_return: Optional[T] = None,
    context: Optional[Dict[str, Any]] = None,
):
    """Decorator for adding external API error handling to functions"""
    
    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, None]]:
        def wrapper(*args, **kwargs) -> Union[T, None]:
            try:
                return func(*args, **kwargs)
            except RequestException as e:
                error = external_api_error_handler.handle_requests_error(
                    e, service_name, "unknown", {**context, "function": func.__name__}
                )
                handle_error(error, raise_http=False)
                
                if default_return is not None:
                    return default_return
                raise error
            except Exception as e:
                error = ExternalServiceError(
                    f"Unexpected error in {func.__name__}: {str(e)}",
                    context={"service": service_name, **(context or {})},
                )
                handle_error(error, raise_http=False)
                
                if default_return is not None:
                    return default_return
                raise error
        return wrapper
    return decorator


def async_with_external_api_error_handling(
    service_name: str,
    default_return: Optional[T] = None,
    context: Optional[Dict[str, Any]] = None,
):
    """Decorator for adding external API error handling to async functions"""
    
    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, None]]:
        async def wrapper(*args, **kwargs) -> Union[T, None]:
            try:
                return await func(*args, **kwargs)
            except (RequestException, aiohttp.ClientError, asyncio.TimeoutError) as e:
                error = external_api_error_handler.handle_aiohttp_error(
                    e, service_name, "unknown", {**context, "function": func.__name__}
                )
                handle_error(error, raise_http=False)
                
                if default_return is not None:
                    return default_return
                raise error
            except Exception as e:
                error = ExternalServiceError(
                    f"Unexpected error in {func.__name__}: {str(e)}",
                    context={"service": service_name, **(context or {})},
                )
                handle_error(error, raise_http=False)
                
                if default_return is not None:
                    return default_return
                raise error
        return wrapper
    return decorator
