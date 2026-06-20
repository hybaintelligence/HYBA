"""
HYBA Sandbox Environment API
Isolated testing environment for development and integration testing
"""

from fastapi import APIRouter, HTTPException, Depends, Header, Body
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/v1/sandbox", tags=["sandbox"])


class SandboxMode(str):
    """Sandbox execution modes"""
    MOCK = "mock"           # Return mock data
    REPLAY = "replay"        # Replay recorded sessions
    ISOLATED = "isolated"    # Isolated environment


class SandboxService(BaseModel):
    """Sandboxed service instance"""
    service_id: str
    name: str
    tier: str = "developer"
    mode: SandboxMode = SandboxMode.MOCK
    created_at: datetime
    quota_requests: int = 100
    quota_remaining: int = 100
    expires_at: datetime  # Sandbox expires after 24 hours


class MockExecutionResult(BaseModel):
    """Mock execution result for testing"""
    workload_type: str
    status: str = "completed"
    latency_ms: float
    result: Dict[str, Any]
    usage: Dict[str, Any]


class SandboxFixture(BaseModel):
    """Test data fixture"""
    fixture_id: str
    name: str
    description: str
    size_bytes: int
    created_at: datetime


@router.post("/services", response_model=SandboxService)
async def create_sandbox_service(
    name: str = Field(..., description="Service name"),
    tier: str = Field(default="developer", description="Service tier"),
    mode: SandboxMode = Field(default=SandboxMode.MOCK, description="Sandbox mode"),
    customer_id: str = Header(..., description="Customer ID")
) -> SandboxService:
    """
    Create a sandboxed service for testing
    
    Sandbox services:
    - Don't consume quota
    - Return mock/simulated data
    - Expire after 24 hours
    - Isolated from production
    
    Example:
    ```bash
    curl -X POST https://api.hyba.ai/v1/sandbox/services \
      -H "X-API-Key: sb_live_..." \
      -H "Content-Type: application/json" \
      -d '{
        "name": "portfolio-test",
        "tier": "developer",
        "mode": "mock"
      }'
    ```
    """
    service_id = f"hyba-sandbox-{uuid.uuid4().hex[:8]}"
    created_at = datetime.utcnow()
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    return SandboxService(
        service_id=service_id,
        name=name,
        tier=tier,
        mode=mode,
        created_at=created_at,
        expires_at=expires_at,
        quota_requests=100,
        quota_remaining=100
    )


@router.post("/services/{service_id}/execute", response_model=MockExecutionResult)
async def execute_sandbox_workload(
    service_id: str,
    workload_type: str = Field(..., description="Workload type"),
    context: str = Field(..., description="Workload context"),
    mode: SandboxMode = Field(default=SandboxMode.MOCK)
) -> MockExecutionResult:
    """
    Execute workload in sandbox (returns mock data)
    
    Example:
    ```bash
    curl -X POST https://api.hyba.ai/v1/sandbox/services/hyba-sandbox-abc123/execute \
      -H "X-API-Key: sb_live_..." \
      -H "Content-Type: application/json" \
      -d '{
        "workload_type": "explain",
        "context": "Portfolio optimization strategy",
        "mode": "mock"
      }'
    ```
    """
    # Generate mock results based on workload type
    mock_results = {
        "explain": {
            "explanation": "Mock explanation for testing",
            "confidence": 0.95,
            "reasoning": [
                "Mock reasoning point 1",
                "Mock reasoning point 2"
            ]
        },
        "orchestrate": {
            "orchestration_result": "Simulated orchestration complete",
            "steps": [
                {"step": 1, "action": "mock_action_1", "status": "completed"},
                {"step": 2, "action": "mock_action_2", "status": "completed"}
            ]
        },
        "counterfactual": {
            "original": {"value": 100},
            "counterfactual": {"value": 105},
            "change": 5.0
        },
        "governance_audit": {
            "audit_status": "mock_pass",
            "checks": [
                {"check": "Authorization", "status": "pass"},
                {"check": "Audit Trail", "status": "pass"}
            ]
        }
    }
    
    result = mock_results.get(workload_type, {"mock": True, "status": "ok"})
    
    return MockExecutionResult(
        workload_type=workload_type,
        status="completed",
        latency_ms=123.45,
        result=result,
        usage={
            "requests": 1,
            "compute_units": 0,
            "cost": 0.0
        }
    )


