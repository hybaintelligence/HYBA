"""
Tests for HYBA SDK Client
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from hyba_sdk.client import HybaClient
from hyba_sdk.exceptions import (
    HybaApiError,
    AuthenticationError,
    QuotaExceededError,
    ServiceNotFoundError,
    ValidationError,
    RateLimitError,
)
from hyba_sdk.connector import ConnectorConfig, ConnectorType


@pytest.fixture
def mock_response():
    """Mock HTTP response"""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"status": "ok"}
    return response


@pytest.fixture
def client():
    """Create test client"""
    return HybaClient(api_key="hyba_live_test_key_123")


class TestHybaClient:
    """Test HybaClient initialization and configuration"""
    
    def test_client_initialization(self):
        """Test client initialization with default values"""
        client = HybaClient(api_key="hyba_live_test")
        
        assert client.api_key == "hyba_live_test"
        assert client.base_url == "https://api.hyba.ai"
        assert client.timeout == 30
    
    def test_client_custom_base_url(self):
        """Test client with custom base URL"""
        client = HybaClient(
            api_key="hyba_live_test",
            base_url="https://sandbox.api.hyba.ai"
        )
        
        assert client.base_url == "https://sandbox.api.hyba.ai"
    
    def test_client_custom_timeout(self):
        """Test client with custom timeout"""
        client = HybaClient(
            api_key="hyba_live_test",
            timeout=60
        )
        
        assert client.timeout == 60
    
    def test_client_headers(self, client):
        """Test client sets correct headers"""
        assert "X-API-Key" in client.session.headers
        assert client.session.headers["X-API-Key"] == "hyba_live_test_key_123"
        assert client.session.headers["Content-Type"] == "application/json"
        assert "hyba-sdk-py" in client.session.headers["User-Agent"]
    
    @patch("hyba_sdk.client.requests.Session.request")
    def test_request_success(self, mock_request, client, mock_response):
        """Test successful API request"""
        mock_request.return_value = mock_response
        
        result = client._request("GET", "/api/health")
        
        assert result == {"status": "ok"}
        mock_request.assert_called_once()
    
    @patch("hyba_sdk.client.requests.Session.request")
    def test_request_authentication_error(self, mock_request, client):
        """Test authentication error handling"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid API key"}
        mock_request.return_value = mock_response
        
        with pytest.raises(AuthenticationError) as exc_info:
            client._request("GET", "/api/test")
        
        assert "Invalid API key" in str(exc_info.value)
        assert exc_info.value.status_code == 401
    
    @patch("hyba_sdk.client.requests.Session.request")
    def test_request_quota_exceeded(self, mock_request, client):
        """Test quota exceeded error handling"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "detail": "Quota exceeded",
            "quota": {"reset_at": "2026-06-21T00:00:00Z"}
        }
        mock_request.return_value = mock_response
        
        with pytest.raises(QuotaExceededError) as exc_info:
            client._request("GET", "/api/test")
        
        assert "Quota exceeded" in str(exc_info.value)
        assert exc_info.value.quota_info["reset_at"] == "2026-06-21T00:00:00Z"
    
    @patch("hyba_sdk.client.requests.Session.request")
    def test_request_rate_limit_with_retry_after(self, mock_request, client):
        """Test rate limit error with Retry-After header"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"detail": "Rate limit exceeded"}
        mock_response.headers = {"Retry-After": "60"}
        mock_request.return_value = mock_response
        
        with pytest.raises(RateLimitError) as exc_info:
            client._request("GET", "/api/test")
        
        assert exc_info.value.retry_after == 60
    
    @patch("hyba_sdk.client.requests.Session.request")
    def test_request_validation_error(self, mock_request, client):
        """Test validation error handling"""
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.json.return_value = {
            "detail": "Validation failed",
            "errors": {"name": "too short", "code_distance": "must be >= 3"}
        }
        mock_request.return_value = mock_response
        
        with pytest.raises(ValidationError) as exc_info:
            client._request("POST", "/api/test", json={})
        
        assert "Validation failed" in str(exc_info.value)
        assert "name" in exc_info.value.validation_errors
    
    @patch("hyba_sdk.client.requests.Session.request")
    def test_request_timeout(self, mock_request, client):
        """Test request timeout handling"""
        import requests.exceptions
        mock_request.side_effect = requests.exceptions.Timeout()
        
        with pytest.raises(HybaApiError) as exc_info:
            client._request("GET", "/api/test")
        
        assert "timed out" in str(exc_info.value).lower()
    
    @patch("hyba_sdk.client.requests.Session.request")
    def test_request_connection_error(self, mock_request, client):
        """Test connection error handling"""
        import requests.exceptions
        mock_request.side_effect = requests.exceptions.ConnectionError()
        
        with pytest.raises(HybaApiError) as exc_info:
            client._request("GET", "/api/test")
        
        assert "connect" in str(exc_info.value).lower()


