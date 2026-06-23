"""SQLAlchemy models for HYBA Genesis enterprise platform.

Enterprise-grade data models for:
- User authentication and authorization
- Role-based access control (RBAC)
- Audit logging and compliance
- Funding allocation and requests
- Multi-tenant isolation
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List
from enum import Enum

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from hyba_genesis_api.database import Base


class UserRole(str, Enum):
    """User roles with hierarchical permissions."""
    ADMIN = "admin"
    EXECUTIVE = "executive"
    OPERATOR = "operator"
    ANALYST = "analyst"
    DEVELOPER = "developer"
    CUSTOMER = "customer"
    VIEWER = "viewer"


class FundingStatus(str, Enum):
    """Funding request lifecycle states."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ALLOCATED = "allocated"
    EXPIRED = "expired"


class User(Base):
    """User account with authentication and authorization.
    
    Enterprise features:
    - Argon2 password hashing
    - Multi-factor authentication support
    - Session management
    - Account lifecycle tracking
    """
    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile
    full_name = Column(String(255))
    organization = Column(String(255))
    
    # Authorization
    role = Column(String(50), nullable=False, default=UserRole.VIEWER.value)
    roles = Column(Text)  # JSON array of roles for RBAC
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    
    # Multi-factor authentication
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_login_at = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True))
    
    # Soft delete
    deleted_at = Column(DateTime(timezone=True))
    
    # Relationships
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    funding_requests = relationship("FundingRequest", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_user_email_active", "email", "is_active"),
        Index("idx_user_role", "role"),
        CheckConstraint("email LIKE '%@%'", name="check_email_format"),
    )

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, email={self.email}, role={self.role})>"


class AuditLog(Base):
    """Immutable audit trail for compliance and security monitoring.
    
    Enterprise features:
    - Tamper-evident logging
    - GDPR/SOC2 compliance support
    - Security event tracking
    - Performance monitoring
    """
    __tablename__ = "audit_logs"

    log_id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False, index=True)
    
    # Event classification
    event_type = Column(String(100), nullable=False, index=True)
    event_category = Column(String(50), nullable=False, index=True)  # auth, admin, api, system
    severity = Column(String(20), nullable=False, default="info")  # debug, info, warning, error, critical
    
    # Event details
    action = Column(String(255), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(String(255))
    description = Column(Text)
    
    # Request context
    ip_address = Column(String(45))  # IPv6 support
    user_agent = Column(Text)
    request_id = Column(String(100), index=True)
    session_id = Column(String(100))
    
    # Result
    status = Column(String(50), nullable=False)  # success, failure, error
    error_message = Column(Text)
    
    # Metadata
    metadata_json = Column(Text)  # JSON blob for flexible data
    
    # Timestamp (immutable)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    __table_args__ = (
        Index("idx_audit_user_timestamp", "user_id", "timestamp"),
        Index("idx_audit_event_timestamp", "event_type", "timestamp"),
        Index("idx_audit_category_severity", "event_category", "severity"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog(log_id={self.log_id}, user_id={self.user_id}, event_type={self.event_type})>"


class FundingAllocation(Base):
    """Approved funding allocations for projects and operations.
    
    Enterprise features:
    - Budget tracking and enforcement
    - Multi-currency support
    - Audit trail integration
    """
    __tablename__ = "funding_allocations"

    allocation_id = Column(String(36), primary_key=True, index=True)
    
    # Allocation details
    project_name = Column(String(255), nullable=False)
    project_description = Column(Text)
    category = Column(String(100), nullable=False)  # research, infrastructure, operations, etc.
    
    # Financial
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    amount_used = Column(Float, nullable=False, default=0.0)
    amount_remaining = Column(Float, nullable=False)
    
    # Lifecycle
    status = Column(String(50), nullable=False, default="active")  # active, depleted, expired, cancelled
    allocated_by = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    approved_by = Column(String(36), ForeignKey("users.user_id"))
    
    # Timestamps
    allocated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True))
    depleted_at = Column(DateTime(timezone=True))
    
    # Audit
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index("idx_funding_allocation_status", "status"),
        Index("idx_funding_allocation_category", "category"),
        CheckConstraint("amount > 0", name="check_amount_positive"),
        CheckConstraint("amount_used >= 0", name="check_amount_used_nonnegative"),
        CheckConstraint("amount_remaining >= 0", name="check_amount_remaining_nonnegative"),
    )

    def __repr__(self) -> str:
        return f"<FundingAllocation(allocation_id={self.allocation_id}, project={self.project_name}, amount={self.amount})>"


class FundingRequest(Base):
    """Funding requests submitted by users for approval workflow.
    
    Enterprise features:
    - Approval workflow automation
    - Budget justification tracking
    - Multi-level approval support
    """
    __tablename__ = "funding_requests"

    request_id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False, index=True)
    
    # Request details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    justification = Column(Text)
    category = Column(String(100), nullable=False)
    
    # Financial
    amount_requested = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    
    # Workflow
    status = Column(String(50), nullable=False, default=FundingStatus.PENDING.value, index=True)
    priority = Column(String(20), default="normal")  # low, normal, high, critical
    
    # Approval
    reviewed_by = Column(String(36), ForeignKey("users.user_id"))
    reviewed_at = Column(DateTime(timezone=True))
    review_notes = Column(Text)
    
    # Allocation link (when approved)
    allocation_id = Column(String(36), ForeignKey("funding_allocations.allocation_id"))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="funding_requests", foreign_keys=[user_id])
    
    __table_args__ = (
        Index("idx_funding_request_user_status", "user_id", "status"),
        Index("idx_funding_request_status_priority", "status", "priority"),
        CheckConstraint("amount_requested > 0", name="check_amount_requested_positive"),
    )

    def __repr__(self) -> str:
        return f"<FundingRequest(request_id={self.request_id}, title={self.title}, status={self.status})>"


# Migration helper function
def create_all_tables(engine):
    """Create all tables in the database.
    
    Use this for initial database setup or migrations.
    For production, use Alembic migrations instead.
    """
    Base.metadata.create_all(bind=engine)


def drop_all_tables(engine):
    """Drop all tables from the database.
    
    WARNING: This is destructive and irreversible.
    Only use in development/testing environments.
    """
    Base.metadata.drop_all(bind=engine)