@router.get("/fixtures", response_model=List[SandboxFixture])
async def list_sandbox_fixtures() -> List[SandboxFixture]:
    """
    List available test data fixtures
    
    Fixtures provide realistic test data for:
    - Portfolio datasets (100, 500, 1000 stocks)
    - Molecular data (100, 1K, 10K compounds)
    - SCADA sensor data (24h, 7d, 30d)
    - Market data (daily, intraday)
    
    Example:
    ```bash
    curl https://api.hyba.ai/v1/sandbox/fixtures \
      -H "X-API-Key: sb_live_..."
    ```
    """
    fixtures = [
        SandboxFixture(
            fixture_id="portfolio_100stocks",
            name="Portfolio: 100 Stocks (1 Year)",
            description="Historical data for 100 stocks, 1 year period",
            size_bytes=5_242_880,  # 5 MB
            created_at=datetime.utcnow()
        ),
        SandboxFixture(
            fixture_id="portfolio_500stocks",
            name="Portfolio: 500 Stocks (1 Year)",
            description="Historical data for 500 stocks, 1 year period",
            size_bytes=26_214_400,  # 25 MB
            created_at=datetime.utcnow()
        ),
        SandboxFixture(
            fixture_id="molecules_1k",
            name="Molecules: 1,000 Compounds (SMILES Format)",
            description="1,000 chemical compounds in SMILES format",
            size_bytes=104_857_600,  # 100 MB
            created_at=datetime.utcnow()
        ),
        SandboxFixture(
            fixture_id="molecules_10k",
            name="Molecules: 10,000 Compounds (SDF Format)",
            description="10,000 chemical compounds in SDF format with properties",
            size_bytes=1_073_741_824,  # 1 GB
            created_at=datetime.utcnow()
        ),
        SandboxFixture(
            fixture_id="scada_24h",
            name="SCADA: 24 Hours Sensor Data",
            description="Sensor readings from SCADA system, 24 hour period",
            size_bytes=52_428_800,  # 50 MB
            created_at=datetime.utcnow()
        ),
        SandboxFixture(
            fixture_id="scada_7d",
            name="SCADA: 7 Days Sensor Data",
            description="Sensor readings from SCADA system, 7 day period",
            size_bytes=262_144_000,  # 250 MB
            created_at=datetime.utcnow()
        ),
        SandboxFixture(
            fixture_id="market_data_daily",
            name="Market Data: Daily Quotes (2 Years)",
            description="Daily OHLCV data for major indices and equities",
            size_bytes=104_857_600,  # 100 MB
            created_at=datetime.utcnow()
        ),
    ]
    
    return fixtures


@router.get("/fixtures/{fixture_id}")
async def download_sandbox_fixture(fixture_id: str):
    """
    Download test data fixture
    
    Returns fixture data as CSV/JSON/Parquet
    
    Example:
    ```bash
    curl -O https://api.hyba.ai/v1/sandbox/fixtures/portfolio_100stocks \
      -H "X-API-Key: sb_live_..."
    ```
    """
    valid_fixtures = [
        "portfolio_100stocks",
        "portfolio_500stocks",
        "molecules_1k",
        "molecules_10k",
        "scada_24h",
        "scada_7d",
        "market_data_daily"
    ]
    
    if fixture_id not in valid_fixtures:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    # Return mock data (in production, would stream actual file)
    mock_data = {
        "portfolio_100stocks": [
            {"ticker": "AAPL", "date": "2025-01-01", "close": 150.25},
            {"ticker": "MSFT", "date": "2025-01-01", "close": 375.50},
        ],
        "molecules_1k": [
            {"id": 1, "smiles": "CCO", "name": "ethanol"},
            {"id": 2, "smiles": "CC(C)O", "name": "isopropanol"},
        ],
        "scada_24h": [
            {"timestamp": "2025-01-01T00:00:00Z", "sensor_1": 42.5, "sensor_2": 98.2},
            {"timestamp": "2025-01-01T00:01:00Z", "sensor_1": 42.7, "sensor_2": 98.1},
        ]
    }
    
    data = mock_data.get(fixture_id, [{"mock": True}])
    
    return {
        "fixture_id": fixture_id,
        "format": "json",
        "row_count": len(data),
        "data": data
    }


@router.post("/replay-sessions", response_model=Dict[str, Any])
async def create_replay_session(
    recordings: List[Dict[str, Any]] = Field(
        ...,
        description="List of request/response recordings"
    )
) -> Dict[str, Any]:
    """
    Create replay session from recorded interactions
    
    Use this to replay recorded API interactions for testing
    
    Example:
    ```json
    {
      "recordings": [
        {
          "request": {
            "method": "POST",
            "url": "/api/v1/provision",
            "body": {...}
          },
          "response": {
            "status": 200,
            "body": {...}
          }
        }
      ]
    }
    ```
    """
    session_id = f"replay_{uuid.uuid4().hex[:8]}"
    
    return {
        "session_id": session_id,
        "recording_count": len(recordings),
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
    }


@router.get("/status", response_model=Dict[str, Any])
async def sandbox_status() -> Dict[str, Any]:
    """Get sandbox environment status"""
    return {
        "status": "operational",
        "fixtures_available": 7,
        "sandbox_services": 42,
        "quota_per_service": 100,
        "service_lifetime_hours": 24,
        "modes": ["mock", "replay", "isolated"]
    }


# Import for type hints
from datetime import timedelta
