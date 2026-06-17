"""Admin API endpoints for user management and system administration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from argon2 import PasswordHasher
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session

from hyba_genesis_api.database import SessionLocal
from hyba_genesis_api.auth.jwt_handler import TokenPayload, get_token_payload
from consciousness_db.models import User, AuditLog, UserRole

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
    if "admin" not in payload.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return payload


def log_audit(
    db: Session,
    actor_username: str,
    action: str,
    target_type: str,
    target_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
):
    """Log an administrative action to the audit trail."""
    audit_entry = AuditLog(
        actor_username=actor_username,
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
    role: UserRole = Field(default=UserRole.OPERATOR)


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
    
    username = user.username
    db.delete(user)
    db.commit()
    
    # Log audit
    log_audit(
        db=db,
        actor_username=payload.username,
        action="user_deleted",
        target_type="user",
        target_id=str(user_id),
        details={"deleted_username": username},
    )


@router.get("/audit-logs")
async def list_audit_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    payload: TokenPayload = Depends(require_admin),
):
    """List audit logs with pagination."""
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    total = db.query(AuditLog).count()
    
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
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "admin_users": admin_users,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
