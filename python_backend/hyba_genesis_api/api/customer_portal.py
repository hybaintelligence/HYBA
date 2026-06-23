"""
Customer Portal API
Self-service customer management, usage tracking, and API key provisioning.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import hashlib
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..auth import get_current_user, require_api_key
from ..database import get_db_connection

router = APIRouter(prefix="/api/customer", tags=["customer_portal"])


# ── Request/Response Models ───────────────────────────────────────────────


class APIKeyResponse(BaseModel):
    api_key_id: str
    api_key: str  # Only returned on creation
    name: str
    created_at: str
    last_used_at: Optional[str]
    status: str


class CreateAPIKeyRequest(BaseModel):
    name: str = Field(..., description="Friendly name for this API key")
    description: Optional[str] = None


class UsageResponse(BaseModel):
    compute_units_used: int
    compute_units_quota: int
    current_period_cost: float
    currency: str
    period_start: str
    period_end: str
    breakdown: Dict[str, int]


class UsageHistoryResponse(BaseModel):
    history: List[Dict]
    total_records: int


class QuotaAlertConfig(BaseModel):
    enabled: bool
    threshold_percent: int = Field(ge=50, le=100)
    notification_email: Optional[str]


# ── Helper Functions ──────────────────────────────────────────────────────


def generate_api_key() -> tuple[str, str]:
    """
    Generate HMAC-SHA256 API key.
    Returns: (api_key, hashed_key)
    """
    random_bytes = secrets.token_bytes(32)
    api_key = f"hyba_{secrets.token_urlsafe(32)}"
    hashed_key = hashlib.sha256(api_key.encode()).hexdigest()
    return api_key, hashed_key


def calculate_usage(customer_id: str, period_start: datetime, period_end: datetime) -> Dict:
    """
    Calculate compute unit usage for a customer in a given period.
    This would query actual execution logs in production.
    """
    # Placeholder: In production, query execution logs
    return {
        "qaas": 1250,
        "qiaas": 3400,
        "ciaas": 2100,
        "quantum_finance": 850,
    }


def get_customer_tier(customer_id: str) -> Dict:
    """
    Get customer tier and quota.
    """
    # Placeholder: In production, query customer subscription
    return {
        "tier": "production",
        "compute_units_quota": 10000,
        "cost_per_unit": 0.01,
        "currency": "USD",
    }


# ── API Key Management ────────────────────────────────────────────────────


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Generate a new API key for the customer.
    Returns the key ONCE - customer must save it.
    """
    customer_id = current_user["id"]
    api_key, hashed_key = generate_api_key()
    
    # Store in database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    api_key_id = f"key_{secrets.token_hex(8)}"
    now = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO api_keys (
            api_key_id, customer_id, hashed_key, name, description, 
            created_at, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        api_key_id, customer_id, hashed_key, request.name,
        request.description, now, "active"
    ))
    
    conn.commit()
    conn.close()
    
    return APIKeyResponse(
        api_key_id=api_key_id,
        api_key=api_key,  # Only returned on creation
        name=request.name,
        created_at=now,
        last_used_at=None,
        status="active"
    )


