"""
Tests for HYBA SDK Service
"""

import pytest
from unittest.mock import Mock, patch
from hyba_sdk.client import HybaClient
from hyba_sdk.service import ComputationalIntelligenceService
from hyba_sdk.exceptions import ServiceStateError, ServiceNotFoundError


@pytest.fixture
def mock_client():
    """Mock HybaClient"""
    client = Mock(spec=HybaClient)
    client._request = Mock()
    return client


@pytest.fixture
def service(mock_client):
    """Create test service"""
    return ComputationalIntelligenceService(
        client=mock_client,
        service_id="svc-001",
        name="test-service",
        state="provisioned",
        service_tier="production",
        tenancy="single-tenant",
        owner="customer-123",
        created_at="2026-06-20T10:00:00Z",
        updated_at="2026-06-20T10:00:00Z",
        commercial_policy={},
        fault_tolerance={},
        substrate={},
        evidence_seal="abc123",
        claim_boundary="test"
    )


class TestComputationalIntelligenceService:
    """Test ComputationalIntelligenceService"""
    
    def test_service_initialization(self, service):
        """Test service initialization"""
        assert service.service_id == "svc-001"
        assert service.name == "test-service"
        assert service.state == "provisioned"
        assert service.service_tier == "production"
    
    def test_service_repr(self, service):
        """Test service string representation"""
        result = repr(service)
        assert "svc-001" in result
        assert "test-service" in result
        assert "provisioned" in result
    
    def test_service_str(self, service):
        """Test service string conversion"""
        result = str(service)
        assert "test-service" in result
        assert "svc-001" in result


class TestServiceLifecycle:
    """Test service lifecycle methods"""
    
    def test_start_service_from_provisioned(self, service, mock_client):
        """Test starting a provisioned service"""
        mock_client._request.return_value = {
            "service_id": "svc-001",
            "state": "running",
            "updated_at": "2026-06-20T10:01:00Z"
        }
        
        result = service.start()
        
        assert service.state == "running"
        mock_client._request.assert_called_once()
        call_args = mock_client._request.call_args
        assert call_args[0] == ("POST", "/api/v1/computational-intelligence-services/svc-001/start")
    
    def test_start_service_from_stopped(self, service, mock_client):
        """Test starting a stopped service"""
        service.state = "stopped"
        mock_client._request.return_value = {
            "service_id": "svc-001",
            "state": "running",
            "updated_at": "2026-06-20T10:01:00Z"
        }
        
        result = service.start()
        
        assert service.state == "running"
    
    def test_start_service_from_running_raises_error(self, service, mock_client):
        """Test starting a running service raises error"""
        service.state = "running"
        
        with pytest.raises(ServiceStateError) as exc_info:
            service.start()
        
        assert exc_info.value.current_state == "running"
        assert exc_info.value.operation == "start"
        mock_client._request.assert_not_called()
    
    def test_stop_service_from_running(self, service, mock_client):
        """Test stopping a running service"""
        service.state = "running"
        mock_client._request.return_value = {
            "service_id": "svc-001",
            "state": "stopped",
            "updated_at": "2026-06-20T10:02:00Z"
        }
        
        result = service.stop()
        
        assert service.state == "stopped"
        mock_client._request.assert_called_once()
        call_args = mock_client._request.call_args
        assert call_args[0] == ("POST", "/api/v1/computational-intelligence-services/svc-001/stop")
    
    def test_stop_service_from_stopped_raises_error(self, service, mock_client):
        """Test stopping a stopped service raises error"""
        service.state = "stopped"
        
        with pytest.raises(ServiceStateError) as exc_info:
            service.stop()
        
        assert exc_info.value.current_state == "stopped"
        assert exc_info.value.operation == "stop"
        mock_client._request.assert_not_called()


