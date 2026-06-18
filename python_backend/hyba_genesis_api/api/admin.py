"""Admin API endpoints for user management, funding, and system administration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from argon2 import PasswordHasher
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session

from hyba_genesis_api.database import SessionLocal
from hyba_genesis_api.auth.jwt_handler import TokenPayload, get_token_payload
from hyba_genesis_api.auth.role_manager import RolePermissions, Permission
from consciousness_db.models import User, AuditLog, UserRole, FundingAllocation, FundingRequest

router = APIRouter(prefix="/api/admin", tags=["admin"])
_password_hasher = PasswordHasher()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_admin(payload: TokenPayload = Depends(get_token_payload)) -> TokenPayload:
    """Require admin role for access."""
    if "admin" not in payload.roles and not RolePermissions.is_executive_role(payload.roles[0] if payload.roles else ""):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return payload


def require_executive(payload: TokenPayload = Depends(get_token_payload)) -> TokenPayload:
    """Require executive role for funding operations."""
    user_role = payload.roles[0] if payload.roles else ""
    if not RolePermissions.is_executive_role(user_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Executive access required for funding operations"
        )
    return payload


def check_permission(payload: TokenPayload, required_permission: Permission) -> bool:
    """Check if user has required permission."""
    user_role = payload.roles[0] if payload.roles else ""
    permissions = RolePermissions.get_permissions_for_role(user_role)
    return required_permission in permissions


def log_audit(
    db: Session,
    actor_username: str,
    actor_role: str,
    action: str,
    target_type: str,
    target_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
):
    """Log an administrative action to the audit trail."""
    audit_entry = AuditLog(
        actor_username=actor_username,
        actor_role=actor_role,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(audit_entry)
    db.commit()


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    password: str = Field(min_length=8, max_length=128)
    role: UserRole


class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    created_by: Optional[str]

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int


@router.get("/users", response_model=UserListResponse)
async def list_users(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    payload: TokenPayload = Depends(require_admin),
):
    """List all users with optional search and pagination."""
    query = db.query(User)
    
    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )
    
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    return UserListResponse(users=users, total=total)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    payload: TokenPayload = Depends(require_admin),
):
    """Get a specific user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateRequest,
    db: Session = Depends(get_db),
    payload: TokenPayload = Depends(require_admin),
):
    """Create a new user."""
    # Check if username already exists
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )
    
    # Check if email already exists
    if user_data.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists"
            )
    
    # Check if user has permission to create executive roles
    user_role = payload.roles[0] if payload.roles else ""
    if RolePermissions.is_executive_role(user_data.role.value) and not RolePermissions.is_executive_role(user_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only executives can create executive roles"
        )
    
    # Hash password
    password_hash = _password_hasher.hash(user_data.password)
    
    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hash,
        role=user_data.role,
        is_active=True,
        created_by=payload.username,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Log audit
    log_audit(
        db=db,
        actor_username=payload.username,
        actor_role=user_role,
        action="user_created",
        target_type="user",
        target_id=str(user.id),
        details={
            "username": user.username,
            "email": user.email,
            "role": user.role,
        },
    )
    
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    db: Session = Depends(get_db),
    payload: TokenPayload = Depends(require_admin),
):
    """Update an existing user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-deactivation
    if user.username == payload.username and user_data.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    # Prevent self-role-change
    if user.username == payload.username and user_data.role is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    
    # Check if user has permission to assign executive roles
    user_role = payload.roles[0] if payload.roles else ""
    if user_data.role and RolePermissions.is_executive_role(user_data.role.value) and not RolePermissions.is_executive_role(user_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only executives can assign executive roles"
        )
    
    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)
    
    if "password" in update_data:
        update_data["password_hash"] = _password_hasher.hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    
    # Log audit
    log_audit(
        db=db,
        actor_username=payload.username,
        actor_role=user_role,
        action="user_updated",
        target_type="user",
        target_id=str(user.id),
        details={
            "updated_fields": list(update_data.keys()),
        },
    )
    
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    payload: TokenPayload = Depends(require_admin),
):
    """Delete a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-deletion
    if user.username == payload.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Prevent deletion of executive roles by non-executives
    user_role = payload.roles[0] if payload.roles else ""
    if RolePermissions.is_executive_role(user.role.value) and not RolePermissions.is_executive_role(user_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only executives can delete executive accounts"
        )
    
    username = user.username
    db.delete(user)
    db.commit()
    
    # Log audit
    log_audit(
        db=db,
        actor_username=payload.username,
        actor_role=user_role,
        action="user_deleted",
        target_type="user",
        target_id=str(user_id),
        details={"deleted_username": username},
    )


