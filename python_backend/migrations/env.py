"""Alembic environment for HYBA_FULLSTACK database migrations.

This script configures Alembic to run migrations against the database
specified by the `DATABASE_URL` environment variable.  It imports the
SQLAlchemy metadata from the HYBA consciousness models so that
alembic's autogenerate feature can produce accurate migration scripts.

Running `alembic upgrade head` will apply pending migrations to the
configured database.  See `docs/database_migration.md` and
`docs/deployment/POSTGRES_DEPLOYMENT_GUIDE.md` for details on
configuring the database URL and running migrations in development and
production environments.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Import the metadata from the SQLAlchemy models.  We import from the
# consciousness_db package rather than hyba_genesis_api.database to
# avoid circular dependencies and to ensure migrations are based on
# explicit table definitions.
from consciousness_db.models import Base  # type: ignore

# this is the Alembic Config object, which provides access to the values
# within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.  This line sets up
# loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Provide your model's MetaData object here for 'autogenerate' support
# target_metadata = mymodel.Base.metadata
# for more details: https://alembic.sqlalchemy.org/en/latest/autogenerate.html

target_metadata = Base.metadata


def get_url() -> str:
    """Return the database URL from environment or fall back to SQLite.

    If the DATABASE_URL environment variable is not set, default to a
    local SQLite database.  This fallback is intended for development
    only; production deployments should always set DATABASE_URL.
    """
    return os.getenv("DATABASE_URL", "sqlite:///consciousness.db")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine.
    Calls to context.execute() here emit the given string to the
    script output.

    When offline, we enable literal binds and set compare_type=True so
    that Alembic generates type changes when the schema differs.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a
    connection with the context.  The connection is created using
    the database URL provided by `get_url()`.  We also enable
    compare_type so that changes in column types are detected.
    """

    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