class TestServiceExecution:
    """Test service execution methods"""
    
    def test_execute_workload(self, service, mock_client):
        """Test executing a workload"""
        service.state = "running"
        mock_client._request.return_value = {
            "result": {"explanation": "Test result"},
            "usage": {"compute_units": 100}
        }
        
        result = service.execute(
            workload="explain",
            context="test context"
        )
        
        assert result["result"]["explanation"] == "Test result"
        mock_client._request.assert_called_once()
        call_args = mock_client._request.call_args
        assert call_args[0] == ("POST", "/api/v1/computational-intelligence-services/svc-001/execute")
        assert call_args[1]["json"]["workload_type"] == "explain"
        assert call_args[1]["json"]["context"] == "test context"
    
    def test_execute_workload_not_running_raises_error(self, service, mock_client):
        """Test executing workload when not running raises error"""
        service.state = "provisioned"
        
        with pytest.raises(ServiceStateError) as exc_info:
            service.execute(workload="explain", context="test")
        
        assert exc_info.value.current_state == "provisioned"
        assert exc_info.value.operation == "execute"
        mock_client._request.assert_not_called()
    
    def test_explain_convenience_method(self, service, mock_client):
        """Test explain convenience method"""
        service.state = "running"
        mock_client._request.return_value = {"result": "explanation"}
        
        result = service.explain("test context")
        
        assert result["result"] == "explanation"
        call_args = mock_client._request.call_args
        assert call_args[1]["json"]["workload_type"] == "explain"
    
    def test_orchestrate_convenience_method(self, service, mock_client):
        """Test orchestrate convenience method"""
        service.state = "running"
        mock_client._request.return_value = {"result": "orchestration"}
        
        result = service.orchestrate("test context")
        
        assert result["result"] == "orchestration"
        call_args = mock_client._request.call_args
        assert call_args[1]["json"]["workload_type"] == "orchestrate"
    
    def test_counterfactual_convenience_method(self, service, mock_client):
        """Test counterfactual convenience method"""
        service.state = "running"
        mock_client._request.return_value = {"result": "counterfactual"}
        
        result = service.counterfactual("test context")
        
        assert result["result"] == "counterfactual"
        call_args = mock_client._request.call_args
        assert call_args[1]["json"]["workload_type"] == "counterfactual"
    
    def test_governance_audit_convenience_method(self, service, mock_client):
        """Test governance_audit convenience method"""
        service.state = "running"
        mock_client._request.return_value = {"result": "audit"}
        
        result = service.governance_audit("test context")
        
        assert result["result"] == "audit"
        call_args = mock_client._request.call_args
        assert call_args[1]["json"]["workload_type"] == "governance_audit"
    
    def test_substrate_health_convenience_method(self, service, mock_client):
        """Test substrate_health convenience method"""
        service.state = "running"
        mock_client._request.return_value = {"health": "ok"}
        
        result = service.substrate_health()
        
        assert result["health"] == "ok"
        call_args = mock_client._request.call_args
        assert call_args[1]["json"]["workload_type"] == "substrate_health"
        assert call_args[1]["json"]["context"] == ""


class TestServiceRefreshAndDelete:
    """Test service refresh and delete"""
    
    def test_refresh_service(self, service, mock_client):
        """Test refreshing service metadata"""
        mock_client._request.return_value = {
            "service_id": "svc-001",
            "state": "running",
            "updated_at": "2026-06-20T10:05:00Z",
            "usage": {"compute_units": 500}
        }
        
        result = service.refresh()
        
        assert result is service  # Should return self
        assert service.state == "running"
        assert service.updated_at == "2026-06-20T10:05:00Z"
        assert service.usage["compute_units"] == 500
    
    def test_delete_service(self, service, mock_client):
        """Test deleting service"""
        mock_client._request.return_value = {"deleted": True}
        
        result = service.delete()
        
        assert result is True
        mock_client._request.assert_called_once()
        call_args = mock_client._request.call_args
        assert call_args[0] == ("DELETE", "/api/v1/computational-intelligence-services/svc-001")
    
    def test_delete_service_false_response(self, service, mock_client):
        """Test delete service with false response"""
        mock_client._request.return_value = {"deleted": False}
        
        result = service.delete()
        
        assert result is False