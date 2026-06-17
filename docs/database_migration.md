# Database Migration Plan

The current implementation of `consciousness_db` uses SQLite for storing runtime metrics and state.  SQLite is convenient for development but not suitable for high‑availability production.  This plan outlines the steps to migrate to PostgreSQL and describes how to run and manage database schema migrations using Alembic.

## Rationale

- **Concurrency and scalability** – SQLite supports only one writer at a time and has limited concurrency.  PostgreSQL offers robust concurrency control and can scale vertically and horizontally.
- **Durability and replication** – PostgreSQL supports replication, backups, and point‑in‑time recovery, which are necessary for production resilience.
- **Migration tooling** – Libraries such as SQLAlchemy and Alembic support automatic migrations and schema versioning with PostgreSQL.

## Migration steps

1. **Define a SQLAlchemy model** for the existing tables in `consciousness_db/schema.sql`.  We have added a minimal ORM definition in `python_backend/consciousness_db/models.py` to map the core tables.
2. **Introduce Alembic** – The repository now includes an `alembic.ini` configuration file at the project root, a migration environment script at `python_backend/migrations/env.py`, and an initial migration in `python_backend/migrations/versions/0001_initial_tables.py`.  These files make it easy to manage schema versions.  Install Alembic (`pip install alembic`) and run `alembic init` is **not** necessary because the structure is already provided.
3. **Create a PostgreSQL instance** in your chosen environment (e.g., Cloud SQL, RDS, self‑hosted).  Obtain connection credentials and store them securely in your secret manager.
4. **Update configuration** – Set the `DATABASE_URL` environment variable (and optional `POSTGRES_*` variables when using Docker Compose) to point to the PostgreSQL database.  The FastAPI backend and Alembic scripts read `DATABASE_URL` to determine which database to use.
5. **Run migrations** – Apply the initial schema to PostgreSQL using Alembic:

   ```bash
   # Ensure the virtual environment has alembic installed
   alembic upgrade head
   ```

   This command will run the migrations in `python_backend/migrations/versions/` against the database specified by `DATABASE_URL`.  You can also run `alembic history` to view available revisions.
6. **Migrate data** – Export existing SQLite data and import it into PostgreSQL.  Use tools like `pgloader` or write custom scripts to map the data.  Ensure that primary/foreign key relationships are preserved.
7. **Update application code** – Ensure that all database operations go through SQLAlchemy; remove direct SQLite calls.  Update tests to run against an in‑memory or containerised PostgreSQL instance for CI.  The provided CI workflow runs tests against a Postgres service.
8. **Monitor and optimise** – Monitor query performance and resource usage on the new database.  Add indexes and tune parameters as needed.

## Backups and recovery

- Set up automated backups with your database provider.  Test recovery procedures regularly.
- Use separate environments (development, staging, production) with isolated databases and credentials.

Adopting PostgreSQL improves reliability, scalability, and maintainability of the persistence layer.  Plan the migration carefully and test thoroughly before switching in production.  The combination of SQLAlchemy models and Alembic migrations in this repository provides a repeatable and auditable way to evolve the database schema over time.
