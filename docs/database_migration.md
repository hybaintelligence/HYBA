# Database Migration Plan

The current implementation of `consciousness_db` uses SQLite for storing runtime metrics and state.  SQLite is convenient for development but not suitable for high‑availability production.  This plan outlines the steps to migrate to PostgreSQL.

## Rationale

- **Concurrency and scalability** – SQLite supports only one writer at a time and has limited concurrency.  PostgreSQL offers robust concurrency control and can scale vertically and horizontally.
- **Durability and replication** – PostgreSQL supports replication, backups, and point‑in‑time recovery, which are necessary for production resilience.
- **Migration tooling** – Libraries such as Alembic and SQLAlchemy support automatic migrations and schema versioning with PostgreSQL.

## Migration steps

1. **Define a SQLAlchemy model** for the existing tables in `consciousness_db/schema.sql`.  Move the schema into a SQLAlchemy ORM definition that can target both SQLite and PostgreSQL.
2. **Introduce Alembic** as a dependency and configure migration scripts.  Initialise an `alembic` directory and generate an initial migration based on the existing model.
3. **Create a PostgreSQL instance** in your chosen environment (e.g., Cloud SQL, RDS, self‑hosted).  Obtain connection credentials and store them securely in the secret manager.
4. **Update configuration** – Add environment variables for `DATABASE_URL` pointing to the PostgreSQL database.  Modify database access code to read from `DATABASE_URL` via SQLAlchemy.
5. **Run migrations** – Use Alembic to apply the initial schema to PostgreSQL:
   ```bash
   alembic upgrade head
   ```
6. **Migrate data** – Export existing SQLite data and import it into PostgreSQL.  Use tools like `pgloader` or custom scripts to perform the migration.
7. **Update application code** – Ensure that all database operations go through SQLAlchemy; remove direct SQLite calls.  Update tests to run against an in‑memory or containerised PostgreSQL instance for CI.
8. **Monitor and optimise** – Monitor query performance and resource usage on the new database.  Add indexes and tune parameters as needed.

## Backups and recovery

- Set up automated backups with your database provider.  Test recovery procedures regularly.
- Use separate environments (development, staging, production) with isolated databases and credentials.

Adopting PostgreSQL improves reliability, scalability, and maintainability of the persistence layer.  Plan the migration carefully and test thoroughly before switching in production.
