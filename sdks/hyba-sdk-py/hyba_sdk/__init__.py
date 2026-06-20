"""
HYBA SDK for Python
Official Python SDK for HYBA QaaS/CIaaS platform

Example:
    >>> from hyba_sdk import HybaClient
    >>> client = HybaClient(api_key="hyba_live_...")
    >>> service = client.provision_service(name="my-optimizer")
    >>> result = service.execute(workload="explain", context="test")
"""

__version__ = "1.0.0"
__author__ = "HYBA Analytics"

from hyba_sdk.client import HybaClient
from hyba_sdk.service import ComputationalIntelligenceService
from hyba_sdk.connector import ConnectorConfig
from hyba_sdk.exceptions import (
    HybaApiError,
    AuthenticationError,
    QuotaExceededError,
    ServiceNotFoundError,
    ValidationError,
)

__all__ = [
    "HybaClient",
    "ComputationalIntelligenceService",
    "ConnectorConfig",
    "HybaApiError",
    "AuthenticationError",
    "QuotaExceededError",
    "ServiceNotFoundError",
    "ValidationError",
]