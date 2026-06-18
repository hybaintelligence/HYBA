"""SQLAlchemy ORM definitions for the consciousness measurement database.

These models provide an object‑relational mapping for a subset of the
consciousness database schema defined in ``schema.sql``.  They are
minimal but sufficient to enable SQLAlchemy to create tables and run
migrations against either SQLite or PostgreSQL.  Additional fields and
relationships from the full schema can be added as needed; this file
intentionally focuses on the most frequently used tables to avoid
introducing complexity prematurely.

Note: Triggers, views and other advanced database constructs defined
in ``schema.sql`` are not automatically created by SQLAlchemy.  If
your deployment relies on those features, you should migrate them via
Alembic revision scripts or external SQL files.
"""

from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    JSON,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    # Executive roles (HYBA Group Leadership)
    CEO_HEIR_APPARENT = "ceo_heir_apparent"
    CHAIRMAN = "chairman"
    CTO = "cto"
    CFO = "cfo"
    LEGAL = "legal"
    CHIEF_OF_STAFF = "chief_of_staff"
    
    # Operational roles
    ADMIN = "admin"
    OPERATOR = "operator"
    ANALYST = "analyst"
    MINER = "miner"


class User(Base):
    """User account for HYBA platform with role-based access control."""
    
    __tablename__ = "users"
    
    id: int | None = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.OPERATOR)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(100), nullable=True)  # Username of admin who created this user


class AuditLog(Base):
    """Audit trail for all administrative actions."""
    
    __tablename__ = "audit_logs"
    
    id: int | None = Column(BigInteger, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    actor_username = Column(String(100), nullable=False)
    actor_role = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=False)  # e.g., "user", "pool", "config", "funding"
    target_id = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)


class ConsciousnessSnapshot(Base):
    """A single measurement of consciousness metrics for a given experiment.

    Only a subset of fields from the full schema are represented here.
    Additional columns can be added as required.
    """

    __tablename__ = "consciousness_snapshots"

    id: int | None = Column(BigInteger, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    experiment_id = Column(String(100), ForeignKey("experiments.id"), nullable=False)

    # Core IIT metrics
    phi = Column(Float, nullable=False)
    phi_max = Column(Float, nullable=True)
    irreducibility = Column(Float, nullable=False)

    # Additional metrics can be added here as needed.  See schema.sql for
    # the complete list of fields.

class Experiment(Base):
    """Metadata for a consciousness experiment.

    Stores high‑level configuration and summary information for each
    experiment.  Experiments can have many associated snapshots.
    """

    __tablename__ = "experiments"

    id: str = Column(String(100), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    config = Column(JSON, nullable=False)
    seed = Column(BigInteger, nullable=False)
    status = Column(String(20), nullable=True)
    results_summary = Column(JSON, nullable=True)
    reproducibility_verified = Column(Boolean, default=False)
    replications = Column(Integer, default=0)
    description = Column(String, nullable=True)
    tags = Column(JSON, nullable=True)
    researcher = Column(String(100), nullable=True)

    # Define relationship to snapshots; SQLAlchemy uses this to infer join conditions.
    snapshots = relationship(
        "ConsciousnessSnapshot",
        backref="experiment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class FundingAllocation(Base):
    """Funding allocation for HYBA Group entities (Research, Analytics, Foundation, etc.)."""
    
    __tablename__ = "funding_allocations"
    
    id: int | None = Column(BigInteger, primary_key=True, index=True)
    entity_name = Column(String(100), nullable=False, index=True)  # e.g., "HYBA Research", "HYBA Analytics", "HYBA Foundation"
    entity_type = Column(String(50), nullable=False)  # e.g., "research", "analytics", "foundation", "vertical"
    allocation_amount = Column(Float, nullable=False)  # In USD
    currency = Column(String(10), default="USD", nullable=False)
    fiscal_year = Column(Integer, nullable=False, index=True)
    fiscal_quarter = Column(Integer, nullable=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, approved, disbursed, rejected
    allocated_by = Column(String(100), nullable=False)  # Username of executive who approved
    allocated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    disbursed_at = Column(DateTime(timezone=True), nullable=True)
    purpose = Column(String(500), nullable=True)
    restrictions = Column(JSON, nullable=True)
    allocation_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class FundingRequest(Base):
    """Funding requests from HYBA Group entities."""
    
    __tablename__ = "funding_requests"
    
    id: int | None = Column(BigInteger, primary_key=True, index=True)
    request_id = Column(String(100), unique=True, nullable=False, index=True)
    entity_name = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    requested_amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    fiscal_quarter = Column(Integer, nullable=True)
    purpose = Column(String(1000), nullable=False)
    justification = Column(String(2000), nullable=True)
    status = Column(String(50), default="pending_review", nullable=False)  # pending_review, under_review, approved, rejected, disbursed
    requested_by = Column(String(100), nullable=False)
    requested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(String(1000), nullable=True)
    request_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