class TestHybaClientServiceManagement:
    """Test service management methods"""
    
    @patch("hyba_sdk.client.requests.Session.request")
    def test_provision_service(self, mock_request, client):
        """Test service provisioning"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "service_id": "hyba-ciaas-001",
            "name": "test-service",
            "state": "provisioned",
            "service_tier": "production",
            "tenancy": "single-tenant",
            "owner": "customer-123",
            "created_at": "2026-06-20T10:00:00Z",
            "updated_at": "2026-06-20T10:00:00Z",
            "commercial_policy": {},
            "fault_tolerance": {},
            "substrate": {},
            "evidence_seal": "abc123",
            "claim_boundary": "test",
        }
        mock_request.return_value = mock_response
        
        service = client.provision_service(name="test-service")
        
        assert service.service_id == "hyba-ciaas-001"
        assert service.name == "test-service"
        assert service.state == "provisioned"
        
        # Verify request was made correctly
        call_args = mock_request.call_args
        assert call_args[1]["json"]["name"] == "test-service"
    
    @patch("hyba_sdk.client.requests.Session.request")
    def test_provision_service_with_connector(self, mock_request, client):
        """Test service provisioning with connector"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "service_id": "hyba-ciaas-002",
            "name": "test-service",
            "state": "provisioned",
            "service_tier": "production",
            "tenancy": "single-tenant",
            "owner": "customer-123",
            "created_at": "2026-06-20T10:00:00Z",
            "updated_at": "2026-06-20T10:00:00Z",
            "commercial_policy": {},
            "fault_tolerance": {},
            "substrate": {},
            "evidence_seal": "abc123",
            "claim_boundary": "test",
        }
        mock_request.return_value = mock_response
        
        connector = ConnectorConfig(
            type=ConnectorType.SQL_SNOWFLAKE,
            host="acme.snowflakecomputing.com",
            database="finance_dw",
            query="SELECT * FROM positions"
        )
        
        service = client.provision_service(
            name="test-service",
            connector=connector
        )
        
        # Verify connector was included in request
        call_args = mock_request.call_args
        assert "connector" in call_args[1]["json"]
        assert call_args[1]["json"]["connector"]["type"] == "sql_snowflake"
    
    @patch("hyba_sdk.client.requests.Session.request")
    def test_list_services(self, mock_request, client):
        """Test listing services"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "service_id": "svc-001",
                "name": "service-1",
                "state": "running",
                "service_tier": "production",
                "tenancy": "single-tenant",
                "owner": "customer-123",
                "created_at": "2026-06-20T10:00:00Z",
                "updated_at": "2026-06-20T10:00:00Z",
                "commercial_policy": {},
                "fault_tolerance": {},
                "substrate": {},
                "evidence_seal": "abc",
                "claim_boundary": "test",
            },
            {
                "service_id": "svc-002",
                "name": "service-2",
                "state": "stopped",
                "service_tier": "developer",
                "tenancy": "single-tenant",
                "owner": "customer-123",
                "created_at": "2026-06-20T10:00:00Z",
                "updated_at": "2026-06-20T10:00:00Z",
                "commercial_policy": {},
                "fault_tolerance": {},
                "substrate": {},
                "evidence_seal": "def",
                "claim_boundary": "test",
            }
        ]
        mock_request.return_value = mock_response
        
        services = client.list_services()
        
        assert len(services) == 2
        assert services[0].service_id == "svc-001"
        assert services[1].service_id == "svc-002"
    
    @patch("hyba_sdk.client.requests.Session.request")
    def test_get_service(self, mock_request, client):
        """Test getting service by ID"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "service_id": "svc-001",
            "name": "test-service",
            "state": "running",
            "service_tier": "production",
            "tenancy": "single-tenant",
            "owner": "customer-123",
            "created_at": "2026-06-20T10:00:00Z",
            "updated_at": "2026-06-20T10:00:00Z",
            "commercial_policy": {},
            "fault_tolerance": {},
            "substrate": {},
            "evidence_seal": "abc",
            "claim_boundary": "test",
        }
        mock_request.return_value = mock_response
        
        service = client.get_service("svc-001")
        
        assert service.service_id == "svc-001"
        assert service.name == "test-service"
    
    @patch("hyba_sdk.client.requests.Session.request")
    def test_health_check(self, mock_request, client):
        """Test health check"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_request.return_value = mock_response
        
        health = client.health_check()
        
        assert health["status"] == "healthy"
    
    def test_context_manager(self, client):
        """Test context manager usage"""
        with client as c:
            assert c is client
            assert c.session is not None
        
        # Session should be closed after exiting context
        # (we can't easily test this without mocking close)


class TestConnectorConfig:
    """Test ConnectorConfig"""
    
    def test_connector_config_creation(self):
        """Test creating connector config"""
        connector = ConnectorConfig(
            type=ConnectorType.SQL_SNOWFLAKE,
            host="acme.snowflakecomputing.com",
            database="finance_dw",
            query="SELECT * FROM positions"
        )
        
        assert connector.type == ConnectorType.SQL_SNOWFLAKE
        assert connector.host == "acme.snowflakecomputing.com"
        assert connector.database == "finance_dw"
    
    def test_connector_to_dict(self):
        """Test converting connector to dictionary"""
        connector = ConnectorConfig(
            type=ConnectorType.SQL_SNOWFLAKE,
            host="acme.snowflakecomputing.com",
            database="finance_dw",
            query="SELECT * FROM positions"
        )
        
        result = connector.to_dict()
        
        assert result["type"] == "sql_snowflake"
        assert result["host"] == "acme.snowflakecomputing.com"
        assert result["database"] == "finance_dw"
        assert result["query"] == "SELECT * FROM positions"
    
    def test_connector_to_dict_optional_fields(self):
        """Test that None values are excluded from dict"""
        connector = ConnectorConfig(
            type=ConnectorType.HTTP,
            endpoint="https://api.example.com"
        )
        
        result = connector.to_dict()
        
        assert "host" not in result
        assert "database" not in result
        assert result["endpoint"] == "https://api.example.com"
    
    def test_connector_from_dict(self):
        """Test creating connector from dictionary"""
        data = {
            "type": "sql_snowflake",
            "host": "acme.snowflakecomputing.com",
            "database": "finance_dw"
        }
        
        connector = ConnectorConfig.from_dict(data)
        
        assert connector.type == ConnectorType.SQL_SNOWFLAKE
        assert connector.host == "acme.snowflakecomputing.com"
        assert connector.database == "finance_dw"
    
    def test_connector_from_dict_unknown_type(self):
        """Test from_dict with unknown type defaults to HTTP"""
        data = {"type": "unknown_type", "endpoint": "https://api.example.com"}
        
        connector = ConnectorConfig.from_dict(data)
        
        assert connector.type == ConnectorType.HTTP
    
    def test_connector_repr(self):
        """Test connector string representation"""
        connector = ConnectorConfig(
            type=ConnectorType.SQL_POSTGRESQL,
            host="localhost"
        )
        
        result = repr(connector)
        
        assert "sql_postgresql" in result
        assert "localhost" in result