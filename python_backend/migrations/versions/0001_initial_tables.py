"""Initial tables for HYBA consciousness database.

Revision ID: 0001_initial
Revises: None
Create Date: 2026-06-17

This migration creates the core tables used by the HYBA consciousness
measurement platform.  It mirrors the SQLAlchemy models defined in
`consciousness_db/models.py` and serves as the base revision for
Alembic migrations.  Additional fields and tables from the full
`schema.sql` can be added in subsequent revisions.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the initial experiments and consciousness_snapshots tables."""
    # Create experiments table
    op.create_table(
        'experiments',
        sa.Column('id', sa.String(length=100), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('seed', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('results_summary', sa.JSON(), nullable=True),
        sa.Column('reproducibility_verified', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.Column('replications', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('researcher', sa.String(length=100), nullable=True),
    )

    # Create consciousness_snapshots table
    op.create_table(
        'consciousness_snapshots',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('experiment_id', sa.String(length=100), sa.ForeignKey('experiments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('phi', sa.Float(), nullable=False),
        sa.Column('phi_max', sa.Float(), nullable=True),
        sa.Column('irreducibility', sa.Float(), nullable=False),
    )


def downgrade() -> None:
    """Drop the initial tables."""
    op.drop_table('consciousness_snapshots')
    op.drop_table('experiments')