@router.get("/audit-logs")
async def list_audit_logs(
    skip: int = 0,
    limit: int = 100,
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    actor_username: Optional[str] = None,
    db: Session = Depends(get_db),
    payload: TokenPayload = Depends(require_admin),
):
    """List audit logs with pagination and filtering."""
    user_role = payload.roles[0] if payload.roles else ""
    
    query = db.query(AuditLog)
    
    if action:
        query = query.filter(AuditLog.action == action)
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)
    if actor_username:
        query = query.filter(AuditLog.actor_username == actor_username)
    
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "logs": logs,
        "total": total,
    }


@router.get("/stats")
async def get_admin_stats(
    db: Session = Depends(get_db),
    payload: TokenPayload = Depends(require_admin),
):
    """Get administrative statistics."""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    admin_users = db.query(User).filter(User.role == UserRole.ADMIN).count()
    
    # Executive stats
    executive_roles = [
        UserRole.CEO_HEIR_APPARENT,
        UserRole.CHAIRMAN,
        UserRole.CTO,
        UserRole.CFO,
        UserRole.LEGAL,
        UserRole.CHIEF_OF_STAFF,
    ]
    executive_users = db.query(User).filter(User.role.in_(executive_roles)).count()
    
    # Funding stats
    total_allocations = db.query(FundingAllocation).count()
    pending_allocations = db.query(FundingAllocation).filter(FundingAllocation.status == "pending").count()
    approved_allocations = db.query(FundingAllocation).filter(FundingAllocation.status == "approved").count()
    total_funding_allocated = db.query(FundingAllocation).filter(
        FundingAllocation.status.in_(["approved", "disbursed"])
    ).with_entities(FundingAllocation.allocation_amount).all()
    total_amount = sum([alloc[0] for alloc in total_funding_allocated]) if total_funding_allocated else 0
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "admin_users": admin_users,
        "executive_users": executive_users,
        "total_allocations": total_allocations,
        "pending_allocations": pending_allocations,
        "approved_allocations": approved_allocations,
        "total_funding_allocated": total_amount,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Funding Management Endpoints ─────────────────────────────────────────────

class FundingAllocationRequest(BaseModel):
    entity_name: str = Field(min_length=1, max_length=100)
    entity_type: str = Field(min_length=1, max_length=50)
    allocation_amount: float = Field(gt=0)
    currency: str = Field(default="USD", max_length=10)
    fiscal_year: int = Field(gt=2000, lt=2100)
    fiscal_quarter: Optional[int] = Field(None, ge=1, le=4)
    purpose: Optional[str] = Field(None, max_length=500)
    restrictions: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class FundingAllocationResponse(BaseModel):
    id: int
    entity_name: str
    entity_type: str
    allocation_amount: float
    currency: str
    fiscal_year: int
    fiscal_quarter: Optional[int]
    status: str
    allocated_by: str
    allocated_at: datetime
    disbursed_at: Optional[datetime]
    purpose: Optional[str]
    restrictions: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FundingAllocationListResponse(BaseModel):
    allocations: List[FundingAllocationResponse]
    total: int


class FundingRequestCreate(BaseModel):
    entity_name: str = Field(min_length=1, max_length=100)
    entity_type: str = Field(min_length=1, max_length=50)
    requested_amount: float = Field(gt=0)
    currency: str = Field(default="USD", max_length=10)
    fiscal_year: int = Field(gt=2000, lt=2100)
    fiscal_quarter: Optional[int] = Field(None, ge=1, le=4)
    purpose: str = Field(min_length=1, max_length=1000)
    justification: Optional[str] = Field(None, max_length=2000)
    metadata: Optional[Dict[str, Any]] = None


class FundingRequestResponse(BaseModel):
    id: int
    request_id: str
    entity_name: str
    entity_type: str
    requested_amount: float
    currency: str
    fiscal_year: int
    fiscal_quarter: Optional[int]
    purpose: str
    justification: Optional[str]
    status: str
    requested_by: str
    requested_at: datetime
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    approval_notes: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FundingRequestListResponse(BaseModel):
    requests: List[FundingRequestResponse]
    total: int


class FundingApprovalRequest(BaseModel):
    status: str = Field(description="approved or rejected")
    approval_notes: Optional[str] = Field(None, max_length=1000)
    allocated_amount: Optional[float] = Field(None, gt=0)


@router.get("/funding/allocations", response_model=FundingAllocationListResponse)
async def list_funding_allocations(
    skip: int = 0,
    limit: int = 50,
    entity_name: Optional[str] = None,
    entity_type: Optional[str] = None,
    status: Optional[str] = None,
    fiscal_year: Optional[int] = None,
    db: Session = Depends(get_db),
    payload: TokenPayload = Depends(require_executive),
):
    """List funding allocations with filtering."""
    query = db.query(FundingAllocation)
    
    if entity_name:
        query = query.filter(FundingAllocation.entity_name.ilike(f"%{entity_name}%"))
    if entity_type:
        query = query.filter(FundingAllocation.entity_type == entity_type)
    if status:
        query = query.filter(FundingAllocation.status == status)
    if fiscal_year:
        query = query.filter(FundingAllocation.fiscal_year == fiscal_year)
    
    total = query.count()
    allocations = query.order_by(FundingAllocation.created_at.desc()).offset(skip).limit(limit).all()
    
    return FundingAllocationListResponse(allocations=allocations, total=total)


