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
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

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