@router.get("/api-keys", response_model=List[Dict])
async def list_api_keys(
    current_user: Dict = Depends(get_current_user)
):
    """
    List all API keys for the current customer.
    Does NOT return the actual key values (only IDs and metadata).
    """
    customer_id = current_user["id"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT api_key_id, name, created_at, last_used_at, status
        FROM api_keys
        WHERE customer_id = ? AND status != 'deleted'
        ORDER BY created_at DESC
    """, (customer_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "api_key_id": row[0],
            "name": row[1],
            "created_at": row[2],
            "last_used_at": row[3],
            "status": row[4],
        }
        for row in rows
    ]


@router.delete("/api-keys/{api_key_id}")
async def revoke_api_key(
    api_key_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Revoke (delete) an API key.
    """
    customer_id = current_user["id"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE api_keys
        SET status = 'deleted', deleted_at = ?
        WHERE api_key_id = ? AND customer_id = ?
    """, (datetime.utcnow().isoformat(), api_key_id, customer_id))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    conn.commit()
    conn.close()
    
    return {"status": "revoked", "api_key_id": api_key_id}


# ── Usage Tracking ────────────────────────────────────────────────────────


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get current billing period usage for the customer.
    """
    customer_id = current_user["id"]
    
    # Calculate current billing period (monthly)
    now = datetime.utcnow()
    period_start = datetime(now.year, now.month, 1)
    if now.month == 12:
        period_end = datetime(now.year + 1, 1, 1) - timedelta(seconds=1)
    else:
        period_end = datetime(now.year, now.month + 1, 1) - timedelta(seconds=1)
    
    # Get customer tier and quota
    tier_info = get_customer_tier(customer_id)
    
    # Calculate usage breakdown
    breakdown = calculate_usage(customer_id, period_start, period_end)
    total_units = sum(breakdown.values())
    
    # Calculate cost
    cost = total_units * tier_info["cost_per_unit"]
    
    return UsageResponse(
        compute_units_used=total_units,
        compute_units_quota=tier_info["compute_units_quota"],
        current_period_cost=cost,
        currency=tier_info["currency"],
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat(),
        breakdown=breakdown
    )


@router.get("/usage/history", response_model=UsageHistoryResponse)
async def get_usage_history(
    months: int = 6,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get historical usage data for the customer.
    """
    customer_id = current_user["id"]
    
    history = []
    now = datetime.utcnow()
    
    for i in range(months):
        # Calculate period
        month_offset = i
        year = now.year
        month = now.month - month_offset
        
        while month <= 0:
            month += 12
            year -= 1
        
        period_start = datetime(year, month, 1)
        if month == 12:
            period_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            period_end = datetime(year, month + 1, 1) - timedelta(seconds=1)
        
        # Get usage for this period
        breakdown = calculate_usage(customer_id, period_start, period_end)
        total_units = sum(breakdown.values())
        tier_info = get_customer_tier(customer_id)
        
        history.append({
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "compute_units_used": total_units,
            "cost": total_units * tier_info["cost_per_unit"],
            "currency": tier_info["currency"],
            "breakdown": breakdown
        })
    
    return UsageHistoryResponse(
        history=history,
        total_records=len(history)
    )


# ── Quota Alerts ──────────────────────────────────────────────────────────


@router.get("/quota-alerts")
async def get_quota_alert_config(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get quota alert configuration for the customer.
    """
    customer_id = current_user["id"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT enabled, threshold_percent, notification_email
        FROM quota_alerts
        WHERE customer_id = ?
    """, (customer_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        # Default config
        return {
            "enabled": True,
            "threshold_percent": 90,
            "notification_email": current_user.get("email")
        }
    
    return {
        "enabled": bool(row[0]),
        "threshold_percent": row[1],
        "notification_email": row[2]
    }


@router.put("/quota-alerts")
async def update_quota_alert_config(
    config: QuotaAlertConfig,
    current_user: Dict = Depends(get_current_user)
):
    """
    Update quota alert configuration.
    """
    customer_id = current_user["id"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO quota_alerts (
            customer_id, enabled, threshold_percent, notification_email, updated_at
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        customer_id, config.enabled, config.threshold_percent,
        config.notification_email, datetime.utcnow().isoformat()
    ))
    
    conn.commit()
    conn.close()
    
    return {"status": "updated", "config": config.dict()}


# ── Billing ───────────────────────────────────────────────────────────────


@router.get("/billing/invoices")
async def get_invoices(
    limit: int = 12,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get billing invoices for the customer.
    """
    customer_id = current_user["id"]
    
    # Placeholder: In production, query billing system
    invoices = []
    now = datetime.utcnow()
    
    for i in range(min(limit, 12)):
        month_offset = i
        year = now.year
        month = now.month - month_offset
        
        while month <= 0:
            month += 12
            year -= 1
        
        period_start = datetime(year, month, 1)
        
        breakdown = calculate_usage(customer_id, period_start, period_start)
        total_units = sum(breakdown.values())
        tier_info = get_customer_tier(customer_id)
        
        invoices.append({
            "invoice_id": f"inv_{year}{month:02d}_{secrets.token_hex(4)}",
            "period": f"{year}-{month:02d}",
            "amount": total_units * tier_info["cost_per_unit"],
            "currency": tier_info["currency"],
            "status": "paid" if i > 0 else "pending",
            "issued_at": period_start.isoformat()
        })
    
    return {
        "invoices": invoices,
        "total": len(invoices)
    }


@router.get("/billing/current")
async def get_current_bill(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get current month's bill (real-time).
    """
    customer_id = current_user["id"]
    
    now = datetime.utcnow()
    period_start = datetime(now.year, now.month, 1)
    
    breakdown = calculate_usage(customer_id, period_start, now)
    total_units = sum(breakdown.values())
    tier_info = get_customer_tier(customer_id)
    
    return {
        "period": f"{now.year}-{now.month:02d}",
        "compute_units_used": total_units,
        "current_amount": total_units * tier_info["cost_per_unit"],
        "currency": tier_info["currency"],
        "breakdown": breakdown,
        "estimated_month_end": total_units * 30 / now.day * tier_info["cost_per_unit"]
    }