@router.post("/funding/allocations", response_model=FundingAllocationResponse, status_code=status.HTTP_201_CREATED)
async def create_funding_allocation(
    allocation_data: FundingAllocationRequest,
    db: Session = Depends(get_db),
    payload: TokenPayload = Depends(require_executive),
):
    """Create a new funding allocation."""
    user_role = payload.roles[0] if payload.roles else ""
    
    allocation = FundingAllocation(
        entity_name=allocation_data.entity_name,
        entity_type=allocation_data.entity_type,
        allocation_amount=allocation_data.allocation_amount,
        currency=allocation_data.currency,
        fiscal_year=allocation_data.fiscal_year,
        fiscal_quarter=allocation_data.fiscal_quarter,
        status="approved",
        allocated_by=payload.username,
        purpose=allocation_data.purpose,
        restrictions=allocation_data.restrictions,
        metadata=allocation_data.metadata,
    )
    db.add(allocation)
    db.commit()
    db.refresh(allocation)
    
    # Log audit
    log_audit(
        db=db,
        actor_username=payload.username,
        actor_role=user_role,
        action="funding_allocated",
        target_type="funding_allocation",
        target_id=str(allocation.id),
        details={
            "entity_name": allocation.entity_name,
            "entity_type": allocation.entity_type,
            "amount": allocation.allocation_amount,
            "currency": allocation.currency,
            "fiscal_year": allocation.fiscal_year,
        },
    )
    
    return allocation


@router.put("/funding/allocations/{allocation_id}", response_model=FundingAllocationResponse)
async def update_funding_allocation(
    allocation_id: int,
    allocation_data: FundingAllocationRequest,
    db: Session = Depends(get_db),
    payload: TokenPayload = Depends(require_executive),
):
    """Update a funding allocation."""
    allocation = db.query(FundingAllocation).filter(FundingAllocation.id == allocation_id).first()
    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Funding allocation not found"
        )
    
    user_role = payload.roles[0] if payload.roles else ""
    
    # Update fields
    update_data = allocation_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(allocation, field, value)
    
    allocation.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(allocation)
    
    # Log audit
    log_audit(
        db=db,
        actor_username=payload.username,
        actor_role=user_role,
        action="funding_allocation_updated",
        target_type="funding_allocation",
        target_id=str(allocation_id),
        details={
            "updated_fields": list(update_data.keys()),
        },
    )
    
    return allocation


@router.post("/funding/allocations/{allocation_id}/disburse", response_model=FundingAllocationResponse)
async def disburse_funding(
    allocation_id: int,
    db: Session = Depends(get_db),
    payload: TokenPayload = Depends(require_executive),
):
    """Mark funding allocation as disbursed."""
    allocation = db.query(FundingAllocation).filter(FundingAllocation.id == allocation_id).first()
    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Funding allocation not found"
        )
    
    if allocation.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only approved allocations can be disbursed"
        )
    
    user_role = payload.roles[0] if payload.roles else ""
    
    allocation.status = "disbursed"
    allocation.disbursed_at = datetime.now(timezone.utc)
    allocation.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(allocation)
    
    # Log audit
    log_audit(
        db=db,
        actor_username=payload.username,
        actor_role=user_role,
        action="funding_disbursed",
        target_type="funding_allocation",
        target_id=str(allocation_id),
        details={
            "entity_name": allocation.entity_name,
            "amount": allocation.allocation_amount,
        },
    )
    
    return allocation


@router.get("/funding/requests", response_model=FundingRequestListResponse)
async def list_funding_requests(
    skip: int = 0,
    limit: int = 50,
    entity_name: Optional[str] = None,
    entity_type: Optional[str] = None,
    status: Optional[str] = None,
    fiscal_year: Optional[int] = None,
    db: Session = Depends(get_db),
    payload: TokenPayload = Depends(require_executive),
):
    """List funding requests with filtering."""
    query = db.query(FundingRequest)
    
    if entity_name:
        query = query.filter(FundingRequest.entity_name.ilike(f"%{entity_name}%"))
    if entity_type:
        query = query.filter(FundingRequest.entity_type == entity_type)
    if status:
        query = query.filter(FundingRequest.status == status)
    if fiscal_year:
        query = query.filter(FundingRequest.fiscal_year == fiscal_year)
    
    total = query.count()
    requests = query.order_by(FundingRequest.created_at.desc()).offset(skip).limit(limit).all()
    
    return FundingRequestListResponse(requests=requests, total=total)


@router.post("/funding/requests", response_model=FundingRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_funding_request(
    request_data: FundingRequestCreate,
    db: Session = Depends(get_db),
    payload: TokenPayload = Depends(require_executive),
):
    """Create a new funding request."""
    user_role = payload.roles[0] if payload.roles else ""
    request_id = f"REQ-{uuid.uuid4().hex[:12].upper()}"
    
    funding_request = FundingRequest(
        request_id=request_id,
        entity_name=request_data.entity_name,
        entity_type=request_data.entity_type,
        requested_amount=request_data.requested_amount,
        currency=request_data.currency,
        fiscal_year=request_data.fiscal_year,
        fiscal_quarter=request_data.fiscal_quarter,
        purpose=request_data.purpose,
        justification=request_data.justification,
        status="pending_review",
        requested_by=payload.username,
        metadata=request_data.metadata,
    )
    db.add(funding_request)
    db.commit()
    db.refresh(funding_request)
    
    # Log audit
    log_audit(
        db=db,
        actor_username=payload.username,
        actor_role=user_role,
        action="funding_request_created",
        target_type="funding_request",
        target_id=funding_request.request_id,
        details={
            "entity_name": funding_request.entity_name,
            "requested_amount": funding_request.requested_amount,
            "fiscal_year": funding_request.fiscal_year,
        },
    )
    
    return funding_request


@router.put("/funding/requests/{request_id}/review", response_model=FundingRequestResponse)
async def review_funding_request(
    request_id: str,
    review_data: FundingApprovalRequest,
    db: Session = Depends(get_db),
    payload: TokenPayload = Depends(require_executive),
):
    """Review and approve/reject a funding request."""
    funding_request = db.query(FundingRequest).filter(FundingRequest.request_id == request_id).first()
    if not funding_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Funding request not found"
        )
    
    if funding_request.status not in ["pending_review", "under_review"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request cannot be reviewed in its current state"
        )
    
    user_role = payload.roles[0] if payload.roles else ""
    
    funding_request.status = review_data.status
    funding_request.reviewed_by = payload.username
    funding_request.reviewed_at = datetime.now(timezone.utc)
    funding_request.approval_notes = review_data.approval_notes
    funding_request.updated_at = datetime.now(timezone.utc)
    
    # If approved, create allocation
    if review_data.status == "approved":
        allocated_amount = review_data.allocated_amount or funding_request.requested_amount
        allocation = FundingAllocation(
            entity_name=funding_request.entity_name,
            entity_type=funding_request.entity_type,
            allocation_amount=allocated_amount,
            currency=funding_request.currency,
            fiscal_year=funding_request.fiscal_year,
            fiscal_quarter=funding_request.fiscal_quarter,
            status="approved",
            allocated_by=payload.username,
            purpose=funding_request.purpose,
            metadata={"source_request_id": funding_request.request_id},
        )
        db.add(allocation)
        funding_request.status = "approved"
    
    db.commit()
    db.refresh(funding_request)
    
    # Log audit
    log_audit(
        db=db,
        actor_username=payload.username,
        actor_role=user_role,
        action="funding_request_reviewed",
        target_type="funding_request",
        target_id=request_id,
        details={
            "status": review_data.status,
            "approval_notes": review_data.approval_notes,
        },
    )
    
    return funding_request


@router.get("/funding/summary")
async def get_funding_summary(
    fiscal_year: Optional[int] = None,
    db: Session = Depends(get_db),
    payload: TokenPayload = Depends(require_executive),
):
    """Get funding summary by entity and fiscal year."""
    query = db.query(FundingAllocation)
    
    if fiscal_year:
        query = query.filter(FundingAllocation.fiscal_year == fiscal_year)
    
    allocations = query.all()
    
    # Group by entity
    entity_summary = {}
    total_by_status = {"pending": 0, "approved": 0, "disbursed": 0, "rejected": 0}
    
    for alloc in allocations:
        entity_key = f"{alloc.entity_name} ({alloc.entity_type})"
        if entity_key not in entity_summary:
            entity_summary[entity_key] = {
                "entity_name": alloc.entity_name,
                "entity_type": alloc.entity_type,
                "total_allocated": 0,
                "total_disbursed": 0,
                "allocation_count": 0,
            }
        
        entity_summary[entity_key]["total_allocated"] += alloc.allocation_amount
        entity_summary[entity_key]["allocation_count"] += 1
        
        if alloc.status == "disbursed":
            entity_summary[entity_key]["total_disbursed"] += alloc.allocation_amount
        
        if alloc.status in total_by_status:
            total_by_status[alloc.status] += alloc.allocation_amount
    
    return {
        "entity_summary": list(entity_summary.values()),
        "total_by_status": total_by_status,
        "fiscal_year": fiscal_year,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
